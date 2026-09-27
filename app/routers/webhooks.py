import hashlib
import hmac
import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter(prefix="/webhooks", tags=["Webhooks (Forgery Demo)"])
security_logger = logging.getLogger("api.security")

# Secret key dùng để ký Webhook (trong thực tế sẽ lấy từ biến môi trường KMS)
WEBHOOK_SECRET = "super-secret-webhook-key"


@router.post("/vulnerable")
async def receive_webhook_vulnerable(payload: dict[str, Any]):
    """
    Endpoint cố tình bị lỗi Webhook Forgery.
    Không kiểm tra chữ ký (signature) từ bên gửi. Ai cũng có thể gọi API này
    và giả mạo dữ liệu (ví dụ: báo cáo đơn hàng đã được thanh toán).
    """
    security_logger.warning(
        "webhook_vulnerable_received",
        extra={
            "event": "webhook_vulnerable_received",
            "payload": payload,
        },
    )
    # Xử lý logic giả lập
    return {"message": "Webhook processed successfully (Vulnerable)", "data": payload}


@router.post("/secure")
async def receive_webhook_secure(
    request: Request,
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256")
):
    """
    Endpoint đã fix Webhook Forgery.
    Kiểm tra header X-Hub-Signature-256 xem có khớp với mã băm HMAC SHA256 của body không.
    """
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256 header")

    body = await request.body()
    
    # Tính toán chữ ký hợp lệ
    expected_mac = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).hexdigest()
    
    expected_signature = f"sha256={expected_mac}"

    # So sánh chữ ký an toàn (tránh timing attack)
    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        security_logger.warning(
            "webhook_forgery_blocked",
            extra={
                "event": "webhook_forgery_blocked",
                "provided_signature": x_hub_signature_256,
            },
        )
        raise HTTPException(status_code=403, detail="Invalid signature")

    import json
    payload = json.loads(body)

    return {"message": "Webhook verified and processed securely", "data": payload}
