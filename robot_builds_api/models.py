from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    role = db.Column(db.String(20), nullable=False, server_default="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


BUILD_STAGES = ("Planned", "Building", "Testing", "Complete")


class RobotBuild(db.Model):
    __tablename__ = "robot_builds"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    stage = db.Column(db.String(20), nullable=False, server_default="Planned")
    description = db.Column(db.Text)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
