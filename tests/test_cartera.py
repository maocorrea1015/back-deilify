import os
import tempfile
import unittest
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db_session, Base
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.factura import Factura, EstadoFactura
from app.models.pago import Pago
from flask_jwt_extended import create_access_token

class TestCarteraIntegration(unittest.TestCase):
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

        cls.db_fd, cls.db_path = tempfile.mkstemp()

        class TestConfig:
            TESTING = True
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{cls.db_path}"
            SECRET_KEY = "test-secret"
            JWT_SECRET_KEY = "test-jwt-secret"
            DEBUG = False
            RESTX_MASK_SWAGGER = False

        cls.app = create_app(TestConfig)

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
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.client = self.app.test_client()

        # Create two companies for multi-tenant testing
        self.empresa1 = Empresa(nombre="Empresa Uno", nit="900111222-1")
        self.empresa2 = Empresa(nombre="Empresa Dos", nit="900333444-2")
        db_session.add_all([self.empresa1, self.empresa2])
        db_session.commit()

        # Users and tokens
        self.user1 = Usuario(nombre="User 1", email="user1@empresa1.com", password_hash="hash", rol="ADMIN", empresa_id=self.empresa1.id)
        self.user2 = Usuario(nombre="User 2", email="user2@empresa2.com", password_hash="hash", rol="ADMIN", empresa_id=self.empresa2.id)
        db_session.add_all([self.user1, self.user2])
        db_session.commit()

        self.token_emp1 = create_access_token(identity=str(self.user1.id), additional_claims={"role": "ADMIN", "empresa_id": self.empresa1.id})
        self.token_emp2 = create_access_token(identity=str(self.user2.id), additional_claims={"role": "ADMIN", "empresa_id": self.empresa2.id})

        # Clients
        self.cliente1 = Cliente(empresa_id=self.empresa1.id, nombre="Cliente Alfa", identificacion="CLI-001", dias_plazo=30, limite_credito=1000000.0)
        self.cliente2 = Cliente(empresa_id=self.empresa1.id, nombre="Cliente Beta", identificacion="CLI-002", dias_plazo=15, limite_credito=500000.0)
        self.cliente_emp2 = Cliente(empresa_id=self.empresa2.id, nombre="Cliente Otro", identificacion="CLI-999", dias_plazo=30, limite_credito=200000.0)
        db_session.add_all([self.cliente1, self.cliente2, self.cliente_emp2])
        db_session.commit()

        # Invoices
        ahora = datetime.utcnow()
        self.fac1 = Factura(
            empresa_id=self.empresa1.id,
            cliente_id=self.cliente1.id,
            numero="FAC-101",
            fecha_emision=ahora - timedelta(days=20),
            fecha_vencimiento=ahora + timedelta(days=10),
            monto_total=300000.0,
            saldo_pendiente=300000.0,
            estado=EstadoFactura.PENDIENTE
        )
        self.fac2 = Factura(
            empresa_id=self.empresa1.id,
            cliente_id=self.cliente2.id,
            numero="FAC-102",
            fecha_emision=ahora - timedelta(days=40),
            fecha_vencimiento=ahora - timedelta(days=10),
            monto_total=150000.0,
            saldo_pendiente=150000.0,
            estado=EstadoFactura.VENCIDA
        )
        self.fac3 = Factura(
            empresa_id=self.empresa2.id,
            cliente_id=self.cliente_emp2.id,
            numero="FAC-201",
            fecha_emision=ahora - timedelta(days=5),
            fecha_vencimiento=ahora + timedelta(days=25),
            monto_total=80000.0,
            saldo_pendiente=80000.0,
            estado=EstadoFactura.PENDIENTE
        )
        db_session.add_all([self.fac1, self.fac2, self.fac3])
        db_session.commit()

    def tearDown(self):
        db_session.remove()
        self.app_context.pop()

    def test_listar_facturas_general(self):
        # Empresa 1 should list fac1 and fac2, NOT fac3
        headers = {"Authorization": f"Bearer {self.token_emp1}"}
        response = self.client.get("/cartera/facturas", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 2)
        numeros = [f["numero"] for f in data]
        self.assertIn("FAC-101", numeros)
        self.assertIn("FAC-102", numeros)
        self.assertNotIn("FAC-201", numeros)

        # Check client name is populated
        fac1_data = next(f for f in data if f["numero"] == "FAC-101")
        self.assertEqual(fac1_data["cliente_nombre"], "Cliente Alfa")
        self.assertEqual(fac1_data["monto_total"], 300000.0)

    def test_listar_facturas_filtro_cliente(self):
        headers = {"Authorization": f"Bearer {self.token_emp1}"}
        response = self.client.get(f"/cartera/facturas?cliente_id={self.cliente1.id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["numero"], "FAC-101")

    def test_listar_facturas_filtro_estado(self):
        headers = {"Authorization": f"Bearer {self.token_emp1}"}
        response = self.client.get("/cartera/facturas?estado=VENCIDA", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["numero"], "FAC-102")

    def test_listar_historico_pagos_por_empresa(self):
        ahora = datetime.utcnow()
        pago_emp1 = Pago(
            empresa_id=self.empresa1.id,
            factura_id=self.fac1.id,
            monto=100000.0,
            fecha_pago=ahora - timedelta(days=2),
            metodo_pago="TRANSFERENCIA",
            transaccion_id="TRX-101"
        )
        pago_emp2 = Pago(
            empresa_id=self.empresa2.id,
            factura_id=self.fac3.id,
            monto=80000.0,
            fecha_pago=ahora - timedelta(days=1),
            metodo_pago="EFECTIVO",
            transaccion_id="TRX-201"
        )
        db_session.add_all([pago_emp1, pago_emp2])
        db_session.commit()

        headers = {"Authorization": f"Bearer {self.token_emp1}"}
        response = self.client.get("/cartera/recaudos", headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]["factura_numero"], "FAC-101")
        self.assertEqual(response.json[0]["cliente_nombre"], "Cliente Alfa")
        self.assertEqual(response.json[0]["monto"], 100000.0)
        self.assertNotEqual(response.json[0]["transaccion_id"], "TRX-201")

    def test_crear_y_listar_acuerdo_pago(self):
        headers = {"Authorization": f"Bearer {self.token_emp1}"}
        payload = {
            "factura_id": self.fac2.id,
            "numero_cuotas": 3,
            "fecha_inicio": "2026-09-15T00:00:00",
            "observaciones": "Acuerdo telefónico"
        }

        post_response = self.client.post(
            "/cartera/acuerdos-pago", json=payload, headers=headers
        )

        self.assertEqual(post_response.status_code, 201)
        self.assertEqual(post_response.json["estado"], "ACTIVO")
        self.assertEqual(post_response.json["factura_numero"], "FAC-102")
        self.assertEqual(post_response.json["monto_acordado"], 150000.0)
        self.assertEqual(post_response.json["numero_cuotas"], 3)
        self.assertEqual(post_response.json["valor_cuota"], 50000.0)

        get_response = self.client.get("/cartera/acuerdos-pago", headers=headers)
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(get_response.json), 1)
        self.assertEqual(get_response.json[0]["observaciones"], "Acuerdo telefónico")

    def test_rechazar_acuerdo_de_factura_de_otra_empresa(self):
        headers = {"Authorization": f"Bearer {self.token_emp1}"}
        response = self.client.post(
            "/cartera/acuerdos-pago",
            json={"factura_id": self.fac3.id, "numero_cuotas": 2},
            headers=headers
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["error"], "Factura no encontrada")

    def test_sincronizar_y_listar_facturas(self):
        headers = {"Authorization": f"Bearer {self.token_emp1}"}
        payload = [{
            "cliente_id": self.cliente1.id,
            "numero": "FAC-999",
            "fecha_emision": "2026-09-01T00:00:00",
            "fecha_vencimiento": "2026-09-30T00:00:00",
            "monto_total": 500000.0
        }]
        post_resp = self.client.post("/cartera/facturas", json=payload, headers=headers)
        self.assertEqual(post_resp.status_code, 201)

        get_resp = self.client.get("/cartera/facturas", headers=headers)
        self.assertEqual(get_resp.status_code, 200)
        numeros = [f["numero"] for f in get_resp.json]
        self.assertIn("FAC-999", numeros)
