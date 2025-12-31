import logging
from random import seed
from kombu.utils import objects
import requests
from celery import shared_task
from django.db.models import Q
from c2_core.settings import API_BASE_URL
from core.models import URLResult, IP
from django.db.models import Count
from core.models import Subdomain, URLResult  # 補上這個
from core.models import IPAIAnalysis, SubdomainAIAnalysis, URLAIAnalysis
from c2_core.config.logging import log_function_call

logger = logging.getLogger(__name__)

NMAP_API_ENDPOINT = f"{API_BASE_URL}/api/nmap/start_scan"
GET_ALL_URL_ENDPOINT_TEMPLATE = f"{API_BASE_URL}/api/get_all_url/get_all_url"

FLARESOLVERR_START_SCANNER_URL = f"{API_BASE_URL}/api/flaresolverr/start_scanner"
AI_ANALYZES_IP = f"{API_BASE_URL}/api/analyze_ai/ips"
AI_ANALYZES_SUBDOMAINS = f"{API_BASE_URL}/api/analyze_ai/subdomains"
AI_ANALYZES_URL = f"{API_BASE_URL}/api/analyze_ai/urls"
NUCLEI_SCAN_URL = f"{API_BASE_URL}/api/nuclei"


# 操！這裡！給函數加上一個參數，並給一個合理的預設值
@shared_task(name="scheduler.tasks.scan_ips_without_nmap_results")
@log_function_call()
def scan_ips_without_nmap_results(batch_size: int = 10):
    """
    找出指定數量(batch_size)的、從未被 Nmap 掃描過的 IP 資產，
    並通過 API 為它們觸發掃描任務。
    """
    logger.info(
        f"定時任務啟動：開始查找無 Nmap 掃描記錄的 IP，本次處理上限為 {batch_size} 個。"
    )

    # 操！這裡！在查詢的最後，用切片 [:batch_size] 來限制數量
    # 這在資料庫層面會被翻譯成 LIMIT 10，效率極高
    ips_to_scan = (
        IP.objects.annotate(scan_count=Count("nmap_scans"))
        .filter(scan_count=0)
        .select_related("which_target")[:batch_size]  # <--- 核心改動在這裡
    )

    # 獲取實際查詢到的數量
    actual_count = len(ips_to_scan)

    if actual_count == 0:
        logger.info("所有 IP 都已有掃描記錄，或隊列中無新目標，本次任務結束。")
        return "No new IPs to scan in this batch."

    logger.info(
        f"發現 {actual_count} 個 IP 需要進行初次 Nmap 掃描（批次上限 {batch_size}）。"
    )

    success_count = 0
    failure_count = 0

    for ip_obj in ips_to_scan:
        target_id = ip_obj.which_target.id
        ip_address = ip_obj.ipv4

        payload = {
            "target_id": target_id,
            "ip": ip_address,
        }

        try:
            response = requests.post(NMAP_API_ENDPOINT, json=payload, timeout=10)
            if 200 <= response.status_code < 300:
                logger.info(
                    f"成功為 IP {ip_address} (Target ID: {target_id}) 觸發掃描任務。"
                )
                success_count += 1
            else:
                logger.error(
                    f"為 IP {ip_address} 觸發掃描任務失敗。 "
                    f"API 返回狀態碼: {response.status_code}, "
                    f"響應: {response.text}"
                )
                failure_count += 1
        except requests.exceptions.RequestException as e:
            logger.exception(f"調用 Nmap API for IP {ip_address} 時發生網絡錯誤: {e}")
            failure_count += 1

    summary = f"定時掃描任務完成。處理 IP 數量: {actual_count}。成功觸發: {success_count} 個, 失敗: {failure_count} 個。"
    logger.info(summary)
    return summary


