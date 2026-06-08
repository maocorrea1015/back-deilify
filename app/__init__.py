import importlib
import pkgutil

from flask import Flask

from .config import Config
from .extensions import api


def create_app(config_object=None):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_object or Config)

    register_extensions(app)
    register_blueprints(app)
    return app


def register_extensions(app):
    api.init_app(app)


def register_blueprints(app):
    import app.api
    import app.models

    import_submodules(app.api)
    import_submodules(app.models)


def import_submodules(package, recursive=True):
    if not hasattr(package, '__path__'):
        return {}

    results = {}
    package_name = package.__name__
    for finder, name, ispkg in pkgutil.iter_modules(package.__path__):
        full_name = f"{package_name}.{name}"
        module = importlib.import_module(full_name)
        results[full_name] = module
        if recursive and ispkg:
            results.update(import_submodules(module, recursive=recursive))

    return results
