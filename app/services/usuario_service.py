from sqlalchemy import select
from ..extensions import db_session
from ..models.usuario import Usuario

class UsuarioService:
    @staticmethod
    def listar_usuarios(empresa_id):
        stmt = select(Usuario).where(Usuario.empresa_id == empresa_id)
        return db_session.execute(stmt).scalars().all()

    @staticmethod
    def crear_usuario(empresa_id, data):
        # Validar si el email ya está en uso (doble check)
        stmt = select(Usuario).where(Usuario.email == data["email"])
        existing_user = db_session.execute(stmt).scalars().first()
        if existing_user:
            raise ValueError("El correo electrónico ya está registrado.")

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
    def obtener_usuario(empresa_id, user_id):
        stmt = select(Usuario).where(Usuario.id == user_id)
        usuario = db_session.execute(stmt).scalars().first()
        if not usuario:
            raise ValueError("Usuario no encontrado.")
        if usuario.empresa_id != empresa_id:
            raise PermissionError("Acceso denegado. El usuario no pertenece a su empresa.")
        return usuario

    @staticmethod
    def actualizar_usuario(empresa_id, user_id, data, requesting_user_role):
        usuario = UsuarioService.obtener_usuario(empresa_id, user_id)

        if "nombre" in data:
            usuario.nombre = data["nombre"]
        if "email" in data:
            # Validar unicidad
            stmt = select(Usuario).where(Usuario.email == data["email"], Usuario.id != user_id)
            existing_user = db_session.execute(stmt).scalars().first()
            if existing_user:
                raise ValueError("El correo electrónico ya está en uso.")
            usuario.email = data["email"]
        if "password" in data:
            usuario.set_password(data["password"])
        if "rol" in data:
            if requesting_user_role != "ADMIN":
                raise PermissionError("Solo los administradores pueden cambiar roles de usuario.")
            usuario.rol = data["rol"]

        db_session.commit()
        return usuario

    @staticmethod
    def eliminar_usuario(empresa_id, user_id, requesting_user_id):
        usuario = UsuarioService.obtener_usuario(empresa_id, user_id)

        if usuario.id == requesting_user_id:
            raise ValueError("No puede eliminarse a sí mismo.")

        db_session.delete(usuario)
        db_session.commit()
        return True