@shared_task(name="scheduler.tasks.scan_subdomains_without_url_results")
@log_function_call()
def scan_subdomains_without_url_results(batch_size: int = 5):
    """
    定期巡邏任務：
    找出指定數量(batch_size)的、活躍且可解析，但從未進行過 URL 掃描的子域名，
    並通過 API 為它們觸發掃描任務。
    """
    logger.info(
        f"定時任務啟動：開始查找無 URL 掃描記錄的 Subdomain，本次處理上限為 {batch_size} 個。"
    )

    # 1. 篩選策略
    # - scans_targeted__count=0: 從沒掃過 (基於 related_name='scans_targeted')
    # - is_active=True: 必須是活的
    # - is_resolvable=True: 必須能解析出 IP (不然 Katana 也是掃了個寂寞)
    subdomains_to_scan = (
        Subdomain.objects.annotate(scan_count=Count("scans_targeted"))
        .filter(scan_count=0, is_active=True, is_resolvable=True)
        .order_by("-id")[:batch_size]  # 優先處理最新發現的子域名
    )

    # 獲取實際查詢到的數量
    actual_count = len(subdomains_to_scan)

    if actual_count == 0:
        logger.info("所有活躍子域名都已有 URL 掃描記錄，隊列清空，本次任務結束。")
        return "No new Subdomains to scan in this batch."

    logger.info(
        f"發現 {actual_count} 個 Subdomain 需要進行初次 URL 掃描（批次上限 {batch_size}）。"
    )

    success_count = 0
    failure_count = 0

    for sub_obj in subdomains_to_scan:
        subdomain_name = sub_obj.name

        # 構造 Payload (對應 ScanAllUrlSchema)
        payload = {
            "name": subdomain_name,
        }

        try:
            # 這裡直接打內部 API，讓 View 層去處理權限和觸發異步任務
            # timeout 設短一點，因為 View 只是派發任務，應該很快返回
            response = requests.post(
                GET_ALL_URL_ENDPOINT_TEMPLATE, json=payload, timeout=5
            )

            if 200 <= response.status_code < 300:
                logger.info(
                    f"成功為子域名 {subdomain_name} (Seed: {sub_obj.which_seed.value}) 觸發 URL 掃描。"
                )
                success_count += 1
            else:
                # 如果是 400/404 等錯誤，可能是邏輯問題（例如 View 層校驗失敗）
                logger.error(
                    f"為子域名 {subdomain_name} 觸發掃描失敗。 "
                    f"API URL: {GET_ALL_URL_ENDPOINT_TEMPLATE} "
                    f"Status: {response.status_code}, "
                    f"Response: {response.text}"
                )
                failure_count += 1

        except requests.exceptions.RequestException as e:
            logger.exception(f"調用 API 失敗 (Subdomain: {subdomain_name}): {e}")
            failure_count += 1

    summary = (
        f"定時 URL 掃描任務完成。處理 Subdomain 數量: {actual_count}。 "
        f"成功觸發: {success_count} 個, 失敗: {failure_count} 個。"
    )
    logger.info(summary)
    return summary


@shared_task(name="scheduler.tasks.scan_urls_missing_response")
@log_function_call()
def scan_urls_missing_response(batch_size: int = 5):
    """
    定期巡邏任務：
    找出指定數量(batch_size)的「未探測」URL。

    定義「未探測」:
    1. 沒有 status_code (代表 httpx/flaresolverr 還沒跑過)
    2. 沒有 raw_response (代表還沒抓取內容)

    一旦掃描成功，status_code 會被填入 (即使是 404 或 200)，
    這樣下次就不會再重複掃描它，避免了對空響應頁面的無限重試。
    """
    logger.info(
        f"定時任務啟動：開始查找未探測 (No Status/No Body) 的 URLResult，本次處理上限為 {batch_size} 個。"
    )

    # 1. 嚴格篩選策略
    urls_to_scan = URLResult.objects.filter(
        # 條件 A: 內容為空
        Q(content_fetch_status="PENDING")
    ).order_by("-id")[
        :batch_size
    ]  # 優先處理最新的數據

    # 獲取實際查詢到的數量
    actual_count = len(urls_to_scan)

    if actual_count == 0:
        logger.info("隊列中沒有待探測的新 URL，本次任務結束。")
        return "No new URLs to scan."

    logger.info(f"發現 {actual_count} 個新 URL 需要進行 FlareSolverr 掃描。")

    success_count = 0
    failure_count = 0

    for url_obj in urls_to_scan:
        # 為了防止單個任務崩潰影響整批，使用 try-except 包裹
        try:

            url = url_obj.url

            # 構造 Payload
            payload = {
                "url": url,
                "method": "GET",
            }

            # 發送請求到內部 API
            # timeout 設短一點，因為 View 只是負責派發 Celery 任務，應該很快
            response = requests.post(
                FLARESOLVERR_START_SCANNER_URL, json=payload, timeout=5
            )

            if 200 <= response.status_code < 300:
                logger.info(f"[成功] 已觸發掃描 -> URL: {url} (ID: {url_obj.id})")
                success_count += 1
            else:
                logger.error(
                    f"[失敗] API 拒絕 -> URL: {url}. Status: {response.status_code}, Msg: {response.text}"
                )
                failure_count += 1

        except Exception as e:
            logger.exception(f"[異常] 處理 URL ID {url_obj.id} 時發生錯誤: {e}")
            failure_count += 1

    summary = (
        f"定時 URL 探測任務完成。總數: {actual_count}。 "
        f"成功派發: {success_count}, 失敗: {failure_count}。"
    )
    logger.info(summary)
    return summary


