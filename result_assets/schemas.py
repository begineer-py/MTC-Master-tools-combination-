from ninja import Schema


class get_ip_by_subdomains(Schema):
    target_id: int
    target_domain: str
    count: int
    results: list
