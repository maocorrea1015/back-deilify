from flask_restx import Api
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

api = Api(
    title="Deilify Backend",
    version="1.0",
    description="API para Gestión de Cartera SaaS Multi-tenant",
)

Base = declarative_base()

# La sesión se vinculará al motor en la inicialización de la app
db_session = scoped_session(sessionmaker())
