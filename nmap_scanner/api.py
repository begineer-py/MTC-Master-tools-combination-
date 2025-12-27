import logging
from ninja import Router, Schema
from ninja.errors import HttpError
from typing import List, Optional
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count

# 操！導入正確的模型
from core.models import IP, Target
from core.models import NmapScan
from .schemas import (
    NmapScanTriggerSchema,
    NmapScanSchema,
    NmapScanOverviewSchema,
    ErrorSchema,
    PortSchema,
)
from .tasks import perform_nmap_scan
from c2_core.config.logging import log_function_call

router = Router()
logger = logging.getLogger(__name__)

# ... (其他 import 保持不變) ...


# --- API 端點：觸發 Nmap 掃描任務 ---
@router.post(
    "/start_scan",
    response={
        200: NmapScanSchema,
        400: ErrorSchema,
        404: ErrorSchema,
        409: ErrorSchema,
        500: ErrorSchema,
    },
)
@log_function_call()
async def start_nmap_scan(request, trigger_data: NmapScanTriggerSchema):
    """
    對指定 IP 觸發一個新的 Nmap 掃描任務。
    """
    # 操！先安檢，再登機。Target 是根，根不存在，一切免談。
    # 用 .filter().afirst() 查詢，如果沒有就返回 None，不會拋異常。
    target = await Target.objects.filter(id=trigger_data.target_id).afirst()
    if not target:
        # 滾蛋。
        logger.warning(f"嘗試為不存在的 Target ID {trigger_data.target_id} 啟動掃描。")
        raise HttpError(
            404, f"根目標 Target ID {trigger_data.target_id} 不存在，無法執行任何操作。"
        )

    # 既然 Target 存在，那就把剩下的邏輯包在一個 try 裡處理其他可能的意外。
    try:
        # 操！第一步，拿到 IP 資產。沒有就創建。
        # target 已經驗證存在，這裡可以放心用。
        ip_obj, created = await IP.objects.aget_or_create(
            ipv4=trigger_data.ip, which_target=target
        )
        if created:
            logger.info(
                f"新的 IP 資產已創建: {trigger_data.ip} for Target {target.domain}"
            )

        # 檢查是否有正在進行的掃描
        existing_active_scan = await NmapScan.objects.filter(
            ip=ip_obj, status__in=["PENDING", "RUNNING"]
        ).afirst()
        if existing_active_scan:
            raise HttpError(
                409,
                f"IP {trigger_data.ip} 已有正在進行中的 Nmap 掃描任務 (ID: {existing_active_scan.id})。",
            )

        # 操！這裡！把前端傳來的參數，真正組合成 nmap 能打的命令！
        args = []
        if trigger_data.scan_service_version:
            args.append("-sV")
        if trigger_data.scan_os:
            args.append("--osscan-guess")  # -O 需要 root，這個更通用

        args.append(f"-T{trigger_data.scan_rate}")

        if isinstance(trigger_data.scan_ports, list) and trigger_data.scan_ports:
            ports_str = ",".join(map(str, trigger_data.scan_ports))
            args.append(f"-p {ports_str}")
        elif trigger_data.scan_ports == "all":
            args.append("-p-")
        elif trigger_data.scan_ports == "top-1000":
            args.append("--top-ports 1000")

        # 總是輸出 XML，方便解析
        args.append("-oX -")
        final_nmap_args = " ".join(args)

        # 創建新的掃描記錄
        scan_record = await NmapScan.objects.acreate(
            ip=ip_obj,
            scan_type="custom_scan",  # 可以根據參數組合生成更詳細的類型
            nmap_args=final_nmap_args,
            status="PENDING",
        )
        logger.info(
            f"為 IP {trigger_data.ip} 創建新的 NmapScan 記錄: ID={scan_record.id}"
        )

        # 丟給 Celery 去執行
        perform_nmap_scan.delay(
            scan_id=scan_record.id,
            ip_address=trigger_data.ip,
            nmap_args=final_nmap_args,
        )
        logger.info(
            f"Nmap 掃描任務 (ID: {scan_record.id}) for IP {trigger_data.ip} 已提交到隊列。"
        )

        return NmapScanSchema(
            id=scan_record.id,
            ip_id=ip_obj.id,
            ip_address=ip_obj.ipv4,
            scan_type=scan_record.scan_type,
            nmap_args=scan_record.nmap_args,
            status=scan_record.status,
            started_at=scan_record.started_at,
            ports_updated=[],  # 剛開始，還沒有任何端口被更新
        )
    except HttpError as e:  # 捕獲自己拋出的 HttpError (比如 409 Conflict)
        raise e
    except Exception as e:  # 捕獲所有其他未知錯誤
        logger.exception(f"啟動 Nmap 掃描 for IP {trigger_data.ip} 時發生意外錯誤: {e}")
        raise HttpError(500, f"無法提交掃描任務，內部服務器錯誤: {e}")


