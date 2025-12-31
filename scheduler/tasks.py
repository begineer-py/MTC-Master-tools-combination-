import logging
from random import seed
from kombu.utils import objects
import requests
from celery import shared_task
from django.db.models import Q, Count
from c2_core.settings import API_BASE_URL
from core.models import URLResult, IP, Subdomain
from c2_core.config.logging import log_function_call

logger = logging.getLogger(__name__)

# API Endpoints
NMAP_API_ENDPOINT = f"{API_BASE_URL}/api/nmap/start_scan"
GET_ALL_URL_ENDPOINT_TEMPLATE = f"{API_BASE_URL}/api/get_all_url/get_all_url"
FLARESOLVERR_START_SCANNER_URL = f"{API_BASE_URL}/api/flaresolverr/start_scanner"
AI_ANALYZES_IP = f"{API_BASE_URL}/api/analyze_ai/ips"
AI_ANALYZES_SUBDOMAINS = f"{API_BASE_URL}/api/analyze_ai/subdomains"
AI_ANALYZES_URL = f"{API_BASE_URL}/api/analyze_ai/urls"
NUCLEI_SCAN_URL = f"{API_BASE_URL}/api/nuclei"


# 1. Nmap 掃描觸發器
@shared_task(name="scheduler.tasks.scan_ips_without_nmap_results")
@log_function_call()
def scan_ips_without_nmap_results(batch_size: int = 10):
    logger.info(f"定時任務啟動：查找無 Nmap 記錄的 IP (Limit {batch_size})")

    ips_to_scan = (
        IP.objects.annotate(scan_count=Count("nmap_scans"))
        .filter(scan_count=0)
        .select_related("which_target")[:batch_size]
    )

    actual_count = len(ips_to_scan)
    if actual_count == 0:
        return "No new IPs to scan."

    success_count = 0
    for ip_obj in ips_to_scan:
        payload = {
            "target_id": ip_obj.which_target.id,
            "ip": ip_obj.ipv4 or ip_obj.ipv6,
        }
        try:
            resp = requests.post(NMAP_API_ENDPOINT, json=payload, timeout=10)
            if 200 <= resp.status_code < 300:
                success_count += 1
            else:
                logger.error(f"Nmap API Error {ip_obj.ipv4}: {resp.status_code}")
        except Exception as e:
            logger.exception(f"Nmap Req Failed: {e}")

    return f"Triggered Nmap for {success_count}/{actual_count} IPs."


# 2. Subdomain URL 發現觸發器
@shared_task(name="scheduler.tasks.scan_subdomains_without_url_results")
@log_function_call()
def scan_subdomains_without_url_results(batch_size: int = 5):
    logger.info(f"定時任務啟動：查找無 URL 掃描的子域名 (Limit {batch_size})")

    subdomains_to_scan = (
        Subdomain.objects.annotate(scan_count=Count("scans_targeted"))
        .filter(scan_count=0, is_active=True, is_resolvable=True)
        .order_by("-id")[:batch_size]
    )

    actual_count = len(subdomains_to_scan)
    if actual_count == 0:
        return "No new Subdomains to scan."

    success_count = 0
    for sub_obj in subdomains_to_scan:
        try:
            resp = requests.post(
                GET_ALL_URL_ENDPOINT_TEMPLATE, json={"name": sub_obj.name}, timeout=5
            )
            if 200 <= resp.status_code < 300:
                success_count += 1
        except Exception as e:
            logger.error(f"URL Scan Req Failed ({sub_obj.name}): {e}")

    return f"Triggered URL Scan for {success_count}/{actual_count} Subdomains."


# 3. URL 內容抓取觸發器 (FlareSolverr)
@shared_task(name="scheduler.tasks.scan_urls_missing_response")
@log_function_call()
def scan_urls_missing_response(batch_size: int = 5):
    logger.info(f"定時任務啟動：查找未抓取內容的 URL (Limit {batch_size})")

    urls_to_scan = URLResult.objects.filter(content_fetch_status="PENDING").order_by(
        "-id"
    )[:batch_size]

    actual_count = len(urls_to_scan)
    if actual_count == 0:
        return "No new URLs to fetch."

    success_count = 0
    for url_obj in urls_to_scan:
        try:
            resp = requests.post(
                FLARESOLVERR_START_SCANNER_URL,
                json={"url": url_obj.url, "method": "GET"},
                timeout=5,
            )
            if 200 <= resp.status_code < 300:
                success_count += 1
        except Exception as e:
            logger.error(f"FlareSolverr Req Failed ({url_obj.url}): {e}")

    return f"Triggered Fetch for {success_count}/{actual_count} URLs."


