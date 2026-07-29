from ..extensions import api
from .root import ns as root_ns
from .cartera import ns as cartera_ns
from ..ia.routes.ai_routes import ns as ai_ns
from .auth import ns as auth_ns
from .usuarios import ns as usuarios_ns
from .clientes import ns as clientes_ns

api.add_namespace(cartera_ns, path='/cartera')
api.add_namespace(ai_ns, path='/api/v1/ai')
api.add_namespace(auth_ns, path='/auth')
api.add_namespace(usuarios_ns, path='/usuarios')
api.add_namespace(clientes_ns, path='/clientes')



