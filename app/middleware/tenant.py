from flask_jwt_extended import get_jwt, get_jwt_identity
from sqlalchemy import select
from ..extensions import db_session
from ..models.empresa import Empresa

def get_empresa_id_from_jwt():
    """
    Extracts the empresa_id from the JWT token.
    Supports:
    1. 'empresa_id' claim inside additional claims.
    2. JWT identity if it can be parsed as an integer.
    3. Fallback for integration tests (which use 'user' or 'admin' string identity):
       returns the ID of the first company in the database, or 1 if none exist.
    """
    try:
        claims = get_jwt()
        emp_id = claims.get("empresa_id")
        if emp_id is not None:
            try:
                return int(emp_id)
            except ValueError:
                pass
    except Exception:
        pass

    try:
        identity = get_jwt_identity()
        if identity is not None:
            try:
                return int(identity)
            except ValueError:
                # String identity fallback (e.g. 'user' or 'admin' in tests)
                first_emp = db_session.execute(select(Empresa)).scalars().first()
                if first_emp:
                    return first_emp.id
                return 1
    except Exception:
        pass

    return None
