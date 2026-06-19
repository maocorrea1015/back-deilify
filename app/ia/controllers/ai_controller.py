import logging
from flask import request
from flask_restx import Resource, fields, reqparse
from flask_jwt_extended import jwt_required, get_jwt
from functools import wraps

from ..routes.ai_routes import ns
from ..services.model_training_service import ModelTrainingService
from ..services.prediction_service import PredictionService
from ..repositories.ai_model_repository import AIModelRepository
from ..repositories.prediction_repository import PredictionRepository
from ..schemas.ai_schemas import AIModelSchema, PredictionLogSchema

logger = logging.getLogger(__name__)

def admin_required():
    """
    Decorator to enforce ADMIN role based on the role claim inside the JWT.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                claims = get_jwt()
                if claims.get("role") != "ADMIN":
                    logger.warning("Acceso denegado: Se requiere rol de ADMINISTRADOR.")
                    return {"error": "Acceso denegado. Se requiere rol de ADMINISTRADOR."}, 403
            except Exception as e:
                logger.error(f"Error al verificar el rol JWT: {str(e)}")
                return {"error": "Token JWT inválido o no configurado para verificar roles."}, 401
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# Swagger models documentation
model_metric_fields = ns.model('ModelMetrics', {
    'id': fields.Integer(readOnly=True, description='ID del modelo en la base de datos'),
    'algorithm': fields.String(readOnly=True, description='Nombre del algoritmo (RandomForest, XGBoost)'),
    'accuracy': fields.Float(readOnly=True, description='Exactitud del modelo'),
    'precision': fields.Float(readOnly=True, description='Precisión del modelo'),
    'recall': fields.Float(readOnly=True, description='Sensibilidad / Recall del modelo'),
    'f1_score': fields.Float(readOnly=True, description='Puntaje F1 del modelo'),
    'roc_auc': fields.Float(readOnly=True, description='ROC AUC score del modelo'),
    'is_active': fields.Boolean(readOnly=True, description='Indica si el modelo está activo para predicciones')
})

train_response_fields = ns.model('TrainResponse', {
    'version': fields.String(readOnly=True, description='Versión única del lote de entrenamiento'),
    'best_model_id': fields.Integer(readOnly=True, description='ID del mejor modelo seleccionado y activado'),
    'best_algorithm': fields.String(readOnly=True, description='Algoritmo del mejor modelo'),
    'models': fields.List(fields.Nested(model_metric_fields), description='Métricas de todos los modelos entrenados')
})

predict_response_fields = ns.model('PredictResponse', {
    'client_id': fields.Integer(readOnly=True, description='ID del cliente evaluado'),
    'risk_score': fields.Integer(readOnly=True, description='Puntaje de riesgo de mora (0 a 100)'),
    'probability': fields.Float(readOnly=True, description='Probabilidad estimada de mora (0.0 a 1.0)'),
    'risk_level': fields.String(readOnly=True, description='Nivel de riesgo (MUY BAJO, BAJO, MEDIO, ALTO, MUY ALTO)'),
    'recommendation': fields.String(readOnly=True, description='Acción recomendada basada en el nivel de riesgo')
})

# Request parser for pagination
pagination_parser = reqparse.RequestParser()
pagination_parser.add_argument('page', type=int, default=1, help='Número de página (1-indexed)')
pagination_parser.add_argument('per_page', type=int, default=10, help='Número de elementos por página')


@ns.route('/train')
class TrainResource(Resource):
    @jwt_required()
    @admin_required()
    @ns.doc('train_models', security='apikey')
    @ns.response(200, 'Modelos entrenados y evaluados con éxito', train_response_fields)
    @ns.response(400, 'Datos insuficientes o error en el proceso')
    @ns.response(403, 'Acceso denegado (Rol ADMIN requerido)')
    def post(self):
        """
        Entrena modelos RandomForest y XGBoost, evalúa métricas y activa el mejor.
        """
        try:
            result = ModelTrainingService.train_models()
            return result, 200
        except ValueError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            logger.exception("Error durante el proceso de entrenamiento de modelos.")
            return {"error": f"Error inesperado durante el entrenamiento: {str(e)}"}, 500


@ns.route('/models')
class ModelListResource(Resource):
    @jwt_required()
    @ns.doc('list_models', security='apikey')
    @ns.response(200, 'Lista de modelos registrados')
    def get(self):
        """
        Obtiene la lista de todos los modelos entrenados y registrados en el sistema.
        """
        try:
            models = AIModelRepository.list_models()
            schema = AIModelSchema(many=True)
            return schema.dump(models), 200
        except Exception as e:
            logger.exception("Error al listar los modelos registrados.")
            return {"error": f"Error al listar los modelos: {str(e)}"}, 500


@ns.route('/models/<int:id>/activate')
@ns.param('id', 'ID del modelo a activar')
class ModelActivateResource(Resource):
    @jwt_required()
    @admin_required()
    @ns.doc('activate_model', security='apikey')
    @ns.response(200, 'Modelo activado correctamente')
    @ns.response(404, 'Modelo no encontrado')
    @ns.response(403, 'Acceso denegado (Rol ADMIN requerido)')
    def put(self, id):
        """
        Activa un modelo de IA específico y desactiva todos los demás.
        """
        try:
            model = AIModelRepository.get_by_id(id)
            if not model:
                return {"error": f"Modelo con ID {id} no encontrado."}, 404
                
            success = AIModelRepository.activate_model(id)
            if success:
                logger.info(f"Modelo ID {id} ({model.algorithm}) activado manualmente por administrador.")
                return {
                    "message": f"Modelo {id} ({model.algorithm}) activado correctamente y configurado como activo."
                }, 200
            return {"error": "No se pudo activar el modelo en la base de datos."}, 500
        except Exception as e:
            logger.exception("Error al intentar activar el modelo.")
            return {"error": f"Error interno en la activación del modelo: {str(e)}"}, 500


@ns.route('/predict/<int:client_id>')
@ns.param('client_id', 'ID del cliente a evaluar')
class PredictResource(Resource):
    @jwt_required()
    @ns.doc('predict_client', security='apikey')
    @ns.response(200, 'Predicción de riesgo calculada exitosamente', predict_response_fields)
    @ns.response(400, 'Modelo no cargado o error en features')
    @ns.response(404, 'Cliente no encontrado')
    def post(self, client_id):
        """
        Calcula la probabilidad e indicador de riesgo de mora para un cliente usando el modelo activo.
        """
        try:
            result = PredictionService.predict_client_risk(client_id)
            return result, 200
        except ValueError as e:
            msg = str(e)
            status_code = 404 if "no encontrado" in msg else 400
            return {"error": msg}, status_code
        except Exception as e:
            logger.exception(f"Error al calcular predicción de riesgo para cliente {client_id}.")
            return {"error": f"Error interno en el cálculo de riesgo: {str(e)}"}, 500


@ns.route('/predictions')
class PredictionHistoryResource(Resource):
    @jwt_required()
    @ns.doc('list_predictions', security='apikey')
    @ns.expect(pagination_parser)
    @ns.response(200, 'Historial de predicciones con paginación')
    def get(self):
        """
        Obtiene el historial de predicciones guardadas con soporte para paginación.
        """
        try:
            args = pagination_parser.parse_args()
            page = args.get('page', 1)
            per_page = args.get('per_page', 10)
            
            offset = (page - 1) * per_page
            predictions = PredictionRepository.list_predictions(limit=per_page, offset=offset)
            total = PredictionRepository.count_predictions()
            
            schema = PredictionLogSchema(many=True)
            return {
                "total": total,
                "page": page,
                "per_page": per_page,
                "predictions": schema.dump(predictions)
            }, 200
        except Exception as e:
            logger.exception("Error al listar el historial de predicciones.")
            return {"error": f"Error al obtener historial de predicciones: {str(e)}"}, 500
