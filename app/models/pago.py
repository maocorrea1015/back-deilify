from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from datetime import datetime
from ..extensions import Base

class Pago(Base):
    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False)
    factura_id: Mapped[int] = mapped_column(ForeignKey("facturas.id"), nullable=False)
    monto: Mapped[float] = mapped_column(Float, nullable=False)
    fecha_pago: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metodo_pago: Mapped[str] = mapped_column(String(50), nullable=False)
    transaccion_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)

    # Relaciones
    factura: Mapped["Factura"] = relationship("Factura", back_populates="recaudos")
