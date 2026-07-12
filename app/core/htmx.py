from fastapi import Request


def is_htmx_request(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"
