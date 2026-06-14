from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, ForeignKey
from ..extensions import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    identificacion: Mapped[str] = mapped_column(String(20), nullable=False)
    dias_plazo: Mapped[int] = mapped_column(Integer, default=30)
    limite_credito: Mapped[float] = mapped_column(Float, default=0.0)

    # Relaciones
    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="clientes")
    facturas: Mapped[list["Factura"]] = relationship("Factura", back_populates="cliente")
