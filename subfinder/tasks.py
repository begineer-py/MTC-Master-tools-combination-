# subdomain_finder/tasks.py

import logging
import subprocess
import json
from collections import defaultdict
from celery import shared_task
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from eventlet.greenpool import GreenPool  # 保持你的并发处理

# 使用正确的模型路径
from core.models.assets import Subdomain, IP, Seed
from core.models.scans_record_modles import SubfinderScan

logger = logging.getLogger(__name__)


# --- 任务链入口 ---
@shared_task(bind=True, ignore_result=True)
def start_subfinder(self, scan_id: int):
    scan = None
    try:
        scan = SubfinderScan.objects.select_related("which_seed").get(id=scan_id)
        seed = scan.which_seed
        logger.info(f"Subfinder 任務 (ID: {scan.id}) for Seed '{seed.value}' 已啟動。")

        scan.status = "RUNNING"
        scan.started_at = timezone.now()
        scan.save(update_fields=["status", "started_at"])

        # [逻辑保留] 保持你原来的命令行构造方式
        command = [
            "subfinder",
            "-d",
            seed.value,
            "-json",
            "-silent",
        ]
        # 如果你的 SubfinderScan 模型需要 timeout, 你应该加上
        # if scan.timeout:
        #    command.extend(["-timeout", str(scan.timeout)])

        logger.info(
            f"準備執行 Subfinder 命令 for Scan ID {scan.id}: {' '.join(command)}"
        )
        process = subprocess.run(command, capture_output=True, text=True, timeout=900)

        if process.returncode == 0:
            logger.info(f"Subfinder 掃描成功 for Scan ID {scan.id}。準備更新資產庫。")

            # [逻辑保留] 保持你原来的 JSON 解析和聚合逻辑
            current_subdomains_map = defaultdict(set)
            stdout_lines = process.stdout.strip().split("\n")
            for line in stdout_lines:
                try:
                    data = json.loads(line.strip())
                    host, source = data.get("host"), data.get("source")
                    if host and source:
                        current_subdomains_map[host].add(source)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"解析 JSON 行失敗，已跳過: {line} - 錯誤: {e}")

            # [逻辑保留] 保持你原来的集合对比逻辑
            current_subdomains_set = set(current_subdomains_map.keys())
            # [修正] 数据源从 Target 改为 Seed
            known_subdomains_qs = Subdomain.objects.filter(which_seed=seed)
            known_subdomains_map = {s.name: s for s in known_subdomains_qs}
            known_subdomains_set = set(known_subdomains_map.keys())

            new_subdomain_names = current_subdomains_set - known_subdomains_set
            reactivated_names = current_subdomains_set.intersection(
                known_subdomains_set
            )
            missing_names = known_subdomains_set - current_subdomains_set

            with transaction.atomic():
                # [修正] 创建资产时绑定到 Seed
                for name in new_subdomain_names:
                    sources_set = current_subdomains_map[name]
                    Subdomain.objects.create(
                        which_seed=seed,
                        name=name,
                        is_active=True,
                        sources_text=",".join(sorted(list(sources_set))),
                        last_scan_type="SubfinderScan",
                        last_scan_id=scan.id,
                    )

                # [逻辑保留] 保持你原来的详细更新逻辑
                for name in reactivated_names:
                    sub_obj = known_subdomains_map[name]
                    existing_sources = set(
                        sub_obj.sources_text.split(",") if sub_obj.sources_text else []
                    )
                    new_sources = current_subdomains_map[name]
                    combined_sources = existing_sources.union(new_sources)
                    new_sources_str = ",".join(sorted(list(combined_sources)))

                    update_fields_list = []
                    if not sub_obj.is_active:
                        sub_obj.is_active = True
                        update_fields_list.append("is_active")
                    if new_sources_str != sub_obj.sources_text:
                        sub_obj.sources_text = new_sources_str
                        update_fields_list.append("sources_text")

                    sub_obj.last_seen = timezone.now()
                    sub_obj.last_scan_type = "SubfinderScan"
                    sub_obj.last_scan_id = scan.id
                    update_fields_list.extend(
                        ["last_seen", "last_scan_type", "last_scan_id"]
                    )

                    if update_fields_list:
                        sub_obj.save(update_fields=update_fields_list)

                # [修正] 标记失联资产时绑定到 Seed
                if missing_names:
                    Subdomain.objects.filter(
                        which_seed=seed, name__in=missing_names, is_active=True
                    ).update(is_active=False)

            scan.added_count = len(new_subdomain_names)
            scan.status = "COMPLETED"
            logger.info(
                f"資產庫更新完成 for Seed '{seed.value}'. 新增: {len(new_subdomain_names)}, 更新: {len(reactivated_names)}, 失聯: {len(missing_names)}."
            )

            # 触下一个任务
            resolve_dns_for_seed.delay(seed_id=seed.id, subfinder_scan_id=scan.id)
        else:
            error_message = f"Subfinder command failed with exit code {process.returncode}. Stderr: {process.stderr[:1000]}"
            logger.error(error_message)
            scan.status = "FAILED"
            # scan.error_message = error_message
    except ObjectDoesNotExist:
        logger.error(f"找不到 SubfinderScan 紀錄，ID: {scan_id}")
        return
    except Exception as e:
        logger.exception(f"Subfinder 任務 ID {scan_id} 發生錯誤: {e}")
        if scan:
            scan.status = "FAILED"
            # scan.error_message = str(e)[:1000]
    finally:
        if scan:
            scan.completed_at = timezone.now()
            scan.save()
            logger.info(
                f"Subfinder 掃描任務 ID: {scan.id} 最終狀態已保存: {scan.status}"
            )