# --- API 端點：查詢掃描任務概覽 ---
@router.get("/list_scans", response=List[NmapScanOverviewSchema])
@log_function_call()
async def list_nmap_scans(
    request, ip_id: Optional[int] = None, status: Optional[str] = None
):
    """
    列出所有 Nmap 掃描任務的概覽。
    因為你有 Hasura，這裡只做最基礎的篩選。
    """
    query = (
        NmapScan.objects.select_related("ip", "ip__which_target")
        .annotate(ports_updated_count=Count("ports_updated"))
        .order_by("-started_at")
    )

    if ip_id:
        query = query.filter(ip_id=ip_id)
    if status:
        query = query.filter(status=status.upper())

    # 操！直接在異步列表推導裡構造 Schema，乾淨利落
    return [
        NmapScanOverviewSchema(
            id=scan.id,
            ip_id=scan.ip_id,
            ip_address=scan.ip.ipv4,
            target_domain=scan.ip.which_target.domain,
            status=scan.status,
            started_at=scan.started_at,
            completed_at=scan.completed_at,
            ports_updated_count=scan.ports_updated_count,
        )
        async for scan in query
    ]


# --- API 端點：獲取單個掃描任務詳情 ---
@router.get("/get_scan/{scan_id}", response=NmapScanSchema)
@log_function_call()
async def get_nmap_scan_detail(request, scan_id: int):
    """
    獲取單個 Nmap 掃描任務的詳細報告。
    """
    try:
        scan = (
            await NmapScan.objects.select_related("ip")
            .prefetch_related("ports_updated")
            .aget(id=scan_id)
        )

        # 操！把關聯的 Port 模型對象轉成 PortSchema
        ports_data = [
            PortSchema.from_orm(port) async for port in scan.ports_updated.all()
        ]

        return NmapScanSchema(
            id=scan.id,
            ip_id=scan.ip_id,
            ip_address=scan.ip.ipv4,
            scan_type=scan.scan_type,
            nmap_args=scan.nmap_args,
            status=scan.status,
            started_at=scan.started_at,
            completed_at=scan.completed_at,
            error_message=scan.error_message,
            ports_updated=ports_data,
        )
    except ObjectDoesNotExist:
        raise HttpError(404, f"Nmap 掃描任務 ID {scan_id} 不存在。")


# --- API 端點：刪除掃描任務 ---
@router.delete("/delete_scan/{scan_id}", response={204: None, 404: ErrorSchema})
@log_function_call()
async def delete_nmap_scan(request, scan_id: int):
    """
    只刪除 Nmap 掃描日誌。關聯的 Port 資產會保留（因為 on_delete=SET_NULL）。
    """
    try:
        scan = await NmapScan.objects.aget(id=scan_id)
        await scan.adelete()
        logger.info(f"成功刪除 Nmap 掃描任務日誌 ID: {scan_id}。")
        return 204
    except ObjectDoesNotExist:
        raise HttpError(404, f"Nmap 掃描任務 ID {scan_id} 不存在。")
