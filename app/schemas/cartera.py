from marshmallow import Schema, fields, post_load
from ..models.factura import EstadoFactura

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
