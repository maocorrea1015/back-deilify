import logging
import joblib
import pandas as pd
from datetime import datetime
from sqlalchemy import select

from ..ml.features import extract_client_features, FEATURE_COLUMNS
from ..repositories.ai_model_repository import AIModelRepository
from ..repositories.prediction_repository import PredictionRepository
from ...models.prediccion_ia import PredictionLog
from ...models.cliente import Cliente
from ...extensions import db_session

logger = logging.getLogger(__name__)

class PredictionService:
    @staticmethod
    def get_risk_level_and_recommendation(score: int) -> tuple[str, str]:
        """
        Maps a risk score (0-100) to a risk level and recommendation.
        """
        if score <= 20:
            return "MUY BAJO", "Sin observaciones / Aprobación estándar"
        elif score <= 40:
            return "BAJO", "Monitoreo estándar"
        elif score <= 60:
            return "MEDIO", "Monitoreo periódico"
        elif score <= 80:
            return "ALTO", "Seguimiento preventivo"
        else:
            return "MUY ALTO", "Acción de cobro inmediata / Suspensión de crédito"

    @staticmethod
    def predict_client_risk(client_id: int) -> dict:
        """
        Predicts credit risk (probability of default/late payment) for a client,
        calculates a score 0-100, maps it to a risk level and recommendation,
        persists the prediction log, and returns the prediction result.
        """
        logger.info(f"Iniciando predicción de riesgo para el cliente ID: {client_id}")
        
        # 1. Get client
        cliente = db_session.execute(select(Cliente).where(Cliente.id == client_id)).scalar_one_or_none()
        if not cliente:
            err_msg = f"Cliente con ID {client_id} no encontrado."
            logger.error(err_msg)
            raise ValueError(err_msg)
            
        # 2. Get active model
        active_model = AIModelRepository.get_active_model()
        if not active_model:
            err_msg = "No hay un modelo de IA activo para realizar la predicción. Por favor, entrene y active un modelo primero."
            logger.error(err_msg)
            raise ValueError(err_msg)
            
        # 3. Load model from disk
        try:
            clf = joblib.load(active_model.model_path)
        except Exception as e:
            err_msg = f"Error al cargar el archivo de modelo en {active_model.model_path}: {str(e)}"
            logger.error(err_msg)
            raise ValueError(err_msg)
            
        # 4. Extract features
        features_dict = extract_client_features(cliente)
        
        # Prepare input for classifier
        # Convert dictionary to DataFrame with column order matching FEATURE_COLUMNS
        features_df = pd.DataFrame([features_dict])[FEATURE_COLUMNS]
        
        # 5. Predict
        try:
            prob = float(clf.predict_proba(features_df)[0][1])
            pred_class = int(clf.predict(features_df)[0])
        except Exception as e:
            err_msg = f"Error durante la inferencia con el modelo: {str(e)}"
            logger.error(err_msg)
            raise ValueError(err_msg)
            
        risk_score = round(prob * 100)
        risk_level, recommendation = PredictionService.get_risk_level_and_recommendation(risk_score)
        
        # 6. Save log in DB
        prediction_log = PredictionLog(
            client_id=client_id,
            model_id=active_model.id,
            prediction=float(pred_class),
            risk_score=risk_score,
            probability=prob
        )
        PredictionRepository.create(prediction_log)
        
        logger.info(f"Predicción completada para cliente ID {client_id}: score {risk_score}, nivel {risk_level}")
        
        return {
            "client_id": client_id,
            "risk_score": risk_score,
            "probability": prob,
            "risk_level": risk_level,
            "recommendation": recommendation
        }
