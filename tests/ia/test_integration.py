import os
import tempfile
import unittest
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from app import create_app
from app.extensions import db_session, Base
from app.models.empresa import Empresa
from app.models.cliente import Cliente
from app.models.factura import Factura, EstadoFactura
from app.models.pago import Pago
from app.ia.repositories.ai_model_repository import AIModelRepository
from app.ia.repositories.prediction_repository import PredictionRepository

class TestAIIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        try:
            from app.extensions import api
            api.namespaces = [api.default_namespace]
            api.endpoints = set()
            for k in list(sys.modules.keys()):
                if k.startswith('app') and k != 'app':
                    sys.modules.pop(k)
        except Exception:
            pass

        # Create a temp file for sqlite db
        cls.db_fd, cls.db_path = tempfile.mkstemp()

        
        # Override config for testing
        class TestConfig:
            TESTING = True
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{cls.db_path}"
            SECRET_KEY = "test-secret"
            JWT_SECRET_KEY = "test-jwt-secret"
            DEBUG = False
            RESTX_MASK_SWAGGER = False

        cls.app = create_app(TestConfig)
        
        # Re-initialize DB session and engine
        from sqlalchemy import create_engine
        cls.engine = create_engine(TestConfig.SQLALCHEMY_DATABASE_URI)
        db_session.configure(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        os.close(cls.db_fd)
        try:
            os.unlink(cls.db_path)
        except OSError:
            pass

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Clear and recreate database tables
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        self.client = self.app.test_client()
        self.created_files = []

        # Generate tokens with different roles
        self.admin_token = create_access_token(identity="admin", additional_claims={"role": "ADMIN"})
        self.user_token = create_access_token(identity="user", additional_claims={"role": "USER"})

    def tearDown(self):
        db_session.remove()
        self.app_context.pop()

        # Remove temporary joblib models created in training tests
        for fpath in self.created_files:
            try:
                if os.path.exists(fpath):
                    os.unlink(fpath)
            except OSError:
                pass


    def seed_data(self):
        # Create Empresa
        emp = Empresa(nombre="SaaS Tenant Test", nit="999888777-1")
        db_session.add(emp)
        db_session.commit()
        
        now = datetime.utcnow()
        # Seed 12 clients (to satisfy training minimum of 10)
        # Class 1: 4 clients, Class 0: 8 clients
        for i in range(12):
            is_delinquent = (i % 3 == 0)
            c = Cliente(
                empresa_id=emp.id,
                nombre=f"Cliente Integracion {i}",
                identificacion=f"IDENT-{i}",
                dias_plazo=30,
                limite_credito=5000.0 if not is_delinquent else 1000.0
            )
            db_session.add(c)
            db_session.commit()
            
            if is_delinquent:
                # Overdue invoice -> Class 1
                f = Factura(
                    empresa_id=emp.id,
                    cliente_id=c.id,
                    numero=f"FAC-BAD-{i}",
                    fecha_emision=now - timedelta(days=60),
                    fecha_vencimiento=now - timedelta(days=30),
                    monto_total=800.0,
                    saldo_pendiente=800.0,
                    estado=EstadoFactura.VENCIDA
                )
                db_session.add(f)
            else:
                # Paid invoice -> Class 0
                f = Factura(
                    empresa_id=emp.id,
                    cliente_id=c.id,
                    numero=f"FAC-GOOD-{i}",
                    fecha_emision=now - timedelta(days=45),
                    fecha_vencimiento=now - timedelta(days=15),
                    monto_total=1200.0,
                    saldo_pendiente=0.0,
                    estado=EstadoFactura.PAGADA
                )
                db_session.add(f)
                db_session.commit()
                
                p = Pago(
                    empresa_id=emp.id,
                    factura_id=f.id,
                    monto=1200.0,
                    fecha_pago=now - timedelta(days=20),
                    metodo_pago="EFECTIVO"
                )
                db_session.add(p)
                
            db_session.commit()

    def test_train_endpoint_no_admin(self):
        # Test training requires ADMIN role
        headers = {"Authorization": f"Bearer {self.user_token}"}
        response = self.client.post("/api/v1/ai/train", headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_train_endpoint_insufficient_data(self):
        # Empty DB (no data)
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.client.post("/api/v1/ai/train", headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Insuficiente cantidad", response.json["error"])

    def test_complete_flow(self):
        # 1. Seed historical data
        self.seed_data()
        
        # 2. Train models (ADMIN endpoint)
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        train_resp = self.client.post("/api/v1/ai/train", headers=headers)
        self.assertEqual(train_resp.status_code, 200)
        
        data = train_resp.json
        self.assertIn("version", data)
        self.assertIn("best_model_id", data)
        self.assertIn("best_algorithm", data)
        self.assertEqual(len(data["models"]), 2) # Both models trained
        
        version = data["version"]
        import glob
        modelos_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../app/ia/modelos"))
        for fpath in glob.glob(os.path.join(modelos_dir, f"*{version}*.joblib")):
            self.created_files.append(fpath)
            
        best_model_id = data["best_model_id"]

        
        # 3. Check models list (Regular user allowed)
        user_headers = {"Authorization": f"Bearer {self.user_token}"}
        list_resp = self.client.get("/api/v1/ai/models", headers=user_headers)
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(len(list_resp.json), 2)
        
        # Check active model
        active_model = AIModelRepository.get_active_model()
        self.assertIsNotNone(active_model)
        self.assertEqual(active_model.id, best_model_id)
        
        # 4. Predict risk for client ID 1
        predict_resp = self.client.post("/api/v1/ai/predict/1", headers=user_headers)
        self.assertEqual(predict_resp.status_code, 200)
        
        pred_data = predict_resp.json
        self.assertEqual(pred_data["client_id"], 1)
        self.assertIn("risk_score", pred_data)
        self.assertIn("probability", pred_data)
        self.assertIn("risk_level", pred_data)
        self.assertIn("recommendation", pred_data)
        
        # 5. Activate the other model manually (ADMIN required)
        other_model_id = [m["id"] for m in list_resp.json if m["id"] != best_model_id][0]
        activate_resp = self.client.put(f"/api/v1/ai/models/{other_model_id}/activate", headers=headers)
        self.assertEqual(activate_resp.status_code, 200)
        
        new_active = AIModelRepository.get_active_model()
        self.assertEqual(new_active.id, other_model_id)
        
        # 6. Check prediction logs list with pagination
        pred_list_resp = self.client.get("/api/v1/ai/predictions?page=1&per_page=5", headers=user_headers)
        self.assertEqual(pred_list_resp.status_code, 200)
        self.assertEqual(pred_list_resp.json["total"], 1)
        self.assertEqual(len(pred_list_resp.json["predictions"]), 1)

    def test_multitenancy_isolation(self):
        # 1. Seed historical data first to have models trained and active
        self.seed_data()
        
        # Train models to have an active model
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        train_resp = self.client.post("/api/v1/ai/train", headers=headers)
        self.assertEqual(train_resp.status_code, 200)
        best_model_id = train_resp.json["best_model_id"]
        
        # Keep track of generated joblib files
        import glob
        modelos_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../app/ia/modelos"))
        version = train_resp.json["version"]
        for fpath in glob.glob(os.path.join(modelos_dir, f"*{version}*.joblib")):
            self.created_files.append(fpath)

        # Create Company B and a client under Company B
        emp_b = Empresa(nombre="Company B Tenant", nit="111222333-2")
        db_session.add(emp_b)
        db_session.commit()
        
        # Client 13 is under Company B (id = 2)
        client_b = Cliente(
            empresa_id=emp_b.id,
            nombre="Cliente Company B",
            identificacion="IDENT-B",
            dias_plazo=30,
            limite_credito=2000.0
        )
        db_session.add(client_b)
        db_session.commit()

        # Tokens for Company A (id=1) and Company B (id=2)
        token_a = create_access_token(identity="user_a", additional_claims={"role": "USER", "empresa_id": 1})
        token_b = create_access_token(identity="user_b", additional_claims={"role": "USER", "empresa_id": emp_b.id})
        
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # Client A (ID 1, belongs to Company A)
        # Client B (client_b.id, belongs to Company B)

        # 1. Company A tries to predict risk of Company B's client -> should fail with 403
        resp = self.client.post(f"/api/v1/ai/predict/{client_b.id}", headers=headers_a)
        self.assertEqual(resp.status_code, 403)

        # Non-existent client -> should fail with 404
        resp_nonexistent = self.client.post("/api/v1/ai/predict/9999", headers=headers_a)
        self.assertEqual(resp_nonexistent.status_code, 404)

        # 2. Company B tries to predict risk of Company B's client -> should succeed
        resp = self.client.post(f"/api/v1/ai/predict/{client_b.id}", headers=headers_b)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["client_id"], client_b.id)

        # 3. Company A tries to get prediction history -> should only see predictions of Company A clients
        # First, let's predict for a Company A client with token_a (client 1 belongs to Company A)
        resp_predict_a = self.client.post("/api/v1/ai/predict/1", headers=headers_a)
        self.assertEqual(resp_predict_a.status_code, 200)

        # Now query history with token_a
        history_a = self.client.get("/api/v1/ai/predictions", headers=headers_a)
        self.assertEqual(history_a.status_code, 200)
        # Verify all retrieved logs belong to Company A's client
        for log in history_a.json["predictions"]:
            self.assertEqual(log["client_id"], 1)

        # Query history with token_b
        history_b = self.client.get("/api/v1/ai/predictions", headers=headers_b)
        self.assertEqual(history_b.status_code, 200)
        # Verify all retrieved logs belong to Company B's client
        for log in history_b.json["predictions"]:
            self.assertEqual(log["client_id"], client_b.id)

        # 4. Company A tries to get the smart report of Company B's client -> should fail with 403
        report_resp_fail = self.client.get(f"/api/v1/ai/predict/{client_b.id}/report", headers=headers_a)
        self.assertEqual(report_resp_fail.status_code, 403)

        # Non-existent client report -> should fail with 404
        report_nonexistent = self.client.get("/api/v1/ai/predict/9999/report", headers=headers_a)
        self.assertEqual(report_nonexistent.status_code, 404)

        # 5. Company B gets the smart report of Company B's client -> should succeed and contain correct structure
        report_resp_success = self.client.get(f"/api/v1/ai/predict/{client_b.id}/report", headers=headers_b)
        self.assertEqual(report_resp_success.status_code, 200)
        report_data = report_resp_success.json
        self.assertEqual(report_data["cliente_id"], client_b.id)
        self.assertIn("analisis_cartera", report_data)
        self.assertIn("evaluacion_ia", report_data)
        self.assertIn("dictamen_detallado", report_data)

        # 6. Cartera endpoint: Company A tries to get state of account for Company B's client -> should fail with 403
        state_resp_fail = self.client.get(f"/cartera/clientes/{client_b.id}/estado-cuenta", headers=headers_a)
        self.assertEqual(state_resp_fail.status_code, 403)

        # Non-existent client state of account -> should fail with 404
        state_nonexistent = self.client.get("/cartera/clientes/9999/estado-cuenta", headers=headers_a)
        self.assertEqual(state_nonexistent.status_code, 404)

        # 7. Cartera endpoint: Company B gets state of account for Company B's client -> should succeed
        state_resp_success = self.client.get(f"/cartera/clientes/{client_b.id}/estado-cuenta", headers=headers_b)
        self.assertEqual(state_resp_success.status_code, 200)
