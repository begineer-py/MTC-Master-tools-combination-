# result_assets/api.py
import logging
from ninja import Router, Query, Path
from ninja.errors import HttpError
from typing import List, Union
from urllib.parse import unquote
from asgiref.sync import sync_to_async

from c2_core.config.logging import log_function_call
from core.models import URLResult, Subdomain, IP, Target
from core.schemas import (
    URLResultSchema,
    ErrorSchema,
    URLResultSetSchema,
    IPResultSetSchema,
    get_ip_by_subdomains,
)
from core.get_target import get_target_object
from subfinder.schemas import SubdomainResultSetSchema, SubdomainResultSetSchemaNoIP
from typing import List
from django.db.models import Q  # <--- 引入這個神器

router = Router()
logger = logging.getLogger(__name__)


@log_function_call()
@router.get(
    "/targets/{target_identifier}/urls",
    # 操，這裡改用新的包裝盒 Schema
    response={200: URLResultSetSchema, 404: ErrorSchema},
    tags=["Assets"],
    summary="根據 Target 獲取所有 URL 掃描結果",
)
async def get_all_url_results_for_target(
    request, target_identifier: Union[int, str] = Path(...)
):
    target = await get_target_object(target_identifier)

    logger.info(f"準備獲取 Target '{target.domain}' 的所有 URLResult")

    results_queryset = (
        URLResult.objects.select_related("which_scan_task__which_subdomain")
        .filter(which_scan_task__which_subdomain__which_target=target)
        .prefetch_related(
            "forms", "js_files", "findings", "links", "comments", "meta_tags", "iframes"
        )
        .order_by("-created_at")
    )

    @sync_to_async(thread_sensitive=True)
    def evaluate_queryset_safely(qs):
        return list(qs)

    evaluated_results = await evaluate_queryset_safely(results_queryset)

    logger.info(f"為 Target '{target.domain}' 找到 {len(evaluated_results)} 筆結果。")

    # 操，最關鍵的改動在這裡！
    # 我們不再直接返回列表，而是構建一個符合 URLResultSetSchema 的字典
    response_data = {
        "target_id": target.id,
        "target_domain": target.domain,
        "count": len(evaluated_results),
        "results": evaluated_results,  # 把結果列表放進 'results' 鍵裡
    }

    # 返回這個包裝好的字典
    return 200, response_data


@log_function_call()
@router.get(
    "/targets/{target_identifier}/urls/find",
    response={200: URLResultSchema, 404: ErrorSchema},
    tags=["Assets"],
    summary="在指定目標下，根據 URL 查找單條分析結果",
)
async def find_single_url_result(
    request,
    target_identifier: Union[int, str] = Path(...),
    url: str = Query(..., description="要查找的完整 URL (需 URL-encoded)"),
    offset: int = Query(0, description="查詢歷史版本偏移量。0=最新, 1=第二新, ..."),
):
    """
    在一個目標下，查找一個精確 URL 的最新或歷史分析結果。
    """
    # 同樣，在視圖內部直接、明確地調用
    target = await get_target_object(target_identifier)

    decoded_url = unquote(url)
    logger.info(
        f"在 Target '{target.domain}' 下查找 URL: {decoded_url} (offset={offset})"
    )

    results_queryset = (
        URLResult.objects.select_related(
            "which_scan_task__which_subdomain"  # <-- 告訴 Django: "把 URLScan 和 Subdomain 的資料都給我一次性查出來！"
        )
        .filter(which_scan_task__which_subdomain__which_target=target, url=decoded_url)
        .prefetch_related(  # prefetch_related 用於多對多或反向外鍵，保持不變
            "forms", "js_files", "findings", "links", "comments", "meta_tags", "iframes"
        )
        .order_by("-created_at")
    )

    @sync_to_async(thread_sensitive=True)
    def get_result_at_offset(queryset, off):
        try:
            return queryset[off]
        except IndexError:
            return None

    url_result = await get_result_at_offset(results_queryset, offset)

    if not url_result:
        raise HttpError(
            404,
            f"URL '{decoded_url}' with offset {offset} not found in Target '{target.domain}'.",
        )

    return url_result


