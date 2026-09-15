from marshmallow import Schema, fields, validate, validates, ValidationError
from sqlalchemy import select
from ..extensions import db_session
from ..models.usuario import Usuario

class UsuarioCreateSchema(Schema):
    nombre = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True, validate=validate.Length(max=120))
    password = fields.Str(required=True, validate=validate.Length(min=6, max=50))
    rol = fields.Str(validate=validate.OneOf(["ADMIN", "USER"]), load_default="USER")

    @validates('email')
    def validate_email(self, value, **kwargs):
        stmt = select(Usuario).where(Usuario.email == value)
        existing = db_session.execute(stmt).scalars().first()
        if existing:
            raise ValidationError("El correo electrónico ya está registrado.")


class UsuarioUpdateSchema(Schema):
    nombre = fields.Str(validate=validate.Length(min=2, max=100))
    email = fields.Email(validate=validate.Length(max=120))
    password = fields.Str(validate=validate.Length(min=6, max=50))
    rol = fields.Str(validate=validate.OneOf(["ADMIN", "USER"]))

    # Pass the user id to context to exclude it when checking for unique email
    @validates('email')
    def validate_email(self, value, **kwargs):
        user_id = self.context.get("user_id")
        stmt = select(Usuario).where(Usuario.email == value)
        if user_id:
            stmt = stmt.where(Usuario.id != user_id)
        existing = db_session.execute(stmt).scalars().first()
        if existing:
            raise ValidationError("El correo electrónico ya está en uso por otro usuario.")
