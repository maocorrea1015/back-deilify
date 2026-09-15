from marshmallow import Schema, fields, validate, validates, ValidationError
from sqlalchemy import select
from ..extensions import db_session
from ..models.usuario import Usuario
from ..models.empresa import Empresa

class UsuarioRegistroSchema(Schema):
    nombre = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True, validate=validate.Length(max=120))
    password = fields.Str(required=True, validate=validate.Length(min=6, max=50))
    rol = fields.Str(validate=validate.OneOf(["ADMIN", "USER"]), load_default="USER")
    
    # Can register in existing company
    empresa_id = fields.Int(required=False)
    
    # Or create a new company on registration
    empresa_nombre = fields.Str(required=False, validate=validate.Length(min=2, max=100))
    empresa_nit = fields.Str(required=False, validate=validate.Length(min=2, max=20))

    @validates('email')
    def validate_email(self, value, **kwargs):
        stmt = select(Usuario).where(Usuario.email == value)
        existing = db_session.execute(stmt).scalars().first()
        if existing:
            raise ValidationError("El correo electrónico ya está registrado.")

    @validates('empresa_id')
    def validate_empresa_id(self, value, **kwargs):
        if value is not None:
            stmt = select(Empresa).where(Empresa.id == value)
            existing = db_session.execute(stmt).scalars().first()
            if not existing:
                raise ValidationError("La empresa especificada no existe.")


    # Cross-field validation in schema
    def validate_company_fields(self, data):
        # We need either empresa_id OR (empresa_nombre and empresa_nit)
        emp_id = data.get("empresa_id")
        emp_name = data.get("empresa_nombre")
        emp_nit = data.get("empresa_nit")
        
        if not emp_id and not (emp_name and emp_nit):
            raise ValidationError(
                "Debe proporcionar un 'empresa_id' existente o los datos para crear una nueva empresa ('empresa_nombre' y 'empresa_nit').",
                field_name="_schema"
            )


class UsuarioLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


class EmpresaSchema(Schema):
    id = fields.Int(dump_only=True)
    nombre = fields.Str()
    nit = fields.Str()


class UsuarioResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    nombre = fields.Str()
    email = fields.Str()
    rol = fields.Str()
    empresa_id = fields.Int()
    empresa = fields.Nested(EmpresaSchema, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
