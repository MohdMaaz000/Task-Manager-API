from datetime import date

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_migrate import Migrate
from flask_limiter.errors import RateLimitExceeded
from sqlalchemy import event, func
from sqlalchemy.engine import Engine
from werkzeug.exceptions import BadRequest

from auth import auth_bp
from config import Config
from limiter import limiter
from logger import logger
from models import ActivityLog, Task, User, db
from tasks import tasks_bp
from validators import validate_login_payload, validate_registration_payload


@event.listens_for(Engine, "connect")
def configure_sqlite(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=MEMORY")
    cursor.close()


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    logger.setLevel(app.config["LOG_LEVEL"])

    cors_origins = app.config["CORS_ORIGINS"]
    if cors_origins == "*":
        CORS(app)
    else:
        origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
        CORS(app, resources={r"/*": {"origins": origins}})

    db.init_app(app)
    Migrate(app, db)
    jwt = JWTManager(app)
    limiter.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)

    register_request_logging(app)
    register_error_handlers(app)
    register_jwt_handlers(jwt)
    register_routes(app)

    if app.config["CREATE_DB_ON_STARTUP"]:
        with app.app_context():
            db.create_all()

    logger.info("Task Manager API started")
    return app


def register_request_logging(app):
    @app.before_request
    def log_request():
        logger.info("%s %s", request.method, request.path)


def register_error_handlers(app):
    @app.errorhandler(BadRequest)
    def bad_request(error):
        return {"error": "invalid request"}, 400

    @app.errorhandler(404)
    def not_found(error):
        return {"error": "resource not found"}, 404

    @app.errorhandler(RateLimitExceeded)
    def rate_limit_exceeded(error):
        return {"error": "rate limit exceeded"}, 429

    @app.errorhandler(500)
    def server_error(error):
        logger.exception("Unhandled server error: %s", error)
        return {"error": "internal server error"}, 500


def register_jwt_handlers(jwt):
    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        return {"error": "authorization required"}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return {"error": "invalid token"}, 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {"error": "token has expired"}, 401


def register_routes(app):
    @app.route("/")
    def home():
        return {"status": "API running"}

    @app.route("/health", methods=["GET"])
    def health_check():
        return {
            "status": "ok",
            "service": "task-manager-api"
        }, 200

    @app.route("/register", methods=["POST"])
    def register():
        data = validate_registration_payload(request)

        if User.query.filter_by(email=data["email"]).first():
            return {"msg": "Email already registered"}, 400

        user = User(
            name=data["name"],
            email=data["email"],
            role="user"
        )
        user.set_password(data["password"])

        db.session.add(user)
        db.session.commit()

        return {"msg": "User registered"}, 201

    @app.route("/login", methods=["POST"])
    @limiter.limit("5 per minute")
    def login():
        data = validate_login_payload(request)
        user = User.query.filter_by(email=data["email"]).first()

        if not user or not user.check_password(data["password"]):
            return {"msg": "Invalid credentials"}, 401

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role}
        )
        refresh_token = create_refresh_token(identity=str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    @app.route("/refresh", methods=["POST"])
    @jwt_required(refresh=True)
    def refresh():
        identity = get_jwt_identity()
        new_token = create_access_token(identity=identity)
        return {"access_token": new_token}

    @app.route("/admin/users", methods=["GET"])
    @jwt_required()
    def get_users():
        claims = get_jwt()

        if claims.get("role") != "admin":
            return {"msg": "Admin access required"}, 403

        users = User.query.all()
        return jsonify([
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role
            } for user in users
        ])

    @app.route("/dashboard", methods=["GET"])
    @jwt_required()
    def dashboard():
        user_id = int(get_jwt_identity())

        total = Task.query.filter_by(
            user_id=user_id,
            is_deleted=False
        ).count()
        completed = Task.query.filter_by(
            user_id=user_id,
            completed=True,
            is_deleted=False
        ).count()
        overdue = Task.query.filter(
            Task.user_id == user_id,
            Task.completed.is_(False),
            Task.is_deleted.is_(False),
            Task.due_date.is_not(None),
            Task.due_date < date.today()
        ).count()
        priority_stats = db.session.query(
            Task.priority,
            func.count(Task.id)
        ).filter(
            Task.user_id == user_id,
            Task.is_deleted.is_(False)
        ).group_by(Task.priority).all()

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "overdue_tasks": overdue,
            "completion_rate": round((completed / total) * 100, 2) if total > 0 else 0,
            "priority_distribution": {priority: count for priority, count in priority_stats}
        }


def log_action(user_id, action):
    log = ActivityLog(user_id=user_id, action=action)
    db.session.add(log)
    db.session.commit()


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
