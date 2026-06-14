from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Enum
from datetime import datetime
import enum
from ..extensions import Base

class EstadoFactura(enum.Enum):
    PAGADA = "PAGADA"
    PENDIENTE = "PENDIENTE"
    VENCIDA = "VENCIDA"

class Factura(Base):
    __tablename__ = "facturas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    numero: Mapped[str] = mapped_column(String(50), nullable=False)
    fecha_emision: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fecha_vencimiento: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    monto_total: Mapped[float] = mapped_column(Float, nullable=False)
    saldo_pendiente: Mapped[float] = mapped_column(Float, nullable=False)
    estado: Mapped[EstadoFactura] = mapped_column(Enum(EstadoFactura), default=EstadoFactura.PENDIENTE)

    # Relaciones
    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="facturas")
    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="facturas")
    recaudos: Mapped[list["Pago"]] = relationship("Pago", back_populates="factura")
