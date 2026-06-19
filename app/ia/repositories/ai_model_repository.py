from sqlalchemy import select, update
from ...extensions import db_session
from ...models.prediccion_ia import AIModel

class AIModelRepository:
    @staticmethod
    def get_active_model() -> AIModel | None:
        stmt = select(AIModel).where(AIModel.is_active == True)
        return db_session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_id(model_id: int) -> AIModel | None:
        stmt = select(AIModel).where(AIModel.id == model_id)
        return db_session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_models() -> list[AIModel]:
        stmt = select(AIModel).order_by(AIModel.created_at.desc())
        return list(db_session.execute(stmt).scalars().all())

    @staticmethod
    def create(model: AIModel) -> AIModel:
        db_session.add(model)
        db_session.commit()
        return model

    @staticmethod
    def activate_model(model_id: int) -> bool:
        # First deactivate all models
        deactivate_stmt = update(AIModel).values(is_active=False)
        db_session.execute(deactivate_stmt)
        
        # Then activate the requested model
        activate_stmt = update(AIModel).where(AIModel.id == model_id).values(is_active=True)
        result = db_session.execute(activate_stmt)
        db_session.commit()
        return result.rowcount > 0
