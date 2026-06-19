import numpy as np
import pandas as pd
from datetime import datetime
from sqlalchemy import select, func
from ...extensions import db_session
from ...models.cliente import Cliente
from ...models.factura import Factura, EstadoFactura
from ...models.pago import Pago
from ...models.audit_log import HistorialCobranza

FEATURE_COLUMNS = [
    "limite_credito",
    "dias_plazo",
    "total_facturas",
    "facturas_pagadas",
    "facturas_vencidas",
    "total_monto_facturado",
    "saldo_pendiente_total",
    "monto_promedio_factura",
    "ratio_saldo_limite",
    "promedio_dias_pago",
    "max_dias_mora",
    "tasa_mora",
    "cantidad_notas_cobranza"
]

def extract_client_features(cliente: Cliente, ref_date: datetime = None) -> dict:
    """
    Extracts features for a single client.
    """
    if ref_date is None:
        ref_date = datetime.utcnow()

    facturas = cliente.facturas
    total_facturas = len(facturas)
    facturas_pagadas = 0
    facturas_vencidas = 0
    total_monto_facturado = 0.0
    saldo_pendiente_total = 0.0
    
    delays = []
    max_dias_mora = 0.0
    late_invoices_count = 0
    
    for f in facturas:
        total_monto_facturado += f.monto_total
        saldo_pendiente_total += f.saldo_pendiente
        
        is_paid = f.saldo_pendiente <= 0 or f.estado == EstadoFactura.PAGADA
        
        if is_paid:
            facturas_pagadas += 1
            if f.recaudos:
                payment_dates = [p.fecha_pago for p in f.recaudos if p.fecha_pago]
                if payment_dates:
                    fully_paid_date = max(payment_dates)
                    delay = (fully_paid_date - f.fecha_vencimiento).days
                else:
                    delay = 0
            else:
                delay = 0
            delays.append(delay)
            if delay > 0:
                late_invoices_count += 1
                if delay > max_dias_mora:
                    max_dias_mora = float(delay)
        else:
            is_overdue = f.fecha_vencimiento < ref_date
            if is_overdue:
                facturas_vencidas += 1
                delay = (ref_date - f.fecha_vencimiento).days
                delays.append(delay)
                late_invoices_count += 1
                if delay > max_dias_mora:
                    max_dias_mora = float(delay)
                    
    promedio_dias_pago = float(np.mean(delays)) if delays else 0.0
    tasa_mora = float(late_invoices_count / total_facturas) if total_facturas > 0 else 0.0
    monto_promedio_factura = float(total_monto_facturado / total_facturas) if total_facturas > 0 else 0.0
    ratio_saldo_limite = float(saldo_pendiente_total / cliente.limite_credito) if cliente.limite_credito > 0 else 0.0
    
    # Get count of collection notes
    cantidad_notas = db_session.execute(
        select(func.count(HistorialCobranza.id)).where(HistorialCobranza.cliente_id == cliente.id)
    ).scalar() or 0
    
    features = {
        "limite_credito": float(cliente.limite_credito),
        "dias_plazo": int(cliente.dias_plazo),
        "total_facturas": int(total_facturas),
        "facturas_pagadas": int(facturas_pagadas),
        "facturas_vencidas": int(facturas_vencidas),
        "total_monto_facturado": float(total_monto_facturado),
        "saldo_pendiente_total": float(saldo_pendiente_total),
        "monto_promedio_factura": float(monto_promedio_factura),
        "ratio_saldo_limite": float(ratio_saldo_limite),
        "promedio_dias_pago": float(promedio_dias_pago),
        "max_dias_mora": float(max_dias_mora),
        "tasa_mora": float(tasa_mora),
        "cantidad_notas_cobranza": int(cantidad_notas)
    }
    
    return features

def determine_target(features: dict) -> int:
    """
    Defines default/delinquency risk target.
    1 if client has overdue invoices, max delay > 30 days, or avg delay > 15 days.
    """
    if features["facturas_vencidas"] > 0 or features["max_dias_mora"] > 30 or features["promedio_dias_pago"] > 15:
        return 1
    return 0

def build_training_dataset(ref_date: datetime = None) -> pd.DataFrame:
    """
    Builds the dataset of features and targets from the DB.
    """
    if ref_date is None:
        ref_date = datetime.utcnow()

    clientes = db_session.execute(select(Cliente)).scalars().all()
    
    dataset_rows = []
    for c in clientes:
        feats = extract_client_features(c, ref_date)
        feats["client_id"] = c.id
        feats["target"] = determine_target(feats)
        dataset_rows.append(feats)
        
    return pd.DataFrame(dataset_rows)
