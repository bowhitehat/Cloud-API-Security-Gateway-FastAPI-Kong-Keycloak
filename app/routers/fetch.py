import ipaddress
import logging
import socket
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.models.user import User
from app.services.deps import get_current_user

router = APIRouter(prefix="/fetch", tags=["Fetch (SSRF Demo)"])
security_logger = logging.getLogger("api.security")


@router.get("/vulnerable")
async def fetch_url_vulnerable(url: str, current_user: User = Depends(get_current_user)):
    """
    Endpoint cố tình bị lỗi SSRF (Server-Side Request Forgery).
    Không kiểm tra URL đầu vào, cho phép attacker truy cập các dịch vụ nội bộ (ví dụ: http://localhost:5432).
    """
    security_logger.warning(
        "ssrf_vulnerable_request",
        extra={
            "event": "ssrf_vulnerable_request",
            "username": current_user.username,
            "target_url": url,
        },
    )
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
            return {"status": response.status_code, "content": response.text[:500]}
    except Exception as e:
        return {"error": str(e)}


def is_private_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_reserved
    except ValueError:
        return False


def resolve_hostname(hostname: str) -> str:
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return ""


@router.get("/secure")
async def fetch_url_secure(url: str, current_user: User = Depends(get_current_user)):
    """
    Endpoint đã fix SSRF bằng cách:
    1. Phân tích URL.
    2. Phân giải DNS ra IP.
    3. Chặn tất cả các IP thuộc dải mạng nội bộ (private/loopback).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        raise HTTPException(status_code=400, detail="Only HTTP/HTTPS allowed")

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="Invalid hostname")

    # Phân giải DNS để lấy IP thật
    ip_address = resolve_hostname(hostname)
    if not ip_address:
        raise HTTPException(status_code=400, detail="Cannot resolve hostname")

    # Kiểm tra IP có phải mạng nội bộ không
    if is_private_ip(ip_address) or hostname in ["localhost", "127.0.0.1"]:
        security_logger.warning(
            "ssrf_blocked",
            extra={
                "event": "ssrf_blocked",
                "username": current_user.username,
                "target_url": url,
                "resolved_ip": ip_address,
            },
        )
        raise HTTPException(status_code=403, detail="Access to private networks is forbidden")

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
            return {"status": response.status_code, "content": response.text[:500]}
    except Exception as e:
        return {"error": str(e)}
