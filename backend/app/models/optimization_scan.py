from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OptimizationScan(Base):
    __tablename__ = "optimization_scans"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    instance_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    instance_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    average_cpu_24h: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    optimization_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    estimated_monthly_cost_usd: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    potential_monthly_savings_usd: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    estimated_energy_kwh_monthly: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    estimated_carbon_kg_monthly: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    potential_carbon_reduction_kg: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )