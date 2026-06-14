from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime
from datetime import datetime
from ..extensions import Base

class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    nit: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    clientes: Mapped[list["Cliente"]] = relationship("Cliente", back_populates="empresa")
    facturas: Mapped[list["Factura"]] = relationship("Factura", back_populates="empresa")
