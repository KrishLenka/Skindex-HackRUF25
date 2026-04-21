"""
Run once to create a test user:
  .venv/bin/python3 seed_user.py
"""
from app import app
from auth import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email="test@dermai.com").first():
        user = User(
            name="Test User",
            email="test@dermai.com",
            password_hash=generate_password_hash("test123"),
            age_group="18-29",
            sex_at_birth="other_or_unspecified",
            fitzpatrick="FST3",
            ethnicity="",
            texture="",
        )
        db.session.add(user)
        db.session.commit()
        print("Test user created.")
    else:
        print("Test user already exists.")

print("Email:    test@dermai.com")
print("Password: test123")
