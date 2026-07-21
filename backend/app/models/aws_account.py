from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.sql import func

from app.core.database import Base


class AWSAccount(Base):
    """
    Registered AWS account for multi-account
    optimization research.

    Permanent AWS credentials are NOT stored.
    Access is performed through STS AssumeRole.
    """

    __tablename__ = "aws_accounts"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    participant_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    account_alias = Column(
        String,
        nullable=True,
    )

    role_arn = Column(
        String,
        unique=True,
        nullable=False,
    )

    default_region = Column(
        String,
        nullable=False,
        default="us-east-1",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )