import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import select, func
from ..extensions import db_session
from ..models.factura import Factura, EstadoFactura
from ..models.pago import Pago
from ..models.cliente import Cliente
from ..models.acuerdo_pago import AcuerdoPago, EstadoAcuerdoPago

class CarteraService:
    @staticmethod
    def _serializar_acuerdo_pago(acuerdo):
        return {
            "id": acuerdo.id,
            "empresa_id": acuerdo.empresa_id,
            "cliente_id": acuerdo.cliente_id,
            "factura_id": acuerdo.factura_id,
            "factura_numero": acuerdo.factura.numero,
            "cliente_nombre": acuerdo.factura.cliente.nombre,
            "monto_acordado": float(acuerdo.monto_acordado),
            "numero_cuotas": acuerdo.numero_cuotas,
            "valor_cuota": float(acuerdo.valor_cuota),
            "fecha_inicio": acuerdo.fecha_inicio.isoformat(),
            "fecha_fin": acuerdo.fecha_fin.isoformat(),
            "estado": acuerdo.estado.value,
            "observaciones": acuerdo.observaciones,
            "created_at": acuerdo.created_at.isoformat()
        }

    @staticmethod
    def listar_acuerdos_pago(empresa_id, cliente_id=None, estado=None):
        query = select(AcuerdoPago).where(AcuerdoPago.empresa_id == empresa_id)
        if cliente_id is not None:
            query = query.where(AcuerdoPago.cliente_id == int(cliente_id))
        if estado:
            query = query.where(AcuerdoPago.estado == EstadoAcuerdoPago[str(estado).strip().upper()])

        acuerdos = db_session.execute(
            query.order_by(AcuerdoPago.created_at.desc(), AcuerdoPago.id.desc())
        ).scalars().all()

        return [CarteraService._serializar_acuerdo_pago(acuerdo) for acuerdo in acuerdos]

    @staticmethod
    def crear_acuerdo_pago(empresa_id, data):
        factura_id = int(data["factura_id"])
        numero_cuotas = int(data["numero_cuotas"])
        if numero_cuotas <= 0:
            raise ValueError("El número de cuotas debe ser mayor que cero")

        factura = db_session.execute(
            select(Factura).where(
                Factura.id == factura_id,
                Factura.empresa_id == empresa_id
            )
        ).scalar_one_or_none()
        if not factura:
            raise ValueError("Factura no encontrada")
        if factura.saldo_pendiente <= 0:
            raise ValueError("La factura no tiene saldo pendiente")

        monto_acordado = float(data.get("monto_acordado") or factura.saldo_pendiente)
        if monto_acordado <= 0:
            raise ValueError("El monto acordado debe ser mayor que cero")

        fecha_inicio = data.get("fecha_inicio") or datetime.utcnow()
        fecha_fin = fecha_inicio + timedelta(days=30 * numero_cuotas)
        acuerdo = AcuerdoPago(
            empresa_id=empresa_id,
            cliente_id=factura.cliente_id,
            factura_id=factura.id,
            monto_acordado=monto_acordado,
            numero_cuotas=numero_cuotas,
            valor_cuota=round(monto_acordado / numero_cuotas, 2),
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado=EstadoAcuerdoPago.ACTIVO,
            observaciones=data.get("observaciones")
        )
        db_session.add(acuerdo)
        db_session.commit()
        return CarteraService._serializar_acuerdo_pago(acuerdo)

    @staticmethod
    def listar_pagos(empresa_id):
        query = (
            select(Pago)
            .join(Factura, Pago.factura_id == Factura.id)
            .where(Pago.empresa_id == empresa_id, Factura.empresa_id == empresa_id)
            .order_by(Pago.fecha_pago.desc(), Pago.id.desc())
        )
        pagos = db_session.execute(query).scalars().all()

        return [{
            "id": pago.id,
            "factura_id": pago.factura_id,
            "factura_numero": pago.factura.numero if pago.factura else None,
            "cliente_id": pago.factura.cliente_id if pago.factura else None,
            "cliente_nombre": (
                pago.factura.cliente.nombre
                if pago.factura and pago.factura.cliente
                else "Cliente sin nombre"
            ),
            "monto": float(pago.monto),
            "fecha_pago": pago.fecha_pago.isoformat() if pago.fecha_pago else None,
            "metodo_pago": pago.metodo_pago,
            "transaccion_id": pago.transaccion_id
        } for pago in pagos]

    @staticmethod
    def listar_facturas(empresa_id, cliente_id=None, estado=None):
        query = select(Factura).where(Factura.empresa_id == empresa_id)
        if cliente_id is not None:
            query = query.where(Factura.cliente_id == int(cliente_id))
        if estado:
            estado_clean = str(estado).strip().upper()
            if estado_clean in EstadoFactura.__members__:
                query = query.where(Factura.estado == EstadoFactura[estado_clean])
            elif estado_clean == "VIGENTE":
                query = query.where(Factura.estado == EstadoFactura.PENDIENTE)

        query = query.order_by(Factura.fecha_vencimiento.asc(), Factura.id.desc())
        facturas = db_session.execute(query).scalars().all()

        ahora = datetime.utcnow()
        resultado = []
        for f in facturas:
            dias_mora = 0
            if f.estado == EstadoFactura.VENCIDA or (f.saldo_pendiente > 0 and f.fecha_vencimiento < ahora):
                dias_mora = max(0, (ahora - f.fecha_vencimiento).days)

            resultado.append({
                "id": f.id,
                "numero": f.numero,
                "cliente_id": f.cliente_id,
                "cliente_nombre": f.cliente.nombre if f.cliente else "Cliente sin nombre",
                "fecha_emision": f.fecha_emision.isoformat() if hasattr(f.fecha_emision, 'isoformat') else str(f.fecha_emision),
                "fecha_vencimiento": f.fecha_vencimiento.isoformat() if hasattr(f.fecha_vencimiento, 'isoformat') else str(f.fecha_vencimiento),
                "monto_total": float(f.monto_total),
                "saldo_pendiente": float(f.saldo_pendiente),
                "estado": f.estado.value if hasattr(f.estado, 'value') else str(f.estado),
                "dias_mora": dias_mora
            })
        return resultado

    @staticmethod
    def registrar_pago(empresa_id, data):
        factura_id = int(data['factura_id'])
        monto = float(data['monto'])
        transaccion_id = data.get('transaccion_id') or data.get('referencia')

        factura = db_session.execute(
            select(Factura).where(Factura.id == factura_id, Factura.empresa_id == empresa_id)
        ).scalar_one_or_none()

        if not factura:
            raise ValueError("Factura no encontrada")

        nuevo_pago = Pago(
            empresa_id=empresa_id,
            factura_id=factura.id,
            monto=monto,
            metodo_pago=data['metodo_pago'],
            transaccion_id=transaccion_id
        )

        # Lógica financiera: Restar saldo y actualizar estado
        factura.saldo_pendiente -= monto
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
            # Validar si el cliente existe en absoluto
            cliente = db_session.execute(
                select(Cliente).where(Cliente.id == data['cliente_id'])
            ).scalar_one_or_none()
            if not cliente:
                raise ValueError(f"El cliente con ID {data['cliente_id']} no existe.")
            # Validar si pertenece a la empresa
            if cliente.empresa_id != empresa_id:
                raise PermissionError(f"Acceso denegado. El cliente con ID {data['cliente_id']} no pertenece a esta empresa.")

            f_emision = datetime.fromisoformat(data['fecha_emision']) if isinstance(data['fecha_emision'], str) else data['fecha_emision']
            f_vencimiento = datetime.fromisoformat(data['fecha_vencimiento']) if isinstance(data['fecha_vencimiento'], str) else data['fecha_vencimiento']
            monto = float(data['monto_total'])

            nueva_factura = Factura(
                empresa_id=empresa_id,
                cliente_id=int(data['cliente_id']),
                numero=str(data['numero']),
                fecha_emision=f_emision,
                fecha_vencimiento=f_vencimiento,
                monto_total=monto,
                saldo_pendiente=monto,
                estado=EstadoFactura.PENDIENTE
            )
            db_session.add(nueva_factura)
        db_session.commit()

    @staticmethod
    def estado_cuenta_cliente(empresa_id, cliente_id):
        # Validar si el cliente existe en absoluto
        cliente = db_session.execute(
            select(Cliente).where(Cliente.id == cliente_id)
        ).scalar_one_or_none()
        if not cliente:
            raise ValueError("El cliente no existe.")
        # Validar si pertenece a la empresa
        if cliente.empresa_id != empresa_id:
            raise PermissionError("Acceso denegado. El cliente no pertenece a esta empresa.")

        query = select(Factura).where(Factura.empresa_id == empresa_id, Factura.cliente_id == cliente_id)
        facturas = db_session.execute(query).scalars().all()
        
        return [{
            "numero": f.numero,
            "vencimiento": f.fecha_vencimiento.isoformat(),
            "monto": f.monto_total,
            "saldo": f.saldo_pendiente,
            "estado": f.estado.value
        } for f in facturas]
