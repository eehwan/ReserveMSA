from sqlalchemy import Column, Integer, String, DateTime, Enum
from datetime import datetime
import enum

from app.db.session import Base

class PaymentStatus(enum.Enum):
    PENDING = "pending"         # 결제 준비됨
    SUCCESS = "success"         # 결제 완료
    FAILED = "failed"           # 결제 실패
    CANCELLED = "cancelled"     # 결제 취소

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_key = Column(String, unique=True, index=True)  # 결제 키
    order_id = Column(String, index=True)  # 주문 ID
    amount = Column(Integer)  # 결제 금액
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # PG사 관련 정보
    imp_uid = Column(String, nullable=True)  # PG사 거래 ID
    merchant_uid = Column(String, nullable=True)  # 가맹점 거래 ID
    
    # 결제 완료/실패 정보
    approved_at = Column(DateTime, nullable=True)
    failure_reason = Column(String, nullable=True)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)