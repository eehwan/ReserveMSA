from typing import Optional
from datetime import datetime
from pydantic import BaseModel

# 기본 스키마
class OrderBase(BaseModel):
    event_id: int
    seat_num: str


# API 요청/응답 스키마
class OrderRequest(OrderBase):
    """주문 생성/취소 API 요청 스키마"""
    pass


class OrderResponse(OrderBase):
    """주문 생성/조회 API 응답 스키마"""
    order_id: str
    expires_at: datetime

# DB 저장용 스키마
class OrderCreate(OrderBase):
    """주문 생성 시 DB 저장용 스키마"""
    order_id: str
    user_id: int
    price: int
    lock_key: str
    expires_at: datetime

class OrderUpdate(OrderBase):
    """주문 업데이트용 스키마"""
    payment_key: Optional[str] = None


class Order(OrderBase):
    """DB 모델 매핑용 스키마"""
    id: int
    order_id: str
    user_id: int
    price: int
    lock_key: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    payment_key: Optional[str] = None

    class Config:
        from_attributes = True
