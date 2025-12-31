import hashlib
import subprocess
from celery import shared_task
from core.models import NucleiScan, Vulnerability, IP, URLResult, Subdomain
from typing import Dict, Any, List
import json
from c2_core.config.logging import log_function_call
from logging import getLogger
from django.utils import timezone

logger = getLogger(__name__)


def save_nuclei_result_to_db(
    data: Dict[str, Any], asset_id: int, asset_type: str, scan_record_id: int = None
) -> Vulnerability:
    """
    將單條 Nuclei 結果存入 Vulnerability 表
    """
    template_id = data.get("template-id")
    matched_at = data.get("matched-at")
    fingerprint = hashlib.sha256(f"{template_id}{matched_at}".encode()).hexdigest()

    defaults = {
        "name": data.get("info", {}).get("name", "Unknown"),
        "severity": data.get("info", {}).get("severity", "info"),
        "extracted_results": data.get("extracted-results", []),
        "request_raw": data.get("request", ""),
        "response_raw": data.get("response", ""),
        "status": "unverified",
    }

    if asset_type == "IP":
        defaults["ip_asset_id"] = asset_id
    elif asset_type == "Subdomain":
        defaults["subdomain_asset_id"] = asset_id
    elif asset_type == "URL":
        defaults["url_asset_id"] = asset_id

    # 寫入漏洞表
    vuln_obj, created = Vulnerability.objects.update_or_create(
        fingerprint=fingerprint, defaults=defaults
    )
    return vuln_obj


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_nuclei_scans_for_ip_batch(self, ip_ids: List[int]):
    # 1. 獲取數據
    ip_records = IP.objects.filter(id__in=ip_ids).values("id", "ipv4", "ipv6")
    ip_map = {}
    scan_record_ids = []  # 用於追蹤本批次創建的掃描記錄 ID

    # 2. 創建掃描記錄 (標記為 RUNNING)
    for r in ip_records:
        val = r["ipv4"] or r["ipv6"]
        if val:
            ip_map[val] = r["id"]
            scan = NucleiScan.objects.create(
                ip_asset_id=r["id"],
                severity_filter="info-crit",
                template_ids=["network"],
                status="RUNNING",  # <--- 關鍵：標記正在運行
            )
            scan_record_ids.append(scan.id)

    if not ip_map:
        return

    # 3. 構建命令
    targets = []
    for ip in ip_map.keys():
        targets.extend(["-u", ip])
    command = ["nuclei"] + targets + ["-t", "network", "-j", "-ni", "-nc", "-silent"]

    # 4. 執行與狀態更新
    try:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, text=True, bufsize=1
        )
        for line in iter(process.stdout.readline, ""):
            if line:
                try:
                    result = json.loads(line.strip())
                    target_ip_id = ip_map.get(result.get("ip"))
                    if target_ip_id:
                        save_nuclei_result_to_db(
                            result, asset_id=target_ip_id, asset_type="IP"
                        )
                except json.JSONDecodeError:
                    continue
        process.wait()

        # 掃描完成，更新所有記錄為 COMPLETED
        NucleiScan.objects.filter(id__in=scan_record_ids).update(status="COMPLETED")

    except Exception as e:
        logger.exception(f"IP Nuclei 掃描失敗: {e}")
        # 發生異常，更新記錄為 FAILED
        NucleiScan.objects.filter(id__in=scan_record_ids).update(status="FAILED")


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_nuclei_scans_for_subdomain_batch(self, subdomain_ids: List[int]):
    sub_records = Subdomain.objects.filter(id__in=subdomain_ids).values("id", "name")
    sub_map = {}
    scan_record_ids = []

    for r in sub_records:
        sub_map[r["name"]] = r["id"]
        scan = NucleiScan.objects.create(
            subdomain_asset_id=r["id"],
            severity_filter="all",
            template_ids=["dns", "ssl", "takeover", "as"],
            status="RUNNING",  # <--- 關鍵
        )
        scan_record_ids.append(scan.id)

    if not sub_map:
        return

    targets = []
    for name in sub_map.keys():
        targets.extend(["-u", name])
    command = (
        ["nuclei"]
        + targets
        + ["-as", "-tags", "dns,ssl,takeover", "-j", "-nc", "-silent"]
    )

    try:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, text=True, bufsize=1
        )
        for line in iter(process.stdout.readline, ""):
            if line:
                try:
                    result = json.loads(line.strip())
                    target_id = sub_map.get(result.get("host"))
                    if target_id:
                        save_nuclei_result_to_db(
                            result, asset_id=target_id, asset_type="Subdomain"
                        )
                except json.JSONDecodeError:
                    continue
        process.wait()

        NucleiScan.objects.filter(id__in=scan_record_ids).update(status="COMPLETED")

    except Exception as e:
        logger.exception(f"Subdomain Nuclei 掃描失敗: {e}")
        NucleiScan.objects.filter(id__in=scan_record_ids).update(status="FAILED")


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_nuclei_scans_for_url_batch(self, url_ids: List[int]):
    url_records = URLResult.objects.filter(id__in=url_ids).values("id", "url")
    url_map = {}
    scan_record_ids = []

    for r in url_records:
        url_map[r["url"]] = r["id"]
        scan = NucleiScan.objects.create(
            url_asset_id=r["id"],
            severity_filter="low-crit",
            template_ids=["as", "vulnerabilities"],
            status="RUNNING",  # <--- 關鍵
        )
        scan_record_ids.append(scan.id)

    if not url_map:
        return

    targets = []
    for url in url_map.keys():
        targets.extend(["-u", url])
    command = (
        ["nuclei"]
        + targets
        + ["-as", "-severity", "low,medium,high,critical", "-j", "-nc", "-silent"]
    )

    try:
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, text=True, bufsize=1
        )
        for line in iter(process.stdout.readline, ""):
            if line:
                try:
                    result = json.loads(line.strip())
                    matched_url = result.get("matched-at") or result.get("url")
                    # 處理 URL 末尾斜槓問題
                    target_id = url_map.get(matched_url) or url_map.get(
                        matched_url.rstrip("/")
                    )
                    if target_id:
                        save_nuclei_result_to_db(
                            result, asset_id=target_id, asset_type="URL"
                        )
                except json.JSONDecodeError:
                    continue
        process.wait()

        NucleiScan.objects.filter(id__in=scan_record_ids).update(status="COMPLETED")

    except Exception as e:
        logger.exception(f"URL Nuclei 掃描失敗: {e}")
        NucleiScan.objects.filter(id__in=scan_record_ids).update(status="FAILED")