# 4. AI 分析 IP 觸發器
@shared_task(name="scheduler.tasks.trigger_scan_ips_without_ai_results")
@log_function_call()
def trigger_scan_ips_without_ai_results(batch_size: int = 10):
    logger.info(f"定時任務：AI 分析 IP (Limit {batch_size})")

    ips_qs = (
        # 修正：使用正確的 M2M 字段名 'discovered_by_scans'
        IP.objects.filter(discovered_by_scans__status="COMPLETED")
        .exclude(ai_analysis__status__in=["COMPLETED", "RUNNING"])
        .distinct()  # 關鍵：防止因多個 Nmap 掃描記錄導致同一 IP 重複出現
        .order_by("-id")[:batch_size]
    )

    targets = list(set([ip.ipv4 or ip.ipv6 for ip in ips_qs if ip.ipv4 or ip.ipv6]))
    if not targets:
        return

    try:
        requests.post(AI_ANALYZES_IP, json={"ips": targets}, timeout=5)
    except Exception as e:
        logger.error(f"AI IP API Failed: {e}")


# 5. AI 分析 Subdomain 觸發器
@shared_task(name="scheduler.tasks.trigger_scan_subdomains_without_ai_results")
@log_function_call()
def trigger_scan_subdomains_without_ai_results(batch_size: int = 10):
    logger.info(f"定時任務：AI 分析子域名 (Limit {batch_size})")

    subdomains_qs = (
        Subdomain.objects.filter(is_active=True)
        .exclude(ai_analysis__status__in=["COMPLETED", "RUNNING"])
        .order_by("-id")[:batch_size]
    )
    targets = list(subdomains_qs.values_list("name", flat=True))
    if not targets:
        return

    try:
        requests.post(AI_ANALYZES_SUBDOMAINS, json={"subdomains": targets}, timeout=5)
    except Exception as e:
        logger.error(f"AI Subdomain API Failed: {e}")


# ==========================================
# 核心優化：URL 去重邏輯 (Hash & Final URL)
# ==========================================


def get_unique_urls_for_analysis(queryset, check_ai=True):
    """
    通用去重函數：
    1. 過濾掉 MD5 Hash 重複的 URL
    2. 過濾掉 Final URL 重複的 URL
    """
    unique_urls = []
    seen_hashes = set()
    seen_finals = set()

    # 這裡我們取大一點的候選集，以便去重後還能剩下一部分
    # 注意：這裡的 queryset 已經包含 [:batch_size] 限制，
    # 實際生產中可能需要取 batch_size * 2 來保證填滿隊列，
    # 但為了防止 N+1，我們先簡單處理當前批次。

    for url_obj in queryset:
        # 1. 檢查 Hash (內容完全一致)
        if url_obj.raw_response_hash:
            if url_obj.raw_response_hash in seen_hashes:
                logger.debug(f"跳過重複 Hash URL: {url_obj.url}")
                continue
            seen_hashes.add(url_obj.raw_response_hash)

        # 2. 檢查 Final URL (跳轉終點一致)
        if url_obj.final_url:
            if url_obj.final_url in seen_finals:
                logger.debug(f"跳過重複 Final URL: {url_obj.url}")
                continue
            seen_finals.add(url_obj.final_url)

        # 通過篩選
        unique_urls.append(url_obj.url)

    return unique_urls


