from sqlalchemy import Column, String, DateTime
from datetime import datetime, timezone
from database import Base

class URL(Base):
    __tablename__ = "urls"
    
    code = Column(String, primary_key=True, index=True)
    destination = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    