@shared_task(name="scheduler.tasks.trigger_scan_ips_without_ai_results")
@log_function_call()
def trigger_scan_ips_without_ai_results(batch_size: int = 10):
    """
    定期巡邏任務：
    找出指定數量(batch_size)的「未分析」IP。
    """
    logger.info(
        f"定時任務啟動：開始查找未分析 (No AI Results) 的 IP，本次處理上限為 {batch_size} 個。"
    )
    ips_qs = (
        IP.objects.filter(nmap_scans__status="COMPLETED")
        .exclude(ai_analysis__status__in=["COMPLETED", "RUNNING"])
        .order_by("-id")[:batch_size]
    )

    target_ip_strings = []
    for ip_obj in ips_qs:
        if ip_obj.ipv4:
            target_ip_strings.append(ip_obj.ipv4)
        elif ip_obj.ipv6:
            target_ip_strings.append(ip_obj.ipv6)

    # 去重 (防止一個 IP 既有 v4 又有 v6 導致邏輯重複，雖然目前模型結構不太可能)
    target_ip_strings = list(set(target_ip_strings))

    if not target_ip_strings:
        logger.info("沒有發現符合條件的待分析 IP，任務結束。")
        return

    logger.info(f"鎖定 {len(target_ip_strings)} 個 IP，正在發送 API 請求...")

    # 4. 發送 HTTP 請求
    try:
        response = requests.post(
            AI_ANALYZES_IP,
            json={"ips": target_ip_strings},
            timeout=5,  # 務必設置超時，防止定時任務卡死
        )

        if response.status_code == 202:
            logger.info(f"API 調用成功: {response.json()}")
        else:
            logger.error(f"API 調用失敗 [{response.status_code}]: {response.text}")

    except requests.RequestException as e:
        logger.error(f"連接 API 失敗: {e}")


@shared_task(name="scheduler.tasks.trigger_scan_subdomains_without_ai_results")
@log_function_call()
def trigger_scan_subdomains_without_ai_results(batch_size: int = 10):
    """
    定期巡邏任務：
    找出指定數量(batch_size)的「未分析」子域名。
    """
    logger.info(
        f"定時任務啟動：開始查找未分析 (No AI Results) 的子域名，本次處理上限為 {batch_size} 個。"
    )
    subdomains_qs = (
        Subdomain.objects.filter(is_active=True)
        .exclude(ai_analysis__status__in=["COMPLETED", "RUNNING"])
        .order_by("-id")[:batch_size]
    )
    target_subdomains = list(subdomains_qs.values_list("name", flat=True))

    if not target_subdomains:
        logger.info("沒有發現符合條件的待分析子域名，任務結束。")
        return
    try:
        response = requests.post(
            AI_ANALYZES_SUBDOMAINS,
            json={"subdomains": target_subdomains},
            timeout=5,
        )

        if response.status_code == 202:
            logger.info(f"API 調用成功: {response.json()}")
        else:
            logger.error(f"API 調用失敗 [{response.status_code}]: {response.text}")

    except requests.RequestException as e:
        logger.error(f"連接 API 失敗: {e}")
    return


@shared_task(name="scheduler.tasks.trigger_scan_urls_without_ai_results")
@log_function_call()
def trigger_scan_urls_without_ai_results(batch_size: int = 5):
    logger.info(
        f"定時任務啟動：開始查找未分析 (No AI Results) 的 URL，本次處理上限為 {batch_size} 個。"
    )
    urls_qs = (
        URLResult.objects.filter(content_fetch_status="SUCCESS_FETCHED")
        .exclude(ai_analysis__status__in=["COMPLETED", "RUNNING"])
        .exclude(status_code=404)
        .order_by("-id")[:batch_size]
    )
    target_urls = list(urls_qs.values_list("url", flat=True))
    if not target_urls:
        logger.info("沒有發現符合條件的待分析 URL，任務結束。")
        return
    try:
        response = requests.post(
            AI_ANALYZES_URL,
            json={"urls": target_urls},
            timeout=5,
        )

        if response.status_code == 202:
            logger.info(f"API 調用成功: {response.json()}")
        else:
            logger.error(f"API 調用失敗 [{response.status_code}]: {response.text}")
    except requests.RequestException as e:
        logger.error(f"連接 API 失敗: {e}")
    return