# 6. AI 分析 URL 觸發器 (已升級去重)
@shared_task(name="scheduler.tasks.trigger_scan_urls_without_ai_results")
@log_function_call()
def trigger_scan_urls_without_ai_results(batch_size: int = 5):
    logger.info(f"定時任務：AI 分析 URL (Limit {batch_size}, 智能去重)")

    # 獲取候選集：多取一些(x2)，因為去重會篩掉一部分
    candidate_qs = (
        URLResult.objects.filter(content_fetch_status="SUCCESS_FETCHED")
        .exclude(ai_analysis__status__in=["COMPLETED", "RUNNING"])
        .exclude(status_code=404)
        .order_by("-id")[: batch_size * 2]
    )

    # 執行內存級去重
    target_urls = get_unique_urls_for_analysis(candidate_qs)

    # 再次截斷到用戶要求的 batch_size
    target_urls = target_urls[:batch_size]

    if not target_urls:
        return "No unique URLs for AI analysis."

    try:
        requests.post(AI_ANALYZES_URL, json={"urls": target_urls}, timeout=5)
        return f"Dispatched {len(target_urls)} Unique URLs to AI."
    except Exception as e:
        logger.error(f"AI URL API Failed: {e}")


# 7. Nuclei 分析 URL 觸發器 (已升級去重)
@shared_task(name="scheduler.tasks.trigger_scan_urls_without_nuclei_results")
@log_function_call()
def trigger_scan_urls_without_nuclei_results(batch_size: int = 5):
    logger.info(f"定時任務：Nuclei 掃描 URL (Limit {batch_size}, 智能去重)")

    # 使用正確的 related_name 查詢
    candidate_qs = (
        URLResult.objects.filter(content_fetch_status="SUCCESS_FETCHED")
        .exclude(nuclei_scans__status__in=["COMPLETED", "RUNNING"])  # 包含重試邏輯
        .order_by("-id")[: batch_size * 2]
    )

    # 執行內存級去重
    target_urls = get_unique_urls_for_analysis(candidate_qs)
    target_urls = target_urls[:batch_size]

    if not target_urls:
        return "No unique URLs for Nuclei scan."

    try:
        requests.post(f"{NUCLEI_SCAN_URL}/urls", json={"urls": target_urls}, timeout=5)
        return f"Dispatched {len(target_urls)} Unique URLs to Nuclei."
    except Exception as e:
        logger.error(f"Nuclei URL API Failed: {e}")


# 8. Nuclei 分析 Subdomain 觸發器
@shared_task(name="scheduler.tasks.trigger_scan_subdomains_without_nuclei_results")
@log_function_call()
def trigger_scan_subdomains_without_nuclei_results(batch_size: int = 5):
    logger.info(f"定時任務：Nuclei 掃描子域名 (Limit {batch_size})")

    subdomains_qs = (
        Subdomain.objects.filter(is_active=True)
        .exclude(nuclei_scans__status__in=["COMPLETED", "RUNNING"])
        .order_by("-id")[:batch_size]
    )
    targets = list(subdomains_qs.values_list("name", flat=True))

    if not targets:
        return

    try:
        requests.post(
            f"{NUCLEI_SCAN_URL}/subdomains", json={"subdomains": targets}, timeout=5
        )
    except Exception as e:
        logger.error(f"Nuclei Subdomain API Failed: {e}")


# 9. Nuclei 分析 IP 觸發器 (邏輯修復版)
@shared_task(name="scheduler.tasks.trigger_scan_ips_without_nuclei_results")
@log_function_call()
def trigger_scan_ips_without_nuclei_results(batch_size: int = 10):
    """
    IP 發現即掃描：只要 IP 存在且沒有成功的 Nuclei 記錄，就開火。
    """
    logger.info(f"定時任務：Nuclei 掃描 IP (Limit {batch_size})")

    # 修正邏輯：使用 exclude status 而不是 isnull，允許重試
    ips_qs = (
        IP.objects.all()
        .exclude(nuclei_scans__status__in=["COMPLETED", "RUNNING"])
        .order_by("-id")[:batch_size]
    )

    target_ips = []
    for ip_obj in ips_qs:
        val = ip_obj.ipv4 or ip_obj.ipv6
        if val:
            target_ips.append(val)

    target_ips = list(set(target_ips))

    if not target_ips:
        return "No IPs pending for Nuclei scan."

    try:
        requests.post(f"{NUCLEI_SCAN_URL}/ips", json={"ips": target_ips}, timeout=5)
        return f"Dispatched {len(target_ips)} IPs to Nuclei."
    except Exception as e:
        logger.error(f"Nuclei IP API Failed: {e}")
