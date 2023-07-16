import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy_utils import URLType

from db.short_links_db_base import Base


class ShortLink(Base):
    """Модель укороченной ссылки"""

    __tablename__ = "short_link"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    is_active = Column(Boolean, default=True)
    original_link = Column(URLType, nullable=False)
    link_id = Column(String(10), index=True, nullable=False, unique=True)
    short_link = Column(URLType, nullable=False)
    usages_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    link_history = relationship('ShortLinkHistory', cascade="all, delete")


class ShortLinkHistory(Base):
    """История использования"""

    __tablename__ = "short_link_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    short_link_id = Column(
        UUID(as_uuid=True),
        ForeignKey('short_link.id', ondelete="CASCADE"),
        nullable=False,
    )
    client_ip = Column(String(60), nullable=False)
    use_at = Column(DateTime, index=True, default=datetime.utcnow)
