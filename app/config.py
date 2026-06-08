import os


class Config:
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    RESTX_MASK_SWAGGER = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