@router.get(
    "/targets/{target_identifier}/subdomains/",
    response={200: SubdomainResultSetSchemaNoIP, 404: ErrorSchema},
    tags=["Assets"],
    summary="根據 Target 獲取所有子域名掃描結果",
)
@log_function_call()
async def get_all_subdomains_for_target(
    request,
    target_identifier: Union[int, str] = Path(...),
):
    target = await get_target_object(target_identifier)

    logger.info(f"準備獲取 Target '{target.domain}' 的所有 Subdomain")

    subdomains_queryset = (
        Subdomain.objects.select_related("ip")  # <-- 操，這裡加上 "ip"
        .filter(which_target=target)
        .order_by("-created_at")
    )

    @sync_to_async(thread_sensitive=True)
    def evaluate_queryset_safely(qs):
        return list(qs)

    evaluated_subdomains = await evaluate_queryset_safely(subdomains_queryset)

    logger.info(
        f"為 Target '{target.domain}' 找到 {len(evaluated_subdomains)} 筆結果。"
    )

    # 操，最關鍵的改動在這裡！
    # 我們不再直接返回列表，而是構建一個符合 SubdomainResultSetSchema 的字典
    response_data = {
        "target_id": target.id,
        "target_domain": target.domain,
        "count": len(evaluated_subdomains),
        "results": evaluated_subdomains,  # 把結果列表放進 'results' 鍵裡
    }

    # 返回這個包裝好的字典
    return 200, response_data


# result_assets/api.py


@log_function_call()
@router.get(
    "/targets/{target_identifier}/subdomain/urls",
    response={200: URLResultSetSchema, 404: ErrorSchema},
    tags=["Assets"],
    summary="獲取特定子域名下的所有 URL 掃描結果 (By Query Param)",
)
async def get_urls_by_subdomain_name(
    request,
    target_identifier: Union[int, str] = Path(...),
    name: str = Query(
        ..., description="子域名完整名稱 (例如: api.example.com)"
    ),  # 必填參數
):
    """
    專用接口：查詢指定 Target 下，特定名稱子域名的所有 URL。
    用法: GET /targets/1/subdomain/urls?name=api.example.com
    """
    # 1. 鎖定目標
    target = await get_target_object(target_identifier)

    # 2. 解碼參數 (以防萬一)
    decoded_name = unquote(name)

    logger.info(
        f"準備獲取 Target '{target.domain}' 下子域名 '{decoded_name}' 的 URL 結果"
    )

    # 3. 構建查詢
    # 強制過濾子域名名稱
    results_queryset = (
        URLResult.objects.select_related("which_scan_task__which_subdomain")
        .filter(
            which_scan_task__which_subdomain__which_target=target,
            which_scan_task__which_subdomain__name=decoded_name,
        )
        .prefetch_related(
            "forms", "js_files", "findings", "links", "comments", "meta_tags", "iframes"
        )
        .order_by("-created_at")
    )

    # 4. 異步執行
    @sync_to_async(thread_sensitive=True)
    def fetch_results(qs):
        return list(qs)

    evaluated_results = await fetch_results(results_queryset)

    logger.info(
        f"子域名 '{decoded_name}' 下找到 {len(evaluated_results)} 筆 URL 結果。"
    )

    # 5. 包裝返回
    response_data = {
        "target_id": target.id,
        "target_domain": target.domain,
        "count": len(evaluated_results),
        "results": evaluated_results,
    }

    return 200, response_data


@log_function_call()
@router.get(
    "/targets/{target_identifier}/ips/subdomains",
    response={200: SubdomainResultSetSchema, 404: ErrorSchema},
    tags=["Assets"],
    summary="找出指定 IP 關聯的所有子域名",
)
async def get_subdomains_by_ip(
    request,
    target_identifier: Union[int, str] = Path(...),
    ip: str = Query(..., description="要查詢的 IP 地址 (IPv4 或 IPv6)"),
):
    """
    【地獄級查詢】
    輸入一個 IP 地址，找出該目標下所有解析到該 IP 的子域名。
    這對於發現「旁站」或「同一台服務器上的關聯資產」至關重要。
    """
    # 1. 鎖定目標
    target = await get_target_object(target_identifier)

    # 2. 清洗輸入 (去除空白)
    query_ip = ip.strip()

    logger.info(f"正在對 Target '{target.domain}' 執行 IP 反查: {query_ip}")

    @sync_to_async(thread_sensitive=True)
    def fetch_data():
        qs = (
            Subdomain.objects.select_related(
                "ip"
            )  # 依然需要預加載，為了返回數據時不 N+1
            .filter(which_target=target)
            .filter(Q(ip__ipv4=query_ip) | Q(ip__ipv6=query_ip))
            .order_by("name")
        )
        return list(qs)

    # 4. 異步執行
    matched_subdomains = await fetch_data()

    logger.info(f"IP {query_ip} 查找成功，關聯了 {len(matched_subdomains)} 個子域名。")

    # 5. 包裝返回
    response_data = {
        "target_id": target.id,
        "target_domain": target.domain,
        "count": len(matched_subdomains),
        "ip": query_ip,
        "results": matched_subdomains,
    }

    return 200, response_data