# --- 任务链第二步 ---
@shared_task(bind=True, ignore_result=True)
def resolve_dns_for_seed(self, seed_id: int, subfinder_scan_id: int):
    try:
        seed = Seed.objects.get(id=seed_id)
        logger.info(f"開始 DNS 解析 for Seed: '{seed.value}'")

        # [修正] 数据源从 Target 改为 Seed
        subdomains_qs = Subdomain.objects.filter(which_seed=seed, is_active=True)
        if not subdomains_qs.exists():
            logger.info("沒有活躍的子域名需要解析。")
            return

        logger.info(f"共篩選出 {subdomains_qs.count()} 個子域名進行解析。")
        subdomain_map = {sub.name: sub for sub in subdomains_qs}
        dnsx_input_data = "\n".join(subdomain_map.keys())

        command = ["dnsx", "-a", "-aaaa", "-cname", "-json", "-silent"]
        logger.info(f"執行 dnsx 命令: {' '.join(command)}")
        process = subprocess.run(
            command, input=dnsx_input_data, capture_output=True, text=True, timeout=600
        )

        if process.returncode != 0:
            logger.error(f"dnsx 執行失敗: {process.stderr}")
            # [逻辑保留] 保持你原来的失败后继续下一步的逻辑
            check_protection_for_seed.delay(
                seed_id=seed_id, subfinder_scan_id=subfinder_scan_id
            )
            return

        lines = process.stdout.strip().split("\n")
        updates_count = 0
        resolved_hosts = set()

        with transaction.atomic():
            for line in lines:
                try:
                    data = json.loads(line.strip())
                    host = data.get("host")
                    if host not in subdomain_map:
                        continue

                    resolved_hosts.add(host)
                    sub_obj = subdomain_map[host]

                    ipv4_list = data.get("a", [])
                    ipv6_list = data.get("aaaa", [])
                    cname_list = data.get("cname", [])

                    # [逻辑保留] 保持原来的解析状态处理
                    is_resolvable_now = bool(ipv4_list or ipv6_list or cname_list)
                    if not sub_obj.is_resolvable and is_resolvable_now:
                        sub_obj.is_resolvable = True
                        sub_obj.save(update_fields=["is_resolvable"])

                    # [修正] 关联 IP (注意：这里需要你决定 IP 归属于 Target 还是 Seed，当前模型是 ManyToManyField，可以归属多个 Seed)
                    if ipv4_list or ipv6_list:
                        for ip_str in ipv4_list:
                            ip_obj, _ = IP.objects.get_or_create(ipv4=ip_str)
                            sub_obj.ips.add(ip_obj)  # ManyToMany add
                        for ip_str in ipv6_list:
                            ip_obj, _ = IP.objects.get_or_create(ipv6=ip_str)
                            sub_obj.ips.add(ip_obj)

                    # [逻辑保留] 保持原来的 CNAME 和 dns_records 更新
                    cname_str = ",".join(cname_list) if cname_list else ""
                    updated_fields = []
                    if sub_obj.cname != cname_str:
                        sub_obj.cname = cname_str
                        updated_fields.append("cname")
                    if sub_obj.dns_records != data:
                        sub_obj.dns_records = data
                        updated_fields.append("dns_records")

                    sub_obj.last_scan_type = "DnsxScan"
                    sub_obj.last_scan_id = subfinder_scan_id
                    updated_fields.extend(["last_scan_type", "last_scan_id"])

                    if updated_fields:
                        sub_obj.save(update_fields=updated_fields)
                        updates_count += 1
                except json.JSONDecodeError:
                    pass

        # [逻辑保留] 保持原来的处理未解析域名的逻辑
        unresolved_hosts = set(subdomain_map.keys()) - resolved_hosts
        if unresolved_hosts:
            logger.warning(
                f"發現 {len(unresolved_hosts)} 個無法解析的子域名，將其標記。"
            )
            Subdomain.objects.filter(
                which_seed=seed, name__in=unresolved_hosts, is_resolvable=True
            ).update(is_resolvable=False)

        logger.info(
            f"DNS 解析完成。更新了 {updates_count} 個子域名，標記了 {len(unresolved_hosts)} 個為不可解析。"
        )
    except Exception as e:
        logger.exception(f"DNS 解析任務 for Seed ID {seed_id} 發生錯誤: {e}")
    finally:
        logger.info(f"觸發 CDN/WAF 檢測任務 for Seed ID: {seed_id}")
        check_protection_for_seed.delay(
            seed_id=seed_id, subfinder_scan_id=subfinder_scan_id
        )


