import logging
from ninja import Router, Schema
from ninja.errors import HttpError
from typing import List, Optional
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count

# 操！導入正確的模型
from core.models import IP, Seed
from core.models import NmapScan
from .schemas import (
    NmapScanTriggerSchema,
    NmapScanSchema,
    ErrorSchema,
)
from .tasks import perform_nmap_scan
from c2_core.config.logging import log_function_call
from django.db.models import Q

router = Router()
logger = logging.getLogger(__name__)

# ... (其他 import 保持不變) ...


@router.post("/start_scan", response={202: NmapScanSchema})
@log_function_call()
async def start_nmap_scan(request, trigger_data: NmapScanTriggerSchema):
    ip_str = trigger_data.ip
    seed_id = trigger_data.seed_id

    # 1. 獲取 IP 和 Seed
    try:
        # 這裡建議同時支援 ipv4 或 ipv6 查詢，增加魯棒性
        ip_obj = await IP.objects.filter(Q(ipv4=ip_str) | Q(ipv6=ip_str)).afirst()
        if not ip_obj:
            raise HttpError(404, f"找不到 IP 資產: {ip_str}")
    except Exception as e:
        raise HttpError(500, f"資料庫查詢失敗: {str(e)}")

    try:
        seed = await Seed.objects.aget(id=seed_id)
    except Seed.DoesNotExist:
        raise HttpError(404, f"找不到 seed: {seed_id}")

    # 2. 檢查是否有正在進行的掃描 (修正欄位名為 ips_discovered)
    existing_active_scan = await NmapScan.objects.filter(
        ips_discovered=ip_obj, status__in=["PENDING", "RUNNING"]
    ).afirst()

    if existing_active_scan:
        raise HttpError(
            409,
            f"IP {ip_str} 已有正在進行中的任務 (ID: {existing_active_scan.id})",
        )

    # 3. 參數組裝 (保持你的邏輯)
    args = []
    # ... (你的 args 組裝邏輯) ...
    args.append("-oX -")
    final_nmap_args = " ".join(args)

    # 4. 創建 NmapScan 紀錄
    # 注意：M2M 欄位 ips_discovered 不能在 acreate 裡直接傳
    scan_record = await NmapScan.objects.acreate(
        which_seed=seed,  # NmapScan 模型裡確實有這個 ForeignKey
        nmap_args=final_nmap_args,
        status="PENDING",
    )

    # 5. 建立 M2M 關聯 (必須在 acreate 之後)
    # 由於 Django M2M manager 目前對 async 支持有限，通常需要 sync_to_async
    from asgiref.sync import sync_to_async

    await sync_to_async(scan_record.ips_discovered.add)(ip_obj)

    logger.info(f"為 IP {ip_str} 創建新的 NmapScan 記錄: ID={scan_record.id}")

    # 6. 觸發任務
    perform_nmap_scan.delay(
        scan_id=scan_record.id,
        ip_address=ip_str,
        nmap_args=final_nmap_args,
    )

    return NmapScanSchema(
        id=scan_record.id,
        ip_id=ip_obj.id,
        ip_address=[ip_obj.ipv4] if ip_obj.ipv4 else [ip_obj.ipv6],
        scan_type="custom_scan",
        nmap_args=scan_record.nmap_args,
        status=scan_record.status,
        started_at=scan_record.started_at,
        completed_at=scan_record.completed_at,
        error_message=scan_record.error_message,
    )


# --- API 端點：刪除掃描任務 ---
@router.delete("/delete_scan/{scan_id}", response={204: None, 404: ErrorSchema})
@log_function_call()
async def delete_nmap_scan(scan_id: int):
    """刪除指定的 Nmap 掃描任務。"""
    try:
        scan = await NmapScan.objects.aget(id=scan_id)
        await scan.adelete()
        logger.info(f"成功刪除 Nmap 掃描任務日誌 ID: {scan_id}。")
        return 204
    except ObjectDoesNotExist:
        raise HttpError(404, f"Nmap 掃描任務 ID {scan_id} 不存在。")
