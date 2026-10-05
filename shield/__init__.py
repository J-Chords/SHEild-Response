import os
import secrets
from pathlib import Path

import click
from flask import Flask, render_template

from .extensions import csrf, db, login_manager


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    instance_path = Path(app.instance_path)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{instance_path / 'shield.db'}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_TIME_LIMIT=None,
    )

    if test_config:
        app.config.update(test_config)

    instance_path.mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .auth.routes import bp as auth_bp
    from .main.routes import bp as main_bp
    from .reporter.routes import bp as reporter_bp
    from .responder.routes import bp as responder_bp
    from .admin.routes import bp as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(reporter_bp, url_prefix="/reporter")
    app.register_blueprint(responder_bp, url_prefix="/responder")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.context_processor
    def inject_globals():
        from .models import EmergencyContact

        try:
            primary_contact = EmergencyContact.query.filter_by(
                is_primary=True, is_active=True
            ).first()
        except Exception:
            primary_contact = None
        return {"primary_contact": primary_contact}

    from .models import describe_update, update_author_label, update_type_label

    app.jinja_env.globals["describe_update"] = describe_update
    app.jinja_env.globals["update_type_label"] = update_type_label
    app.jinja_env.globals["update_author_label"] = update_author_label

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Create the repeat-safe fictional demonstration dataset."""
        from .seed import seed_database

        db.create_all()
        seed_database()
        click.echo("SHEild Response demo data is ready.")

    @app.cli.command("seed-final-demo")
    def seed_final_demo_command():
        """Create the repeat-safe final defence demonstration dataset."""
        from .final_demo import seed_final_demo
        from .schema import ensure_schema

        db.create_all()
        ensure_schema()
        result = seed_final_demo()
        deactivated = ", ".join(result["legacy"]["deactivated"]) or "none"
        removed = ", ".join(result["legacy"]["removed"]) or "none"
        click.echo("SHEild Response final defence dataset is ready.")
        click.echo(f"Legacy accounts deactivated: {deactivated}")
        click.echo(f"Dependency-free legacy accounts removed: {removed}")
        click.echo(
            "Obsolete unlinked baseline alert removed: "
            f"{'yes' if result['obsolete_alert_removed'] else 'not present'}"
        )
        click.echo(f"Final demo cases ensured: {len(result['case_numbers'])}")
        click.echo(f"Linked SOS alerts ensured: {len(result['alert_numbers'])}")

    with app.app_context():
        from .seed import seed_database
        from .schema import ensure_schema

        db.create_all()
        ensure_schema()
        if not app.config.get("SKIP_SEED"):
            seed_database()

    return app
