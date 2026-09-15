from marshmallow import Schema, fields, post_load
from ..models.factura import EstadoFactura
from ..models.acuerdo_pago import EstadoAcuerdoPago

class ClienteSchema(Schema):
    id = fields.Int(dump_only=True)
    nombre = fields.Str(required=True)
    identificacion = fields.Str(required=True)
    dias_plazo = fields.Int()
    limite_credito = fields.Float()

class FacturaSchema(Schema):
    id = fields.Int(dump_only=True)
    numero = fields.Str(required=True)
    fecha_emision = fields.DateTime(required=True)
    fecha_vencimiento = fields.DateTime(required=True)
    monto_total = fields.Float(required=True)
    saldo_pendiente = fields.Float(dump_only=True)
    estado = fields.Enum(EstadoFactura, dump_only=True)
    cliente_id = fields.Int(required=True)

class PagoSchema(Schema):
    id = fields.Int(dump_only=True)
    factura_id = fields.Int(required=True)
    monto = fields.Float(required=True)
    fecha_pago = fields.DateTime()
    metodo_pago = fields.Str(required=True)
    transaccion_id = fields.Str()


class AcuerdoPagoSchema(Schema):
    factura_id = fields.Int(required=True)
    monto_acordado = fields.Float(allow_none=True)
    numero_cuotas = fields.Int(required=True)
    fecha_inicio = fields.DateTime(allow_none=True)
    observaciones = fields.Str(allow_none=True)


class AcuerdoPagoResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    empresa_id = fields.Int(dump_only=True)
    cliente_id = fields.Int(dump_only=True)
    factura_id = fields.Int(dump_only=True)
    factura_numero = fields.Str(dump_only=True)
    cliente_nombre = fields.Str(dump_only=True)
    monto_acordado = fields.Float(dump_only=True)
    numero_cuotas = fields.Int(dump_only=True)
    valor_cuota = fields.Float(dump_only=True)
    fecha_inicio = fields.DateTime(dump_only=True)
    fecha_fin = fields.DateTime(dump_only=True)
    estado = fields.Enum(EstadoAcuerdoPago, dump_only=True)
    observaciones = fields.Str(allow_none=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