@shared_task(name="scheduler.tasks.trigger_scan_urls_without_nuclei_results")
@log_function_call()
def trigger_scan_urls_without_nuclei_results(batch_size: int = 5):
    logger.info(
        f"定時任務啟動：開始查找未分析 (No Nuclei Results) 的 URL，本次處理上限為 {batch_size} 個。"
    )
    urls_qs = (
        URLResult.objects.filter(content_fetch_status="SUCCESS_FETCHED")
        .exclude(nuclei_scans__isnull=False)
        .order_by("-id")[:batch_size]
    )
    target_urls = list(urls_qs.values_list("url", flat=True))
    if not target_urls:
        logger.info("沒有發現符合條件的待分析 URL，任務結束。")
        return
    try:
        response = requests.post(
            f"{NUCLEI_SCAN_URL}/urls",
            json={"urls": target_urls},
            timeout=5,
        )

        if response.status_code == 202:
            logger.info(f"API 調用成功: {response.json()}")
        else:
            logger.error(f"API 調用失敗 [{response.status_code}]: {response.text}")
    except requests.RequestException as e:
        logger.error(f"連接 API 失敗: {e}")
    return


@shared_task(name="scheduler.tasks.trigger_scan_subdomains_without_nuclei_results")
@log_function_call()
def trigger_scan_subdomains_without_nuclei_results(batch_size: int = 5):
    logger.info(
        f"定時任務啟動：開始查找未分析 (No Nuclei Results) 的子域名，本次處理上限為 {batch_size} 個。"
    )
    subdomains_qs = (
        Subdomain.objects.filter(is_active=True)
        .exclude(nuclei_scans__isnull=False)
        .order_by("-id")[:batch_size]
    )
    target_subdomains = list(subdomains_qs.values_list("name", flat=True))

    if not target_subdomains:
        logger.info("沒有發現符合條件的待分析子域名，任務結束。")
        return
    try:
        response = requests.post(
            f"{NUCLEI_SCAN_URL}/subdomains",
            json={"subdomains": target_subdomains},
            timeout=5,
        )

        if response.status_code == 202:
            logger.info(f"API 調用成功: {response.json()}")
        else:
            logger.error(f"API 調用失敗 [{response.status_code}]: {response.text}")

    except requests.RequestException as e:
        logger.error(f"連接 API 失敗: {e}")
    return


@shared_task(name="scheduler.tasks.trigger_scan_ips_without_nuclei_results")
@log_function_call()
def trigger_scan_ips_without_nuclei_results(batch_size: int = 10):
    """
    定期巡邏任務：
    找出指定數量(batch_size)的「未分析」IP。
    """
    logger.info(
        f"定時任務啟動：開始查找未分析 (No Nuclei Results) 的 IP，本次處理上限為 {batch_size} 個。"
    )
    ips_qs = IP.objects.filter(nuclei_scans__isnull=True).order_by("-id")[:batch_size]

    target_ip_strings = []
    for ip_obj in ips_qs:
        if ip_obj.ipv4:
            target_ip_strings.append(ip_obj.ipv4)
        elif ip_obj.ipv6:
            target_ip_strings.append(ip_obj.ipv6)

    # 去重 (防止一個 IP 既有 v4 又有 v6 導致邏輯重複，雖然目前模型結構不太可能)
    target_ip_strings = list(set(target_ip_strings))

    if not target_ip_strings:
        logger.info("沒有發現符合條件的待分析 IP，任務結束。")
        return

    logger.info(f"鎖定 {len(target_ip_strings)} 個 IP，正在發送 API 請求...")

    # 4. 發送 HTTP 請求
    try:
        response = requests.post(
            f"{NUCLEI_SCAN_URL}/ips",
            json={"ips": target_ip_strings},
            timeout=5,  # 務必設置超時，防止定時任務卡死
        )

        if response.status_code == 202:
            logger.info(f"API 調用成功: {response.json()}")
        else:
            logger.error(f"API 調用失敗 [{response.status_code}]: {response.text}")

    except requests.RequestException as e:
        logger.error(f"連接 API 失敗: {e}")
