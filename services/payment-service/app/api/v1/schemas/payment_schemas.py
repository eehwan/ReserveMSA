from pydantic import BaseModel
from typing import Optional

# Webhook 관련
class PaymentWebhookRequest(BaseModel):
    payment_key: str
    order_id: str
    imp_uid: str  # PG사 거래 ID
    merchant_uid: str  # 가맹점 거래 ID
    status: str  # "SUCCESS" or "FAILED"
    amount: int
    approved_at: Optional[str] = None
    failure_reason: Optional[str] = None

class PaymentWebhookResponse(BaseModel):
    result: str  # "success" or "error"
    message: str

# 결제 상태 조회 관련
class PaymentStatusRequest(BaseModel):
    payment_key: str

class PaymentStatusResponse(BaseModel):
    payment_key: str
    order_id: str
    amount: int
    status: str  # "pending", "success", "failed", "cancelled"
    approved_at: Optional[str] = None
    failure_reason: Optional[str] = None