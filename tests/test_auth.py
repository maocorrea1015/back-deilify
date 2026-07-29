import os
import tempfile
import unittest
from app import create_app
from app.extensions import db_session, Base
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from flask_jwt_extended import decode_token

class TestAuthIntegration(unittest.TestCase):
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

    def tearDown(self):
        db_session.remove()
        self.app_context.pop()

    def test_register_user_with_new_company(self):
        payload = {
            "nombre": "Mao Correa",
            "email": "mao@deilify.com",
            "password": "securepassword123",
            "rol": "ADMIN",
            "empresa_nombre": "Deilify SaaS",
            "empresa_nit": "123456789-0"
        }
        response = self.client.post("/auth/register", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["nombre"], "Mao Correa")
        self.assertEqual(data["email"], "mao@deilify.com")
        self.assertEqual(data["rol"], "ADMIN")
        self.assertIsNotNone(data["empresa_id"])
        self.assertEqual(data["empresa"]["nombre"], "Deilify SaaS")
        self.assertEqual(data["empresa"]["nit"], "123456789-0")

    def test_register_user_in_existing_company(self):
        empresa = Empresa(nombre="Empresa Existente", nit="987654321-1")
        db_session.add(empresa)
        db_session.commit()

        payload = {
            "nombre": "Juan Perez",
            "email": "juan@existing.com",
            "password": "anotherpassword",
            "rol": "USER",
            "empresa_id": empresa.id
        }
        response = self.client.post("/auth/register", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["nombre"], "Juan Perez")
        self.assertEqual(data["email"], "juan@existing.com")
        self.assertEqual(data["rol"], "USER")
        self.assertEqual(data["empresa_id"], empresa.id)

    def test_login_successful_and_get_me(self):
        empresa = Empresa(nombre="Login Company", nit="555-555")
        db_session.add(empresa)
        db_session.commit()

        user = Usuario(
            nombre="User Login",
            email="login@test.com",
            rol="USER",
            empresa_id=empresa.id
        )
        user.set_password("mypassword")
        db_session.add(user)
        db_session.commit()

        payload = {
            "email": "login@test.com",
            "password": "mypassword"
        }
        response = self.client.post("/auth/login", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIn("access_token", data)
        self.assertEqual(data["usuario"]["email"], "login@test.com")

        decoded = decode_token(data["access_token"])
        self.assertEqual(decoded["sub"], str(user.id))
        self.assertEqual(decoded["role"], "USER")
        self.assertEqual(decoded["empresa_id"], empresa.id)

        headers = {"Authorization": f"Bearer {data['access_token']}"}
        me_response = self.client.get("/auth/me", headers=headers)
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json["email"], "login@test.com")

    def test_login_invalid_credentials(self):
        payload = {
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        }
        response = self.client.post("/auth/login", json=payload)
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)
