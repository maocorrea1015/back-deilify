from flask_restx import Namespace

ns = Namespace('ai', description='Módulo de Inteligencia Artificial para Riesgo Crediticio')

# Import controllers to register the routes on the namespace
from ..controllers.ai_controller import (
    TrainResource,
    ModelListResource,
    ModelActivateResource,
    PredictResource,
    PredictionHistoryResource
)
