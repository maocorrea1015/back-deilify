from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from ...services.cartera_service import CarteraService
from ...schemas.cartera import PagoSchema, FacturaSchema

ns = Namespace('cartera', description='Operaciones de Cartera y Cobranzas')

# Modelos para Swagger (Flask-RESTX)
pago_model = ns.model('Pago', {
    'factura_id': fields.Integer(required=True),
    'monto': fields.Float(required=True),
    'metodo_pago': fields.String(required=True),
    'transaccion_id': fields.String()
})

@ns.route('/dashboard')
class CarteraDashboard(Resource):
    @jwt_required()
    @ns.doc('obtener_metrics')
    def get(self):
        """Retorna métricas clave de cartera (DSO, Antigüedad, etc.)"""
        empresa_id = get_jwt_identity() # Asumimos que la identidad es el empresa_id
        return CarteraService.obtener_dashboard(empresa_id), 200

@ns.route('/facturas')
class FacturasSinc(Resource):
    @jwt_required()
    @ns.expect([fields.Raw])
    def post(self):
        """Cargar/Sincronizar facturas nuevas"""
        empresa_id = get_jwt_identity()
        data = request.json
        CarteraService.sincronizar_facturas(empresa_id, data)
        return {"message": "Facturas sincronizadas correctamente"}, 201

@ns.route('/recaudos')
class RegistrarRecaudo(Resource):
    @jwt_required()
    @ns.expect(pago_model)
    def post(self):
        """Registrar un pago/recaudo"""
        empresa_id = get_jwt_identity()
        schema = PagoSchema()
        errors = schema.validate(request.json)
        if errors:
            return errors, 400
        
        try:
            pago = CarteraService.registrar_pago(empresa_id, request.json)
            return {"message": "Pago registrado", "pago_id": pago.id}, 201
        except ValueError as e:
            return {"error": str(e)}, 404

@ns.route('/clientes/<int:id>/estado-cuenta')
@ns.param('id', 'ID del cliente')
class EstadoCuenta(Resource):
    @jwt_required()
    def get(self, id):
        """Reporte de estado de cuenta para un cliente"""
        empresa_id = get_jwt_identity()
        reporte = CarteraService.estado_cuenta_cliente(empresa_id, id)
        return reporte, 200
