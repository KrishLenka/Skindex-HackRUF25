"""
auth.py — Flask Blueprint for authentication and user profile management.

Endpoints:
  POST /auth/register   — create account
  POST /auth/login      — authenticate, returns JWT
  GET  /auth/me         — get current user (JWT required)
  PUT  /auth/profile    — update demographic profile (JWT required)
"""

import datetime
import json
from functools import wraps

import jwt
from flask import Blueprint, current_app, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------

class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # Demographic fields
    # Age group: <18 | 18-29 | 30-39 | 40-49 | 50-59 | 60-69 | 70-79 | 80+
    age_group     = db.Column(db.String(10),  nullable=True)
    # Sex at birth: male | female | other_or_unspecified
    sex_at_birth  = db.Column(db.String(30),  nullable=True)
    # Fitzpatrick scale enum
    fitzpatrick   = db.Column(db.String(50),  nullable=True)
    # Ethnicity enum
    ethnicity     = db.Column(db.String(60),  nullable=True)
    # Texture enum
    texture       = db.Column(db.String(40),  nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id":           self.id,
            "name":         self.name,
            "email":        self.email,
            "age_group":    self.age_group,
            "sex_at_birth": self.sex_at_birth,
            "fitzpatrick":  self.fitzpatrick,
            "ethnicity":    self.ethnicity,
            "texture":      self.texture,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Scan model
# ---------------------------------------------------------------------------

class Scan(db.Model):
    __tablename__ = "scans"

    id                   = db.Column(db.Integer, primary_key=True)
    user_id              = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at           = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    body_part            = db.Column(db.String(60),  nullable=True)
    symptoms_json        = db.Column(db.Text, nullable=True)   # JSON array
    description          = db.Column(db.Text, nullable=True)
    image_b64            = db.Column(db.Text, nullable=True)   # data URL stored for detail view
    condition            = db.Column(db.String(120), nullable=True)
    confidence           = db.Column(db.Float,       nullable=True)
    severity             = db.Column(db.String(40),  nullable=True)
    recommendations_json = db.Column(db.Text, nullable=True)   # JSON array

    def to_summary(self):
        """Lightweight representation for list views (no image_b64)."""
        return {
            "id":         self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "body_part":  self.body_part,
            "symptoms":   json.loads(self.symptoms_json) if self.symptoms_json else [],
            "condition":  self.condition,
            "confidence": self.confidence,
            "severity":   self.severity,
        }

    def to_dict(self):
        """Full representation including image data for detail view."""
        d = self.to_summary()
        d["description"]     = self.description
        d["image_b64"]       = self.image_b64
        d["recommendations"] = json.loads(self.recommendations_json) if self.recommendations_json else []
        return d


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def _issue_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def token_required(f):
    """Decorator that validates the Bearer JWT and injects `current_user`."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization token missing"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            current_user = db.session.get(User, payload["user_id"])
            if not current_user:
                return jsonify({"error": "User not found"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired — please log in again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(current_user, *args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Blueprint & routes
# ---------------------------------------------------------------------------

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    data     = request.get_json(silent=True) or {}
    name     = (data.get("name")     or "").strip()
    email    = (data.get("email")    or "").strip().lower()
    password =  data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email, and password are required"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"token": _issue_token(user.id), "user": user.to_dict()}), 201


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data     = request.get_json(silent=True) or {}
    email    = (data.get("email")    or "").strip().lower()
    password =  data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"token": _issue_token(user.id), "user": user.to_dict()})


@auth_bp.route("/auth/me", methods=["GET"])
@token_required
def get_me(current_user):
    return jsonify({"user": current_user.to_dict()})


@auth_bp.route("/auth/profile", methods=["PUT"])
@token_required
def update_profile(current_user):
    data = request.get_json(silent=True) or {}

    allowed = ["name", "age_group", "sex_at_birth", "fitzpatrick", "ethnicity", "texture"]
    for field in allowed:
        if field in data:
            setattr(current_user, field, data[field])

    db.session.commit()
    return jsonify({"user": current_user.to_dict()})


# ---------------------------------------------------------------------------
# Scan endpoints
# ---------------------------------------------------------------------------

@auth_bp.route("/scans", methods=["POST"])
@token_required
def create_scan(current_user):
    data = request.get_json(silent=True) or {}
    scan = Scan(
        user_id=current_user.id,
        body_part=data.get("body_part"),
        symptoms_json=json.dumps(data.get("symptoms", [])),
        description=data.get("description"),
        image_b64=data.get("image_b64"),
        condition=data.get("condition"),
        confidence=data.get("confidence"),
        severity=data.get("severity"),
        recommendations_json=json.dumps(data.get("recommendations", [])),
    )
    db.session.add(scan)
    db.session.commit()
    return jsonify({"scan": scan.to_summary()}), 201


@auth_bp.route("/scans", methods=["GET"])
@token_required
def list_scans(current_user):
    scans = (
        Scan.query
        .filter_by(user_id=current_user.id)
        .order_by(Scan.created_at.desc())
        .all()
    )
    return jsonify({"scans": [s.to_summary() for s in scans]})


@auth_bp.route("/scans/<int:scan_id>", methods=["GET"])
@token_required
def get_scan(current_user, scan_id):
    scan = Scan.query.filter_by(id=scan_id, user_id=current_user.id).first()
    if not scan:
        return jsonify({"error": "Scan not found"}), 404
    return jsonify({"scan": scan.to_dict()})


@auth_bp.route("/scans/<int:scan_id>", methods=["DELETE"])
@token_required
def delete_scan(current_user, scan_id):
    scan = Scan.query.filter_by(id=scan_id, user_id=current_user.id).first()
    if not scan:
        return jsonify({"error": "Scan not found"}), 404
    db.session.delete(scan)
    db.session.commit()
    return jsonify({"ok": True})
