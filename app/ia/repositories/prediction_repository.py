from sqlalchemy import select, func
from ...extensions import db_session
from ...models.prediccion_ia import PredictionLog

class PredictionRepository:
    @staticmethod
    def create(log: PredictionLog) -> PredictionLog:
        db_session.add(log)
        db_session.commit()
        return log

    @staticmethod
    def list_predictions(limit: int, offset: int) -> list[PredictionLog]:
        stmt = select(PredictionLog).order_by(PredictionLog.created_at.desc()).limit(limit).offset(offset)
        return list(db_session.execute(stmt).scalars().all())

    @staticmethod
    def count_predictions() -> int:
        stmt = select(func.count(PredictionLog.id))
        return db_session.execute(stmt).scalar() or 0
