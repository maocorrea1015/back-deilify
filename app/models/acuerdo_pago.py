from datetime import datetime
import enum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import Base


class EstadoAcuerdoPago(enum.Enum):
	ACTIVO = "ACTIVO"
	CUMPLIDO = "CUMPLIDO"
	INCUMPLIDO = "INCUMPLIDO"
	CANCELADO = "CANCELADO"


class AcuerdoPago(Base):
	__tablename__ = "acuerdos_pago"

	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False)
	cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
	factura_id: Mapped[int] = mapped_column(ForeignKey("facturas.id"), nullable=False)
	monto_acordado: Mapped[float] = mapped_column(Float, nullable=False)
	numero_cuotas: Mapped[int] = mapped_column(Integer, nullable=False)
	valor_cuota: Mapped[float] = mapped_column(Float, nullable=False)
	fecha_inicio: Mapped[datetime] = mapped_column(DateTime, nullable=False)
	fecha_fin: Mapped[datetime] = mapped_column(DateTime, nullable=False)
	estado: Mapped[EstadoAcuerdoPago] = mapped_column(
		Enum(EstadoAcuerdoPago), default=EstadoAcuerdoPago.ACTIVO, nullable=False
	)
	observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

	factura: Mapped["Factura"] = relationship("Factura")
