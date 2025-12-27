import logging
import subprocess
import shlex
import xml.etree.ElementTree as ET
from datetime import datetime

from celery import shared_task
from django.utils import timezone
from django.db import transaction

# 操！把模型都叫過來
from core.models import NmapScan
from core.models import Port

logger = logging.getLogger(__name__)


# 操！這就是我們的 nmap 突擊隊
@shared_task(bind=True, name="nmap_scanner.tasks.perform_nmap_scan")
def perform_nmap_scan(self, scan_id: int, ip_address: str, nmap_args: str):
    """
    執行 Nmap 掃描，解析結果，並將情報存入資料庫。
    這是一個獨立的、可以失敗和重試的作戰單元。
    """
    logger.info(
        f"任務 [{self.request.id}] 領取命令：開始處理 NmapScan ID: {scan_id} for IP: {ip_address}"
    )

    scan_record = None
    try:
        # 操！第一件事，從資料庫把任務命令書拿出來。
        scan_record = NmapScan.objects.get(id=scan_id)

        # 如果任務不是 PENDING，說明有問題，直接滾蛋
        if scan_record.status != "PENDING":
            logger.warning(
                f"Scan ID {scan_id} 狀態為 {scan_record.status}，非 PENDING。任務終止。"
            )
            return f"Scan ID {scan_id} not in PENDING state."

        # 立即更新狀態為 RUNNING，讓前台知道我們在幹活了。
        scan_record.status = "RUNNING"
        scan_record.started_at = timezone.now()  # 操！用帶時區的時間
        scan_record.save()

        # 準備執行命令。用 shlex.split 保證參數安全，防止命令注入。
        # 操！目標 IP 必須是最後一個參數。
        command = f"nmap {nmap_args} {ip_address}"
        logger.info(f"準備執行命令: {command}")

        # 執行命令，設置超時（比如30分鐘），捕獲標準輸出和錯誤
        # 注意：nmap -oX - 會把XML輸出到stdout
        process = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minutes timeout
        )

        # 檢查 nmap 是否成功執行
        if process.returncode != 0:
            error_msg = (
                f"Nmap 執行失敗，返回碼: {process.returncode}. Stderr: {process.stderr}"
            )
            raise RuntimeError(error_msg)

        xml_output = process.stdout
        # 操！必須把原始輸出存下來，方便日後查水錶
        scan_record.nmap_output = xml_output
        scan_record.save(update_fields=["nmap_output"])

        logger.info(f"NmapScan ID {scan_id} 執行完畢，準備解析 XML 結果。")
        # 操！這裡是重頭戲：把 nmap 的 XML 報告變成我們資料庫裡的情報。
        parse_and_save_nmap_results(scan_record, xml_output)

        # 如果能走到這裡，說明一切順利
        scan_record.status = "COMPLETED"
        logger.info(f"NmapScan ID {scan_id} 成功完成。")

    except NmapScan.DoesNotExist:
        logger.error(
            f"操！任務 [{self.request.id}] 找不到 NmapScan 記錄，ID: {scan_id}"
        )
        # 記錄不存在，重試也沒用，直接放棄
        return
    except subprocess.TimeoutExpired:
        logger.error(f"NmapScan ID {scan_id} 執行超時。")
        if scan_record:
            scan_record.status = "FAILED"
            scan_record.error_message = "Nmap command timed out after 30 minutes."
    except Exception as e:
        logger.exception(f"處理 NmapScan ID {scan_id} 時發生未知錯誤: {e}")
        if scan_record:
            scan_record.status = "FAILED"
            # 操！把錯誤信息寫清楚
            scan_record.error_message = f"An unexpected error occurred: {str(e)}"
    finally:
        # 操！無論成敗，都必須有始有終。更新最終狀態和完成時間。
        if scan_record:
            scan_record.completed_at = timezone.now()
            scan_record.save()
            logger.info(f"NmapScan ID {scan_id} 最終狀態: {scan_record.status}")


def parse_and_save_nmap_results(scan_record: NmapScan, xml_output: str):
    """
    解析 nmap XML 輸出並更新 Port 資產庫。
    """
    try:
        root = ET.fromstring(xml_output)

        # 操！用事務包裹，要麼全部成功，要麼全部回滾，保證數據一致性。
        with transaction.atomic():
            ip_object = scan_record.ip  # 直接從 scan record 裡拿 IP 對象

            # 找到 host 標籤
            for host in root.findall("host"):
                # 找到 ports 標籤
                ports_element = host.find("ports")
                if ports_element is None:
                    continue

                # 遍歷所有 port 標籤
                for port_element in ports_element.findall("port"):
                    port_number = int(port_element.get("portid"))
                    protocol = port_element.get("protocol")

                    state_element = port_element.find("state")
                    state = (
                        state_element.get("state")
                        if state_element is not None
                        else "unknown"
                    )

                    service_element = port_element.find("service")
                    service_name = (
                        service_element.get("name")
                        if service_element is not None
                        else None
                    )
                    service_version = (
                        service_element.get("version")
                        if service_element is not None
                        else None
                    )

                    # 操！用 update_or_create，這他媽是原子操作的聖杯。
                    # 如果端口存在，就更新它的狀態；如果不存在，就創建一條新紀錄。
                    port_obj, created = Port.objects.update_or_create(
                        ip=ip_object,
                        port_number=port_number,
                        protocol=protocol,
                        defaults={
                            "state": state,
                            "service_name": service_name,
                            "service_version": service_version,
                            "last_updated_by_scan": scan_record,  # 關鍵！記錄是誰更新了它
                            "last_seen": timezone.now(),  # 手動更新 last_seen
                        },
                    )

                    action = "創建" if created else "更新"
                    logger.debug(
                        f"成功 {action} 端口資產: {ip_object.ipv4}:{port_number}/{protocol} - {state}"
                    )

    except ET.ParseError as e:
        logger.error(f"解析 Nmap XML 失敗 for Scan ID {scan_record.id}: {e}")
        # 操！這種情況必須拋出異常，讓外層的 try-except 抓住，把任務標記為 FAILED
        raise ValueError(f"XML Parse Error: {e}")
    except Exception as e:
        logger.exception(f"在資料庫操作中發生錯誤 for Scan ID {scan_record.id}: {e}")
        raise
