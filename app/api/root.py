from flask_restx import Resource

from app.extensions import api

ns = api.namespace('', description='Root endpoints')


@ns.route('/')
class HealthCheck(Resource):
    @ns.doc(security=[])
    def get(self):
        return {'status': 'ok', 'message': 'Deilify backend está en marcha'}
