from flask import request
from flask_restx import Namespace, Resource, fields, reqparse
from flask_jwt_extended import jwt_required
from ...services.cartera_service import CarteraService
from ...schemas.cartera import (
    AcuerdoPagoSchema,
    AcuerdoPagoResponseSchema,
    PagoSchema,
    FacturaSchema,
)
from ...middleware.tenant import get_empresa_id_from_jwt

ns = Namespace('cartera', description='Operaciones de Cartera y Cobranzas', security='apikey')

# Modelos para Swagger (Flask-RESTX)
pago_model = ns.model('Pago', {
    'factura_id': fields.Integer(required=True),
    'monto': fields.Float(required=True),
    'metodo_pago': fields.String(required=True),
    'transaccion_id': fields.String()
})

pago_response_model = ns.model('PagoHistorico', {
    'id': fields.Integer,
    'factura_id': fields.Integer,
    'factura_numero': fields.String,
    'cliente_id': fields.Integer,
    'cliente_nombre': fields.String,
    'monto': fields.Float,
    'fecha_pago': fields.String,
    'metodo_pago': fields.String,
    'transaccion_id': fields.String
})

facturas_query_parser = reqparse.RequestParser()
facturas_query_parser.add_argument('cliente_id', type=int, help='Filtrar por ID de cliente')
facturas_query_parser.add_argument(
    'estado',
    type=str,
    choices=('PENDIENTE', 'PAGADA', 'VENCIDA', 'VIGENTE'),
    help='Filtrar por estado: PENDIENTE, PAGADA, VENCIDA o VIGENTE'
)

factura_model = ns.model('Factura', {
    'id': fields.Integer,
    'numero': fields.String,
    'cliente_id': fields.Integer,
    'cliente_nombre': fields.String,
    'fecha_emision': fields.DateTime,
    'fecha_vencimiento': fields.DateTime,
    'monto_total': fields.Float,
    'saldo_pendiente': fields.Float,
    'estado': fields.String,
    'dias_mora': fields.Integer
})

acuerdo_pago_model = ns.model('AcuerdoPago', {
    'id': fields.Integer,
    'empresa_id': fields.Integer,
    'cliente_id': fields.Integer,
    'factura_id': fields.Integer,
    'factura_numero': fields.String,
    'cliente_nombre': fields.String,
    'monto_acordado': fields.Float,
    'numero_cuotas': fields.Integer,
    'valor_cuota': fields.Float,
    'fecha_inicio': fields.String,
    'fecha_fin': fields.String,
    'estado': fields.String,
    'observaciones': fields.String,
    'created_at': fields.String
})

acuerdos_query_parser = reqparse.RequestParser()
acuerdos_query_parser.add_argument('cliente_id', type=int, help='Filtrar por ID de cliente')
acuerdos_query_parser.add_argument(
    'estado',
    type=str,
    choices=('ACTIVO', 'CUMPLIDO', 'INCUMPLIDO', 'CANCELADO'),
    help='Filtrar por estado del acuerdo'
)

@ns.route('/dashboard')
class CarteraDashboard(Resource):
    @jwt_required()
    @ns.doc('obtener_metrics')
    def get(self):
        """Retorna métricas clave de cartera (DSO, Antigüedad, etc.)"""
        empresa_id = get_empresa_id_from_jwt()
        return CarteraService.obtener_dashboard(empresa_id), 200

@ns.route('/facturas')
class FacturasSinc(Resource):
    @jwt_required()
    @ns.expect(facturas_query_parser)
    @ns.marshal_list_with(factura_model)
    @ns.doc('listar_facturas')
    def get(self):
        """Listar facturas de la empresa con filtros opcionales por cliente y estado"""
        empresa_id = get_empresa_id_from_jwt()
        args = facturas_query_parser.parse_args()
        return CarteraService.listar_facturas(
            empresa_id=empresa_id,
            cliente_id=args.get('cliente_id'),
            estado=args.get('estado')
        ), 200

    @jwt_required()
    @ns.expect([fields.Raw])
    def post(self):
        """Cargar/Sincronizar facturas nuevas"""
        empresa_id = get_empresa_id_from_jwt()
        data = request.json
        try:
            CarteraService.sincronizar_facturas(empresa_id, data)
            return {"message": "Facturas sincronizadas correctamente"}, 201
        except PermissionError as e:
            return {"error": str(e)}, 403
        except ValueError as e:
            return {"error": str(e)}, 400

@ns.route('/acuerdos-pago')
class AcuerdosPago(Resource):
    @jwt_required()
    @ns.expect(acuerdos_query_parser)
    @ns.marshal_list_with(acuerdo_pago_model)
    @ns.doc('listar_acuerdos_pago')
    def get(self):
        """Listar acuerdos de pago de la empresa."""
        empresa_id = get_empresa_id_from_jwt()
        args = acuerdos_query_parser.parse_args()
        return CarteraService.listar_acuerdos_pago(
            empresa_id=empresa_id,
            cliente_id=args.get('cliente_id'),
            estado=args.get('estado')
        ), 200

    @jwt_required()
    @ns.expect(fields.Raw)
    @ns.doc('crear_acuerdo_pago')
    def post(self):
        """Crear un acuerdo de pago para una factura con saldo pendiente."""
        errors = AcuerdoPagoSchema().validate(request.json or {})
        if errors:
            return errors, 400

        try:
            data = AcuerdoPagoSchema().load(request.json or {})
            acuerdo = CarteraService.crear_acuerdo_pago(
                get_empresa_id_from_jwt(), data
            )
            return acuerdo, 201
        except ValueError as error:
            return {"error": str(error)}, 400

@ns.route('/recaudos')
class RegistrarRecaudo(Resource):
    @jwt_required()
    @ns.marshal_list_with(pago_response_model)
    @ns.doc('listar_pagos')
    def get(self):
        """Listar el histórico de pagos de la empresa."""
        empresa_id = get_empresa_id_from_jwt()
        return CarteraService.listar_pagos(empresa_id), 200

    @jwt_required()
    @ns.expect(pago_model)
    def post(self):
        """Registrar un pago/recaudo"""
        empresa_id = get_empresa_id_from_jwt()
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
        empresa_id = get_empresa_id_from_jwt()
        try:
            reporte = CarteraService.estado_cuenta_cliente(empresa_id, id)
            return reporte, 200
        except PermissionError as e:
            return {"error": str(e)}, 403
        except ValueError as e:
            return {"error": str(e)}, 404
