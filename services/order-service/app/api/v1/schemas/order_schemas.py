from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.db.models import OrderStatus

class OrderBase(BaseModel):
    order_id: str
    user_id: int
    event_id: int
    seat_num: str
    price: int

class OrderCreate(BaseModel):
    order_id: str
    user_id: int
    event_id: int
    seat_num: str
    price: int
    lock_key: str
    expires_at: datetime

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    payment_key: Optional[str] = None

class Order(OrderBase):
    id: int
    status: OrderStatus
    lock_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    payment_key: Optional[str] = None

    class Config:
        from_attributes = True

#####

class OrderRequest(BaseModel):
    event_id: int
    seat_num: str

class OrderResponse(BaseModel):
    order_id: str
    event_id: int
    seat_num: str
    expires_at: datetime
    status: str

class OrderStatusResponse(BaseModel):
    order_id: str
    status: str
    event_id: Optional[int] = None
    seat_num: Optional[str] = None
    expires_at: Optional[datetime] = None
