import os
from pathlib import Path

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
load_dotenv()
from config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


@jwt.unauthorized_loader
def missing_jwt(_reason):
    return jsonify(error={"code": "AUTHENTICATION_REQUIRED", "message": "Authentication is required"}), 401


@jwt.invalid_token_loader
def invalid_jwt(_reason):
    return jsonify(error={"code": "INVALID_TOKEN", "message": "Token is invalid"}), 401


@jwt.expired_token_loader
def expired_jwt(_jwt_header, _jwt_payload):
    return jsonify(error={"code": "TOKEN_EXPIRED", "message": "Token has expired"}), 401


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    migrations_dir = Path(__file__).resolve().parent.parent / "migrations"
    migrate.init_app(app, db, directory=str(migrations_dir))
    jwt.init_app(app)
    CORS(app, origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","))
    from app.routes import api
    app.register_blueprint(api, url_prefix="/api")
    @app.errorhandler(404)
    def missing(_):
        return jsonify(error={"code":"NOT_FOUND","message":"Resource not found"}), 404

    @app.errorhandler(HTTPException)
    def http_error(error):
        code = "METHOD_NOT_ALLOWED" if error.code == 405 else "HTTP_ERROR"
        return jsonify(error={"code": code, "message": error.description}), error.code

    @app.errorhandler(Exception)
    def internal_error(error):
        app.logger.exception("Unhandled request error: %s", error)
        return jsonify(error={"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}), 500

    return app
