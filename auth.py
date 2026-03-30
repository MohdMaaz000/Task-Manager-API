from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)

from models import db, User
from validators import validate_login_payload, validate_registration_payload

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# -------------------------
# REGISTER
# -------------------------
@auth_bp.route("/register", methods=["POST"])
def register():
    data = validate_registration_payload(request)

    if User.query.filter_by(email=data["email"]).first():
        return {"error": "email already registered"}, 400

    user = User(
        name=data["name"],
        email=data["email"]
    )

    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    return {"message": "user registered"}, 201


# -------------------------
# LOGIN
# -------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = validate_login_payload(request)

    user = User.query.filter_by(email=data["email"]).first()

    if not user or not user.check_password(data["password"]):
        return {"error": "invalid credentials"}, 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )
    refresh_token = create_refresh_token(identity=str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }, 200


# -------------------------
# CURRENT USER
# -------------------------
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def current_user():

    user_id = get_jwt_identity()

    user = User.query.get(user_id)

    if not user:
        return {"error": "user not found"}, 404

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }
