from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from ...services.usuario_service import UsuarioService
from ...schemas.usuarios import UsuarioCreateSchema, UsuarioUpdateSchema
from ...schemas.auth import UsuarioResponseSchema
from ...middleware.tenant import get_empresa_id_from_jwt

ns = Namespace('usuarios', description='Administración de Usuarios de la Empresa', security='apikey')

# Modelos Swagger para documentación
usuario_create_model = ns.model('UsuarioCreate', {
    'nombre': fields.String(required=True, description='Nombre del usuario'),
    'email': fields.String(required=True, description='Correo electrónico'),
    'password': fields.String(required=True, description='Contraseña (mínimo 6 caracteres)'),
    'rol': fields.String(description='Rol: ADMIN o USER', default='USER')
})

usuario_update_model = ns.model('UsuarioUpdate', {
    'nombre': fields.String(description='Nombre del usuario'),
    'email': fields.String(description='Correo electrónico'),
    'password': fields.String(description='Contraseña'),
    'rol': fields.String(description='Rol: ADMIN o USER')
})


@ns.route('/')
class UsuarioListResource(Resource):
    @jwt_required()
    @ns.doc('listar_usuarios_empresa')
    def get(self):
        """Listar todos los usuarios de la empresa"""
        empresa_id = get_empresa_id_from_jwt()
        usuarios = UsuarioService.listar_usuarios(empresa_id)
        schema = UsuarioResponseSchema(many=True)
        return schema.dump(usuarios), 200

    @jwt_required()
    @ns.expect(usuario_create_model)
    def post(self):
        """Crear un nuevo usuario dentro de la empresa (Requiere rol ADMIN)"""
        claims = get_jwt()
        if claims.get("role") != "ADMIN":
            return {"error": "Solo los administradores pueden crear usuarios en la empresa."}, 403

        empresa_id = get_empresa_id_from_jwt()
        data = request.json
        if not data:
            return {"error": "Datos no proporcionados"}, 400

        schema = UsuarioCreateSchema()
        errors = schema.validate(data)
        if errors:
            return errors, 400

        try:
            usuario = UsuarioService.crear_usuario(empresa_id, data)
            res_schema = UsuarioResponseSchema()
            return res_schema.dump(usuario), 201
        except ValueError as e:
            return {"error": str(e)}, 400


@ns.route('/<int:id>')
@ns.param('id', 'ID del usuario')
class UsuarioResource(Resource):
    @jwt_required()
    def get(self, id):
        """Obtener detalles de un usuario de la empresa"""
        empresa_id = get_empresa_id_from_jwt()
        try:
            usuario = UsuarioService.obtener_usuario(empresa_id, id)
            schema = UsuarioResponseSchema()
            return schema.dump(usuario), 200
        except PermissionError as e:
            return {"error": str(e)}, 403
        except ValueError as e:
            return {"error": str(e)}, 404

    @jwt_required()
    @ns.expect(usuario_update_model)
    def put(self, id):
        """Actualizar datos de un usuario de la empresa (ADMIN, o el propio usuario)"""
        claims = get_jwt()
        empresa_id = get_empresa_id_from_jwt()
        current_user_id = int(get_jwt_identity())

        # Solo el propio usuario o un administrador de la empresa pueden modificarlo
        if claims.get("role") != "ADMIN" and current_user_id != id:
            return {"error": "No tiene permisos para modificar este usuario."}, 403

        data = request.json
        if not data:
            return {"error": "Datos no proporcionados"}, 400

        schema = UsuarioUpdateSchema()
        schema.context = {"user_id": id}


        errors = schema.validate(data)
        if errors:
            return errors, 400

        try:
            usuario = UsuarioService.actualizar_usuario(
                empresa_id=empresa_id,
                user_id=id,
                data=data,
                requesting_user_role=claims.get("role")
            )
            schema_res = UsuarioResponseSchema()
            return schema_res.dump(usuario), 200
        except PermissionError as e:
            return {"error": str(e)}, 403
        except ValueError as e:
            return {"error": str(e)}, 400

    @jwt_required()
    def delete(self, id):
        """Eliminar un usuario de la empresa (Requiere rol ADMIN)"""
        claims = get_jwt()
        if claims.get("role") != "ADMIN":
            return {"error": "Solo los administradores pueden eliminar usuarios de la empresa."}, 403

        empresa_id = get_empresa_id_from_jwt()
        current_user_id = int(get_jwt_identity())

        try:
            UsuarioService.eliminar_usuario(
                empresa_id=empresa_id,
                user_id=id,
                requesting_user_id=current_user_id
            )
            return {"message": "Usuario eliminado correctamente"}, 200
        except PermissionError as e:
            return {"error": str(e)}, 403
        except ValueError as e:
            return {"error": str(e)}, 400
