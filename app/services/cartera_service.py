import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import select, func
from ..extensions import db_session
from ..models.factura import Factura, EstadoFactura
from ..models.pago import Pago
from ..models.cliente import Cliente

class CarteraService:
    @staticmethod
    def registrar_pago(empresa_id, data):
        factura = db_session.execute(
            select(Factura).where(Factura.id == data['factura_id'], Factura.empresa_id == empresa_id)
        ).scalar_one_or_none()

        if not factura:
            raise ValueError("Factura no encontrada")

        nuevo_pago = Pago(
            empresa_id=empresa_id,
            factura_id=factura.id,
            monto=data['monto'],
            metodo_pago=data['metodo_pago'],
            transaccion_id=data.get('transaccion_id')
        )

        # Lógica financiera: Restar saldo y actualizar estado
        factura.saldo_pendiente -= data['monto']
        if factura.saldo_pendiente <= 0:
            factura.saldo_pendiente = 0
            factura.estado = EstadoFactura.PAGADA
        
        db_session.add(nuevo_pago)
        db_session.commit()
        return nuevo_pago

    @staticmethod
    def obtener_dashboard(empresa_id):
        # Obtener todas las facturas no pagadas de la empresa
        query = select(Factura).where(Factura.empresa_id == empresa_id, Factura.estado != EstadoFactura.PAGADA)
        results = db_session.execute(query).scalars().all()
        
        if not results:
            return {
                "cartera_vencida_total": 0,
                "dso_proyectado": 0,
                "distribucion_edades": {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
            }

        # Usar Pandas para análisis rápido
        df = pd.DataFrame([{
            'id': f.id,
            'saldo': f.saldo_pendiente,
            'vencimiento': f.fecha_vencimiento,
            'emision': f.fecha_emision,
            'estado': f.estado.value
        } for f in results])

        ahora = datetime.utcnow()
        df['dias_vencidos'] = (ahora - df['vencimiento']).dt.days
        df['dias_vencidos'] = df['dias_vencidos'].apply(lambda x: max(0, x))

        # Cartera Vencida Total
        cartera_vencida = df[df['dias_vencidos'] > 0]['saldo'].sum()

        # Distribución de edades
        bins = [-1, 30, 60, 90, float('inf')]
        labels = ['0-30', '31-60', '61-90', '90+']
        df['rango'] = pd.cut(df['dias_vencidos'], bins=bins, labels=labels)
        distribucion = df.groupby('rango')['saldo'].sum().to_dict()

        # DSO Proyectado (Días de venta pendientes)
        # DSO = (Cuentas por Cobrar / Ventas Totales) * Días del periodo (asumimos 30 días para proyección)
        total_cxc = df['saldo'].sum()
        # Para ventas totales, en un dashboard real buscaríamos el histórico de 30 días.
        # Aquí simplificamos con el monto total de facturas emitidas en el último mes.
        query_ventas = select(func.sum(Factura.monto_total)).where(
            Factura.empresa_id == empresa_id, 
            Factura.fecha_emision >= ahora - timedelta(days=30)
        )
        ventas_mes = db_session.execute(query_ventas).scalar() or 1 # Evitar división por cero
        dso = (total_cxc / ventas_mes) * 30

        return {
            "cartera_vencida_total": float(cartera_vencida),
            "dso_proyectado": round(float(dso), 2),
            "distribucion_edades": {k: float(v) for k, v in distribucion.items()}
        }

    @staticmethod
    def sincronizar_facturas(empresa_id, facturas_data):
        for data in facturas_data:
            nueva_factura = Factura(
                empresa_id=empresa_id,
                cliente_id=data['cliente_id'],
                numero=data['numero'],
                fecha_emision=data['fecha_emision'],
                fecha_vencimiento=data['fecha_vencimiento'],
                monto_total=data['monto_total'],
                saldo_pendiente=data['monto_total'],
                estado=EstadoFactura.PENDIENTE
            )
            db_session.add(nueva_factura)
        db_session.commit()

    @staticmethod
    def estado_cuenta_cliente(empresa_id, cliente_id):
        query = select(Factura).where(Factura.empresa_id == empresa_id, Factura.cliente_id == cliente_id)
        facturas = db_session.execute(query).scalars().all()
        
        return [{
            "numero": f.numero,
            "vencimiento": f.fecha_vencimiento.isoformat(),
            "monto": f.monto_total,
            "saldo": f.saldo_pendiente,
            "estado": f.estado.value
        } for f in facturas]
