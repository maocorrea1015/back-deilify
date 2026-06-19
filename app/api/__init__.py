from ..extensions import api
from .root import ns as root_ns
from .cartera import ns as cartera_ns
from ..ia.routes.ai_routes import ns as ai_ns

api.add_namespace(cartera_ns, path='/cartera')
api.add_namespace(ai_ns, path='/api/v1/ai')

