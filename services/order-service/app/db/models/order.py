from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.db.session import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)  # 예약번호
    user_id = Column(Integer, index=True)
    event_id = Column(Integer, index=True)
    seat_num = Column(String)
    price = Column(Integer)  # 좌석 가격
    lock_key = Column(String, nullable=True)  # Redis lock key
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)  # 주문 만료 시간
    payment_key = Column(String, nullable=True)  # 결제 키 (결제 완료 시)