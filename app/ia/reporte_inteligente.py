import logging
from datetime import datetime
from sqlalchemy import select
from ..extensions import db_session
from ..models.cliente import Cliente
from .services.prediction_service import PredictionService
from .ml.features import extract_client_features

logger = logging.getLogger(__name__)

class SmartReportService:
    @staticmethod
    def generate_client_report(client_id: int, empresa_id: int = None) -> dict:
        """
        Generates a detailed credit risk report for a client by accessing only their portfolio.
        """
        logger.info(f"Generando reporte inteligente para cliente ID {client_id}")
        
        # 1. Get the client and verify company permissions
        cliente = db_session.execute(select(Cliente).where(Cliente.id == client_id)).scalar_one_or_none()
        if not cliente:
            raise ValueError(f"Cliente con ID {client_id} no encontrado.")
            
        if empresa_id is not None and cliente.empresa_id != empresa_id:
            raise PermissionError("Acceso denegado. El cliente no pertenece a su empresa.")
            
        # 2. Extract features (accessing only the client's own portfolio/cartera)
        features = extract_client_features(cliente)
        
        # 3. Get prediction metrics
        try:
            pred_result = PredictionService.predict_client_risk(client_id, empresa_id)
        except Exception as e:
            logger.warning(f"No se pudo calcular la predicción de riesgo: {str(e)}")
            pred_result = {
                "risk_score": None,
                "probability": None,
                "risk_level": "DESCONOCIDO",
                "recommendation": "Por favor, entrene y active un modelo de IA primero."
            }
            
        # 4. Construct a descriptive verdict
        verdict = f"El cliente {cliente.nombre} tiene un límite de crédito de {cliente.limite_credito:,.2f} con plazo de {cliente.dias_plazo} días. "
        
        if features["facturas_vencidas"] > 0:
            verdict += f"Actualmente posee {features['facturas_vencidas']} factura(s) vencida(s) con un retraso máximo de {features['max_dias_mora']} días, lo cual representa un riesgo directo de mora. "
        else:
            verdict += "No presenta facturas vencidas al día de hoy. "
            
        if features["promedio_dias_pago"] > 0:
            verdict += f"Históricamente presenta un promedio de demora en sus pagos de {features['promedio_dias_pago']:.1f} días. "
        else:
            verdict += "Históricamente realiza sus pagos dentro de los plazos establecidos. "
            
        if features["ratio_saldo_limite"] > 0.8:
            verdict += f"Su saldo pendiente actual ({features['saldo_pendiente_total']:,.2f}) consume un porcentaje crítico de su límite de crédito ({features['ratio_saldo_limite']*100:.1f}%). "
            
        report = {
            "cliente_id": cliente.id,
            "nombre": cliente.nombre,
            "identificacion": cliente.identificacion,
            "limite_credito": cliente.limite_credito,
            "dias_plazo": cliente.dias_plazo,
            "fecha_reporte": datetime.utcnow().isoformat(),
            "analisis_cartera": {
                "total_facturas": features["total_facturas"],
                "facturas_pagadas": features["facturas_pagadas"],
                "facturas_vencidas": features["facturas_vencidas"],
                "total_monto_facturado": features["total_monto_facturado"],
                "saldo_pendiente_total": features["saldo_pendiente_total"],
                "ratio_uso_credito": features["ratio_saldo_limite"],
                "promedio_dias_retraso": features["promedio_dias_pago"],
                "maximo_dias_mora": features["max_dias_mora"],
                "tasa_mora_facturas": features["tasa_mora"],
                "gestiones_cobranza_realizadas": features["cantidad_notas_cobranza"]
            },
            "evaluacion_ia": {
                "score_riesgo": pred_result["risk_score"],
                "probabilidad_mora": pred_result["probability"],
                "nivel_riesgo": pred_result["risk_level"],
                "recomendacion": pred_result["recommendation"]
            },
            "dictamen_detallado": verdict
        }
        
        return report
