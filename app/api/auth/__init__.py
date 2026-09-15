from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import select
from ...services.auth_service import AuthService
from ...schemas.auth import UsuarioRegistroSchema, UsuarioLoginSchema, UsuarioResponseSchema
from ...extensions import db_session
from ...models.usuario import Usuario

ns = Namespace('auth', description='Operaciones de Autenticación y Registro')

# Modelos Swagger para documentación
register_model = ns.model('UsuarioRegistro', {
    'nombre': fields.String(required=True, description='Nombre completo del usuario'),
    'email': fields.String(required=True, description='Correo electrónico'),
    'password': fields.String(required=True, description='Contraseña (mínimo 6 caracteres)'),
    'rol': fields.String(description='Rol del usuario: ADMIN o USER', default='USER'),
    'empresa_id': fields.Integer(description='ID de la empresa (si ya existe)'),
    'empresa_nombre': fields.String(description='Nombre de la empresa a crear (si no existe)'),
    'empresa_nit': fields.String(description='NIT de la empresa a crear (si no existe)')
})

login_model = ns.model('UsuarioLogin', {
    'email': fields.String(required=True, description='Correo electrónico'),
    'password': fields.String(required=True, description='Contraseña')
})

@ns.route('/register')
class RegisterResource(Resource):
    @ns.expect(register_model)
    def post(self):
        """Registro de nuevo usuario (y opcionalmente nueva empresa)"""
        data = request.json
        if not data:
            return {"error": "Datos no proporcionados"}, 400
            
        schema = UsuarioRegistroSchema()
        
        # Validaciones cruzadas de empresa
        try:
            schema.validate_company_fields(data)
        except Exception as e:
            return {"error": str(e)}, 400
            
        # Validación de campos generales
        errors = schema.validate(data)
        if errors:
            return errors, 400
            
        try:
            usuario = AuthService.registrar_usuario(data)
            res_schema = UsuarioResponseSchema()
            return res_schema.dump(usuario), 201
        except ValueError as e:
            return {"error": str(e)}, 400


@ns.route('/login')
class LoginResource(Resource):
    @ns.expect(login_model)
    def post(self):
        """Iniciar sesión y obtener token JWT"""
        data = request.json
        if not data:
            return {"error": "Datos no proporcionados"}, 400
            
        schema = UsuarioLoginSchema()
        errors = schema.validate(data)
        if errors:
            return errors, 400
            
        result = AuthService.login_usuario(data["email"], data["password"])
        if not result:
            return {"error": "Credenciales incorrectas o usuario no encontrado"}, 401
            
        res_schema = UsuarioResponseSchema()
        return {
            "access_token": result["access_token"],
            "usuario": res_schema.dump(result["usuario"])
        }, 200


@ns.route('/me')
class ProfileResource(Resource):
    @jwt_required()
    @ns.doc(security='apikey')
    def get(self):
        """Obtener el perfil del usuario autenticado"""
        try:
            user_id = get_jwt_identity()
            stmt = select(Usuario).where(Usuario.id == int(user_id))
            usuario = db_session.execute(stmt).scalars().first()
            if not usuario:
                return {"error": "Usuario no encontrado"}, 404
                
            res_schema = UsuarioResponseSchema()
            return res_schema.dump(usuario), 200
        except ValueError:
            return {"error": "Formato de token inválido"}, 401
