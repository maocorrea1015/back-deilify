from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from datetime import datetime
from ..extensions import Base

class HistorialCobranza(Base):
    __tablename__ = "historial_cobranza"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    nota: Mapped[str] = mapped_column(Text, nullable=False)
    usuario_id: Mapped[int] = mapped_column(Integer, nullable=True) # ID del usuario que hizo el seguimiento
