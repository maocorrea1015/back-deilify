from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from ...extensions import db_session
from ...middleware.tenant import get_empresa_id_from_jwt
from ...models.cliente import Cliente
from ...schemas.cartera import ClienteSchema

ns = Namespace('clientes', description='Administracion de Clientes', security='apikey')

cliente_model = ns.model('Cliente', {
    'nombre': fields.String(required=True, description='Nombre o razon social del cliente'),
    'identificacion': fields.String(required=True, description='Identificacion tributaria o documento'),
    'dias_plazo': fields.Integer(description='Dias de plazo de pago', default=30),
    'limite_credito': fields.Float(description='Limite de credito', default=0.0),
})

cliente_update_model = ns.model('ClienteUpdate', {
    'nombre': fields.String(description='Nombre o razon social del cliente'),
    'identificacion': fields.String(description='Identificacion tributaria o documento'),
    'dias_plazo': fields.Integer(description='Dias de plazo de pago'),
    'limite_credito': fields.Float(description='Limite de credito'),
})


def _get_cliente_or_404(empresa_id, cliente_id):
    cliente = db_session.execute(
        select(Cliente).where(Cliente.id == cliente_id)
    ).scalars().first()
    if not cliente:
        return None, ({"error": "El cliente no existe."}, 404)
    if cliente.empresa_id != empresa_id:
        return None, ({"error": "Acceso denegado. El cliente no pertenece a esta empresa."}, 403)
    return cliente, None


@ns.route('/')
class ClienteListResource(Resource):
    @jwt_required()
    def get(self):
        """Listar todos los clientes de la empresa"""
        empresa_id = get_empresa_id_from_jwt()
        clientes = db_session.execute(
            select(Cliente).where(Cliente.empresa_id == empresa_id).order_by(Cliente.nombre.asc())
        ).scalars().all()
        return ClienteSchema(many=True).dump(clientes), 200

    @jwt_required()
    @ns.expect(cliente_model)
    def post(self):
        """Crear un cliente dentro de la empresa autenticada"""
        empresa_id = get_empresa_id_from_jwt()
        data = request.json or {}
        schema = ClienteSchema()
        errors = schema.validate(data)
        if errors:
            return errors, 400

        existente = db_session.execute(
            select(Cliente).where(
                Cliente.empresa_id == empresa_id,
                Cliente.identificacion == data['identificacion']
            )
        ).scalars().first()
        if existente:
            return {"error": "Ya existe un cliente con esa identificacion en la empresa."}, 400

        cliente = Cliente(
            empresa_id=empresa_id,
            nombre=data['nombre'],
            identificacion=data['identificacion'],
            dias_plazo=data.get('dias_plazo', 30),
            limite_credito=data.get('limite_credito', 0.0),
        )
        db_session.add(cliente)
        try:
            db_session.commit()
        except IntegrityError:
            db_session.rollback()
            return {"error": "No fue posible crear el cliente."}, 400
        return schema.dump(cliente), 201


@ns.route('/<int:id>')
@ns.param('id', 'ID del cliente')
class ClienteResource(Resource):
    @jwt_required()
    def get(self, id):
        """Obtener un cliente de la empresa"""
        empresa_id = get_empresa_id_from_jwt()
        cliente, error = _get_cliente_or_404(empresa_id, id)
        if error:
            return error
        return ClienteSchema().dump(cliente), 200

    @jwt_required()
    @ns.expect(cliente_update_model)
    def put(self, id):
        """Actualizar un cliente de la empresa"""
        empresa_id = get_empresa_id_from_jwt()
        cliente, error = _get_cliente_or_404(empresa_id, id)
        if error:
            return error

        data = request.json or {}
        if not data:
            return {"error": "Datos no proporcionados"}, 400

        schema = ClienteSchema(partial=True)
        errors = schema.validate(data)
        if errors:
            return errors, 400

        if 'identificacion' in data and data['identificacion'] != cliente.identificacion:
            existente = db_session.execute(
                select(Cliente).where(
                    Cliente.empresa_id == empresa_id,
                    Cliente.identificacion == data['identificacion'],
                    Cliente.id != id
                )
            ).scalars().first()
            if existente:
                return {"error": "Ya existe otro cliente con esa identificacion."}, 400

        for field in ['nombre', 'identificacion', 'dias_plazo', 'limite_credito']:
            if field in data:
                setattr(cliente, field, data[field])
        db_session.commit()
        return ClienteSchema().dump(cliente), 200

    @jwt_required()
    def delete(self, id):
        """Eliminar un cliente sin facturas asociadas"""
        empresa_id = get_empresa_id_from_jwt()
        cliente, error = _get_cliente_or_404(empresa_id, id)
        if error:
            return error
        if cliente.facturas:
            return {"error": "No se puede eliminar un cliente con facturas asociadas."}, 400
        db_session.delete(cliente)
        db_session.commit()
        return {"message": "Cliente eliminado correctamente"}, 200
