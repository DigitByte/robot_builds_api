import click
from flask.cli import with_appcontext

from .extensions import db
from .models import User


@click.command("promote-admin")
@click.argument("email")
@with_appcontext
def promote_admin(email):
    """Grant administrator access to an existing registered account."""
    user = db.session.scalar(db.select(User).where(User.email == email.strip()))
    if user is None:
        raise click.ClickException("No registered account has that email.")
    user.role = "admin"
    db.session.commit()
    click.echo(f"Administrator access granted to {user.email}.")