# --- 任务链第三步 ---
@shared_task(bind=True, ignore_result=True)
def check_protection_for_seed(
    self,
    seed_id: int,
    subfinder_scan_id: int,
    chunk_size: int = 100,
    greenpool_size: int = 20,
):
    try:
        seed = Seed.objects.get(id=seed_id)
        logger.info(f"開始 CDN/WAF 檢測 for Seed: '{seed.value}'")

        # [修正] 数据源从 Target 改为 Seed
        subdomains_to_check = Subdomain.objects.filter(
            which_seed=seed, is_active=True, is_resolvable=True
        )
        if not subdomains_to_check.exists():
            logger.info("沒有需要檢測 CDN/WAF 的子域名。")
            return

        # [逻辑保留] 保持你原来的并发分块处理
        subdomain_map = {sub.name: sub for sub in subdomains_to_check}
        all_names = list(subdomain_map.keys())
        chunks = [
            all_names[i : i + chunk_size] for i in range(0, len(all_names), chunk_size)
        ]

        command = [
            "cdncheck",
            "-jsonl",
            "-silent",
        ]  # 你的原始命令没有 -i -，它是从 stdin 读的
        logger.info(f"将 {len(all_names)} 个子域名分成 {len(chunks)} 批进行并发检测。")

        def run_cdncheck_on_chunk(chunk):
            input_data = "\n".join(chunk)
            try:
                process = subprocess.run(
                    command,
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if process.returncode == 0:
                    return [line for line in process.stdout.strip().split("\n") if line]
                else:
                    logger.error(f"cdncheck 批次執行失敗: {process.stderr}")
                    return []
            except Exception as e:
                logger.error(f"cdncheck 批次執行異常: {e}")
                return []

        pool = GreenPool(size=greenpool_size)
        all_lines = []
        for lines_chunk in pool.imap(run_cdncheck_on_chunk, chunks):
            all_lines.extend(lines_chunk)

        updates_count = 0
        with transaction.atomic():
            for line in all_lines:
                try:
                    data = json.loads(line)
                    host = data.get("input")
                    if host in subdomain_map:
                        sub_obj = subdomain_map[host]
                        is_cdn = data.get("cdn", False)
                        is_waf = data.get("waf", False)
                        cdn_name = data.get("cdn_name")
                        waf_name = data.get("waf_name")

                        # [逻辑保留] 保持原来的只在变化时更新的逻辑
                        if (
                            sub_obj.is_cdn != is_cdn
                            or sub_obj.is_waf != is_waf
                            or sub_obj.cdn_name != cdn_name
                            or sub_obj.waf_name != waf_name
                        ):

                            sub_obj.is_cdn, sub_obj.is_waf = is_cdn, is_waf
                            sub_obj.cdn_name, sub_obj.waf_name = cdn_name, waf_name
                            sub_obj.last_scan_type = "CdnCheckScan"
                            sub_obj.last_scan_id = subfinder_scan_id

                            sub_obj.save(
                                update_fields=[
                                    "is_cdn",
                                    "is_waf",
                                    "cdn_name",
                                    "waf_name",
                                    "last_scan_type",
                                    "last_scan_id",
                                ]
                            )
                            updates_count += 1
                except (json.JSONDecodeError, KeyError):
                    pass
        logger.info(f"CDN/WAF 檢測完成。共更新 {updates_count} 個子域名的信息。")
    except Exception as e:
        logger.exception(f"CDN/WAF 檢測任務 for Seed ID {seed_id} 失敗: {e}")
