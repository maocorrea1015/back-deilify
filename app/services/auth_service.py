from sqlalchemy import select
from ..extensions import db_session
from ..models.usuario import Usuario
from ..models.empresa import Empresa
from flask_jwt_extended import create_access_token

class AuthService:
    @staticmethod
    def registrar_usuario(data):
        empresa_id = data.get("empresa_id")
        empresa_nombre = data.get("empresa_nombre")
        empresa_nit = data.get("empresa_nit")
        
        if not empresa_id and not (empresa_nombre and empresa_nit):
            raise ValueError(
                "Debe proporcionar un empresa_id existente o los datos para crear una nueva empresa (empresa_nombre y empresa_nit)."
            )
            
        # Crear empresa si no se especificó empresa_id
        if not empresa_id:
            # Validar si ya existe una empresa con ese NIT
            stmt = select(Empresa).where(Empresa.nit == empresa_nit)
            existing_emp = db_session.execute(stmt).scalars().first()
            if existing_emp:
                raise ValueError(f"Ya existe una empresa registrada con el NIT: {empresa_nit}")
                
            empresa = Empresa(nombre=empresa_nombre, nit=empresa_nit)
            db_session.add(empresa)
            db_session.flush()  # Obtener el ID generado antes del commit final
            empresa_id = empresa.id
            
        # Validar si el email ya está en uso
        stmt = select(Usuario).where(Usuario.email == data["email"])
        existing_user = db_session.execute(stmt).scalars().first()
        if existing_user:
            raise ValueError("El correo electrónico ya está registrado.")
            
        # Crear el usuario
        usuario = Usuario(
            nombre=data["nombre"],
            email=data["email"],
            rol=data.get("rol", "USER"),
            empresa_id=empresa_id
        )
        usuario.set_password(data["password"])
        
        db_session.add(usuario)
        db_session.commit()
        return usuario

    @staticmethod
    def login_usuario(email, password):
        stmt = select(Usuario).where(Usuario.email == email)
        usuario = db_session.execute(stmt).scalars().first()
        
        if not usuario or not usuario.check_password(password):
            return None
            
        # Generar token JWT con claims adicionales para multi-tenant y roles
        access_token = create_access_token(
            identity=str(usuario.id),
            additional_claims={
                "role": usuario.rol,
                "empresa_id": usuario.empresa_id
            }
        )
        
        return {
            "usuario": usuario,
            "access_token": access_token
        }