@log_function_call()
@router.get(
    "/targets/{target_identifier}/ips",
    response={200: IPResultSetSchema, 404: ErrorSchema},
    tags=["Assets"],
    summary="獲取 Target 的所有 IP 資產 (支持高級過濾)",
)
async def get_target_ips(
    request,
    target_identifier: Union[int, str] = Path(...),
    # --- 新增過濾參數 ---
    origin_only: bool = Query(False, description="只顯示非 CDN 的源站 IP"),
    linked_only: bool = Query(False, description="只顯示有關聯子域名的 IP"),
):
    """
    列出屬於該目標的所有 IP 地址。
    - ?origin_only=true: 過濾掉 CDN IP。
    - ?linked_only=true: 只顯示那些當前有關聯子域名的 IP。
    """
    target = await get_target_object(target_identifier)

    log_msg = f"準備提取 Target '{target.domain}' 的 IP 資產"
    if origin_only or linked_only:
        log_msg += " (過濾條件:"
        if origin_only:
            log_msg += " origin_only"
        if linked_only:
            log_msg += " linked_only"
        log_msg += ")"
    logger.info(log_msg)

    # 1. 基礎查詢
    query = IP.objects.filter(which_target=target)

    if origin_only:
        query = query.filter(subdomains__is_cdn=False).distinct()  # 第一個 filter

    if linked_only:
        query = query.filter(subdomains__is_resolvable=True).distinct()  # 第二個 filter

    # 3. 排序和異步撈取
    @sync_to_async(thread_sensitive=True)
    def fetch_ips(qs):
        return list(qs.order_by("ipv4"))

    ips = await fetch_ips(query)

    logger.info(f"提取到 {len(ips)} 個 IP 資產。")

    # 4. 包裝返回 (不變)
    response_data = {
        "target_id": target.id,
        "target_domain": target.domain,
        "count": len(ips),
        "results": ips,
    }
    return 200, response_data


# 以下皆爲反查
@log_function_call()
@router.get(
    "/targets/{target_identifier}/subdomainsTOip",
    response={200: get_ip_by_subdomains, 404: ErrorSchema},
    tags=["Assets"],
    summary="使用subdomains反查ip",
)
async def get_ip_for_subdomain_v2(
    request,
    target_identifier: Union[int, str] = Path(...),
    name: str = Query(..., description="要查詢的子域名完整名稱"),  # <-- 改回 Query 參數
):
    "使用subdomains反查ip"
    target = await get_target_object(target_identifier)
    logger.info(f"準備使用subdomains {name}反查ip")

    @sync_to_async(thread_sensitive=True)
    def fetch_ip_by_subdomain(subdomain):
        return (
            IP.objects.select_related("which_target")
            .filter(which_target=target, subdomains__name=subdomain)  # <--- 加上這個
            .first()
        )

    ip = await fetch_ip_by_subdomain(name)
    if not ip:
        raise HttpError(404, f"Subdomain '{name}' not found.")

    logger.info(f"找到 Subdomain '{name}' 的 IP: {ip}")

    return get_ip_by_subdomains(target_id=target.id, target_domain=target.domain, ip=ip)


import json
from ninja import Body


@router.post(
    "/targets/{target_identifier}/urls/search/advanced",
    response={200: URLResultSetSchema, 400: ErrorSchema},
    tags=["Assets Search"],
    summary="[上帝模式] 支援 AND/OR/NOT 巢狀邏輯的萬能查詢",
)
async def god_mode_search(
    request,
    target_identifier: Union[int, str] = Path(...),
    # 用 POST Body 傳 JSON，因為這種複雜結構放 Query Param 會太長
    query: dict = Body(
        ..., description="遞歸查詢結構: {'OR': [...], 'status_code': 200}"
    ),
):
    target = await get_target_object(target_identifier)

    # 1. 鎖定範圍 + 預加載 (效能優化)
    base_qs = (
        URLResult.objects.filter(which_scan_task__which_subdomain__which_target=target)
        .select_related("which_scan_task__which_subdomain")
        .prefetch_related("forms")
    )  # 根據你的需求加載

    # 2. 呼叫黑魔法構造 Q 物件
    try:
        final_q = build_q_object(query)
        logger.debug(f"Generated SQL Q: {final_q}")
    except Exception as e:
        return 400, {"detail": f"Query Build Error: {str(e)}"}

    # 3. 執行查詢
    @sync_to_async(thread_sensitive=True)
    def execute():
        # distinct() 非常重要，因為跨表查詢(Form)可能會造成 URL 重複
        return list(base_qs.filter(final_q).distinct().order_by("-created_at")[:500])

    results = await execute()

    return 200, {
        "target_id": target.id,
        "target_domain": target.domain,
        "count": len(results),
        "results": results,
    }
