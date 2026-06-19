import unittest
from app.ia.services.prediction_service import PredictionService
from app.ia.ml.features import determine_target
from app.ia.schemas.ai_schemas import AIModelSchema, PredictionLogSchema

class TestAIUnit(unittest.TestCase):
    def test_risk_level_muy_bajo(self):
        level, rec = PredictionService.get_risk_level_and_recommendation(15)
        self.assertEqual(level, "MUY BAJO")
        self.assertIn("Aprobación", rec)

    def test_risk_level_bajo(self):
        level, rec = PredictionService.get_risk_level_and_recommendation(30)
        self.assertEqual(level, "BAJO")
        self.assertIn("Monitoreo estándar", rec)

    def test_risk_level_medio(self):
        level, rec = PredictionService.get_risk_level_and_recommendation(50)
        self.assertEqual(level, "MEDIO")
        self.assertIn("Monitoreo periódico", rec)

    def test_risk_level_alto(self):
        level, rec = PredictionService.get_risk_level_and_recommendation(75)
        self.assertEqual(level, "ALTO")
        self.assertIn("Seguimiento preventivo", rec)

    def test_risk_level_muy_alto(self):
        level, rec = PredictionService.get_risk_level_and_recommendation(95)
        self.assertEqual(level, "MUY ALTO")
        self.assertIn("cobro inmediata", rec)

    def test_determine_target_delinquent(self):
        # Overdue invoices present
        feats = {
            "facturas_vencidas": 1,
            "max_dias_mora": 5.0,
            "promedio_dias_pago": 2.0
        }
        self.assertEqual(determine_target(feats), 1)

        # High max delay
        feats = {
            "facturas_vencidas": 0,
            "max_dias_mora": 35.0,
            "promedio_dias_pago": 5.0
        }
        self.assertEqual(determine_target(feats), 1)

        # High avg delay
        feats = {
            "facturas_vencidas": 0,
            "max_dias_mora": 20.0,
            "promedio_dias_pago": 18.0
        }
        self.assertEqual(determine_target(feats), 1)

    def test_determine_target_non_delinquent(self):
        feats = {
            "facturas_vencidas": 0,
            "max_dias_mora": 10.0,
            "promedio_dias_pago": 5.0
        }
        self.assertEqual(determine_target(feats), 0)

    def test_schemas_dump(self):
        model_data = {
            "id": 1,
            "name": "Test Model",
            "version": "v1",
            "algorithm": "XGBClassifier",
            "accuracy": 0.95,
            "precision": 0.94,
            "recall": 0.93,
            "f1_score": 0.92,
            "roc_auc": 0.96,
            "model_path": "/path",
            "is_active": True
        }
        schema = AIModelSchema()
        dumped = schema.dump(model_data)
        self.assertEqual(dumped["name"], "Test Model")
        self.assertEqual(dumped["roc_auc"], 0.96)
        self.assertTrue(dumped["is_active"])
