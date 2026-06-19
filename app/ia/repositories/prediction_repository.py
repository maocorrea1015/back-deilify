from sqlalchemy import select, func
from ...extensions import db_session
from ...models.prediccion_ia import PredictionLog
from ...models.cliente import Cliente

class PredictionRepository:
    @staticmethod
    def create(log: PredictionLog) -> PredictionLog:
        db_session.add(log)
        db_session.commit()
        return log

    @staticmethod
    def list_predictions(limit: int, offset: int, empresa_id: int = None) -> list[PredictionLog]:
        stmt = select(PredictionLog)
        if empresa_id is not None:
            stmt = stmt.join(Cliente).where(Cliente.empresa_id == empresa_id)
        stmt = stmt.order_by(PredictionLog.created_at.desc()).limit(limit).offset(offset)
        return list(db_session.execute(stmt).scalars().all())

    @staticmethod
    def count_predictions(empresa_id: int = None) -> int:
        stmt = select(func.count(PredictionLog.id))
        if empresa_id is not None:
            stmt = stmt.join(Cliente).where(Cliente.empresa_id == empresa_id)
        return db_session.execute(stmt).scalar() or 0
