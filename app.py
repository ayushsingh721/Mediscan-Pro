import os
import shutil
import threading
import webbrowser
from datetime import datetime
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

login_manager = LoginManager()
bcrypt        = Bcrypt()
sess          = Session()
csrf          = CSRFProtect()


def create_app(env=None):

    app = Flask(
        __name__,
        static_folder   = 'static',
        template_folder = 'templates'
    )

    # ── Config ────────────────────────────────────────────────
    from config import config_by_name
    env = env or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(
        config_by_name.get(env, config_by_name['default'])
    )

    # ── Directories ───────────────────────────────────────────
    for d in ['instance', 'instance/sessions',
              'instance/uploads', 'ml_models/saved_models']:
        os.makedirs(d, exist_ok=True)

    # ── Extensions ────────────────────────────────────────────
    from database.db import db

    bcrypt.init_app(app)
    sess.init_app(app)
    db.init_app(app)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view             = 'auth.login'
    login_manager.login_message          = 'Please log in.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from database.db import User
        return User.query.get(int(user_id))

    # ── Database ──────────────────────────────────────────────
    import database.models  # noqa
    with app.app_context():
        db.create_all()

    # ── Blueprints ────────────────────────────────────────────
    from routes.auth_routes       import auth_bp
    from routes.dashboard_routes  import dashboard_bp
    from routes.prediction_routes import prediction_bp

    app.register_blueprint(auth_bp,        url_prefix='/auth')
    app.register_blueprint(dashboard_bp,   url_prefix='/dashboard')
    app.register_blueprint(prediction_bp,  url_prefix='/predict')

    # ── Error handlers ────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # ── Template globals ──────────────────────────────────────
    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        return dict(
            now          = datetime.utcnow(),
            app_name     = 'MediScan Pro',
            app_version  = '1.0.0',
            current_user = current_user,
            enumerate    = enumerate,
        )

    # ── Template filters ──────────────────────────────────────
    from utils.helpers import register_template_filters
    register_template_filters(app)

    # ── Home route ────────────────────────────────────────────
    @app.route('/')
    def home():
        # Always show home page — navbar handles dashboard link
        return render_template('index.html')

    return app


# ── Entry point ───────────────────────────────────────────────
if __name__ == '__main__':

    application = create_app()

    # Clear sessions on every restart
    # This means no user is auto-logged in when server starts
    session_dir = os.path.join('instance', 'sessions')
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)
        os.makedirs(session_dir, exist_ok=True)
        print("✓ Sessions cleared")

    # Open browser automatically after 1.5 seconds
    def open_browser():
        webbrowser.open('http://127.0.0.1:5000/')

    threading.Timer(1.5, open_browser).start()

    print("✓ Starting MediScan Pro...")
    print("✓ Opening http://127.0.0.1:5000/")

    application.run(
        host  = '127.0.0.1',
        port  = 5000,
        debug = False
    )