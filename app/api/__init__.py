from ..extensions import api
from .root import ns as root_ns
from .cartera import ns as cartera_ns

api.add_namespace(cartera_ns, path='/cartera')
