"""
Modèles ORM simplifiés - Table de test uniquement.
"""
from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID

from .database import Base


class TestTable(Base):
    """
    Table de test simple.
    """
    __tablename__ = "test_table"
    
    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        nullable=False
    )
    name = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False
    )
