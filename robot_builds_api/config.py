import os


def settings():
    return {
        "SQLALCHEMY_DATABASE_URI": os.getenv(
            "DATABASE_URL", "sqlite:///robot_builds.db"
        ),
        "JWT_SECRET_KEY": os.getenv("JWT_SECRET_KEY"),
        "JWT_ACCESS_LIFETIME_MINUTES": int(
            os.getenv("JWT_ACCESS_LIFETIME_MINUTES", "15")
        ),
    }
