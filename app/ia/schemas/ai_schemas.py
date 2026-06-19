from marshmallow import Schema, fields

class AIModelSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    version = fields.Str(dump_only=True)
    algorithm = fields.Str(dump_only=True)
    accuracy = fields.Float(dump_only=True)
    precision = fields.Float(dump_only=True)
    recall = fields.Float(dump_only=True)
    f1_score = fields.Float(dump_only=True)
    roc_auc = fields.Float(dump_only=True)
    model_path = fields.Str(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

class PredictionLogSchema(Schema):
    id = fields.Int(dump_only=True)
    client_id = fields.Int(dump_only=True)
    model_id = fields.Int(dump_only=True)
    prediction = fields.Float(dump_only=True)
    risk_score = fields.Int(dump_only=True)
    probability = fields.Float(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
