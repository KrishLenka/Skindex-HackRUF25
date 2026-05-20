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
    """Represents a registered user in the database.

    Attributes:
        id (int): Primary key.
        name (str): Full name of the user.
        email (str): Unique email address used for login.
        password_hash (str): Securely hashed password.
        age_group (str, optional): Demographic age demographic (e.g., "18-29").
        sex_at_birth (str, optional): Demographic sex at birth.
        fitzpatrick (str, optional): Demographic Fitzpatrick skin type.
        ethnicity (str, optional): Demographic ethnicity.
        texture (str, optional): Demographic skin texture.
        created_at (datetime.datetime): Timestamp of account creation.
    """
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
        """Serializes the user instance to a dictionary.

        Returns:
            dict: A dictionary representation of the user's demographic and account data.
        """
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
    """Represents a skin condition scan submitted by a user.

    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key linking to the User.
        created_at (datetime.datetime): Timestamp when the scan was uploaded.
        body_part (str, optional): The body part scanned.
        symptoms_json (str, optional): JSON string list of symptoms.
        description (str, optional): Free-text description provided by the user.
        image_b64 (str, optional): Base64 encoded image data string.
        condition (str, optional): Evaluated primary skin condition.
        confidence (float, optional): Model confidence score.
        severity (str, optional): Severity rating.
        recommendations_json (str, optional): JSON string list of recommendations.
    """
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
        """Returns a lightweight representation of the scan for list views.

        Ony includes summary metadata, omitting the heavy `image_b64` string.

        Returns:
            dict: Summary dictionary of the scan.
        """
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
        """Returns a full representation of the scan including image data.

        Returns:
            dict: Detailed dictionary of the scan.
        """
        d = self.to_summary()
        d["description"]     = self.description
        d["image_b64"]       = self.image_b64
        d["recommendations"] = json.loads(self.recommendations_json) if self.recommendations_json else []
        return d


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def _issue_token(user_id: int) -> str:
    """Issues a JSON Web Token (JWT) for a specific user.

    Args:
        user_id (int): The ID of the authenticated user.

    Returns:
        str: Encoded JWT string expiring in 7 days.
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def token_required(f):
    """Decorator that validates a Bearer JWT in the request headers.

    If valid, it injects the `current_user` User object into the wrapped route.

    Args:
        f (callable): The route function to wrap.

    Returns:
        callable: The wrapped function or a 401 JSON error response.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        """Wrapper function that performs the JWT validation and user injection."""
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
    """Registers a new user account.

    Expects JSON payload with `name`, `email`, and `password`.

    Returns:
        tuple[Response, int]: JSON response with a token and user dict, and 201 status,
                              or JSON error message with 400/409 status.
    """
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
    """Authenticates a user and issues a JWT session token.

    Expects JSON payload with `email` and `password`.

    Returns:
        tuple[Response, int]: JSON response with `token` and `user` data, or a 401/400 error.
    """
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
    """Fetches the currently authenticated user's profile information.

    Args:
        current_user (User): The authenticated User object (injected).

    Returns:
        Response: JSON representation of the current user.
    """
    return jsonify({"user": current_user.to_dict()})


@auth_bp.route("/auth/profile", methods=["PUT"])
@token_required
def update_profile(current_user):
    """Updates the demographic profile of the authenticated user.

    Expects an optional JSON payload with profile fields (e.g., `age_group`, `ethnicity`).

    Args:
        current_user (User): The authenticated User object (injected).

    Returns:
        Response: JSON representation of the updated user.
    """
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
    """Creates a new scan record for the user.

    Args:
        current_user (User): The authenticated User object (injected).

    Returns:
        tuple[Response, int]: JSON response of the created scan summary and a 201 status code.
    """
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
    """Lists all scans associated with the authenticated user.

    Args:
        current_user (User): The authenticated User object (injected).

    Returns:
        Response: JSON array of scan summaries (omitting full image base64 data).
    """
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
    """Retrieves full details of a specific scan, including the image data.

    Args:
        current_user (User): The authenticated User object (injected).
        scan_id (int): The database ID of the scan.

    Returns:
        tuple[Response, int]: JSON representation of the detailed scan, or a 404 error if not found.
    """
    scan = Scan.query.filter_by(id=scan_id, user_id=current_user.id).first()
    if not scan:
        return jsonify({"error": "Scan not found"}), 404
    return jsonify({"scan": scan.to_dict()})


@auth_bp.route("/scans/<int:scan_id>", methods=["DELETE"])
@token_required
def delete_scan(current_user, scan_id):
    """Deletes a specific scan belonging to the user from the database.

    Args:
        current_user (User): The authenticated User object (injected).
        scan_id (int): The database ID of the scan to delete.

    Returns:
        tuple[Response, int]: JSON `{ok: True}` on success, or a 404 error if not found.
    """
    scan = Scan.query.filter_by(id=scan_id, user_id=current_user.id).first()
    if not scan:
        return jsonify({"error": "Scan not found"}), 404
    db.session.delete(scan)
    db.session.commit()
    return jsonify({"ok": True})
