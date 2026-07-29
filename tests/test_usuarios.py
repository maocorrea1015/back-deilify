import os
import tempfile
import unittest
from app import create_app
from app.extensions import db_session, Base
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from flask_jwt_extended import create_access_token

class TestUsuariosIntegration(unittest.TestCase):
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

        # Seed initial companies
        self.empresa_a = Empresa(nombre="Empresa A", nit="111")
        self.empresa_b = Empresa(nombre="Empresa B", nit="222")
        db_session.add_all([self.empresa_a, self.empresa_b])
        db_session.commit()

        # Seed initial users for Company A
        self.admin_a = Usuario(nombre="Admin A", email="admina@test.com", rol="ADMIN", empresa_id=self.empresa_a.id)
        self.admin_a.set_password("password")
        
        self.user_a = Usuario(nombre="User A", email="usera@test.com", rol="USER", empresa_id=self.empresa_a.id)
        self.user_a.set_password("password")
        
        # Seed initial user for Company B
        self.admin_b = Usuario(nombre="Admin B", email="adminb@test.com", rol="ADMIN", empresa_id=self.empresa_b.id)
        self.admin_b.set_password("password")

        db_session.add_all([self.admin_a, self.user_a, self.admin_b])
        db_session.commit()

        # Generate tokens
        self.admin_a_token = create_access_token(identity=str(self.admin_a.id), additional_claims={"role": "ADMIN", "empresa_id": self.empresa_a.id})
        self.user_a_token = create_access_token(identity=str(self.user_a.id), additional_claims={"role": "USER", "empresa_id": self.empresa_a.id})
        self.admin_b_token = create_access_token(identity=str(self.admin_b.id), additional_claims={"role": "ADMIN", "empresa_id": self.empresa_b.id})

    def tearDown(self):
        db_session.remove()
        self.app_context.pop()

    def test_list_usuarios_isolation(self):
        # Company A admin lists users
        headers = {"Authorization": f"Bearer {self.admin_a_token}"}
        response = self.client.get("/usuarios/", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 2)
        emails = [u["email"] for u in data]
        self.assertIn("admina@test.com", emails)
        self.assertIn("usera@test.com", emails)
        self.assertNotIn("adminb@test.com", emails) # Company B user must not be listed

    def test_create_usuario_authorization(self):
        # Regular USER tries to create a user -> should fail with 403
        headers = {"Authorization": f"Bearer {self.user_a_token}"}
        payload = {
            "nombre": "Nuevo User",
            "email": "nuevo@test.com",
            "password": "password123",
            "rol": "USER"
        }
        response = self.client.post("/usuarios/", json=payload, headers=headers)
        self.assertEqual(response.status_code, 403)

        # ADMIN creates a user -> should succeed
        admin_headers = {"Authorization": f"Bearer {self.admin_a_token}"}
        response = self.client.post("/usuarios/", json=payload, headers=admin_headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["email"], "nuevo@test.com")
        self.assertEqual(response.json["empresa_id"], self.empresa_a.id)

    def test_get_usuario_details(self):
        # Querying own company user details -> succeeds
        headers = {"Authorization": f"Bearer {self.user_a_token}"}
        response = self.client.get(f"/usuarios/{self.admin_a.id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["email"], "admina@test.com")

        # Querying another company user details -> fails with 403
        response = self.client.get(f"/usuarios/{self.admin_b.id}", headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_update_usuario(self):
        headers = {"Authorization": f"Bearer {self.user_a_token}"}
        payload = {"nombre": "User A Modificado"}
        
        # User modifies themselves -> succeeds
        response = self.client.put(f"/usuarios/{self.user_a.id}", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["nombre"], "User A Modificado")

        # User tries to modify admin -> fails with 403
        response = self.client.put(f"/usuarios/{self.admin_a.id}", json=payload, headers=headers)
        self.assertEqual(response.status_code, 403)

        # Admin modifies user -> succeeds
        admin_headers = {"Authorization": f"Bearer {self.admin_a_token}"}
        response = self.client.put(f"/usuarios/{self.user_a.id}", json={"rol": "ADMIN"}, headers=admin_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["rol"], "ADMIN")

    def test_delete_usuario(self):
        admin_headers = {"Authorization": f"Bearer {self.admin_a_token}"}
        
        # Admin tries to delete themselves -> fails with 400
        response = self.client.delete(f"/usuarios/{self.admin_a.id}", headers=admin_headers)
        self.assertEqual(response.status_code, 400)

        # Admin deletes regular user -> succeeds
        response = self.client.delete(f"/usuarios/{self.user_a.id}", headers=admin_headers)
        self.assertEqual(response.status_code, 200)

        # Regular user tries to delete -> fails with 403
        user_headers = {"Authorization": f"Bearer {self.user_a_token}"}
        response = self.client.delete(f"/usuarios/{self.admin_a.id}", headers=user_headers)
        self.assertEqual(response.status_code, 403)
