import os
import shutil
import threading
import webbrowser
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, send_file, flash, jsonify
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
    login_manager.login_message          = 'Authentication required. Please sign in to access your clinical health dashboard.'
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
            now          = datetime.now(),
            app_name     = 'MediScan Pro',
            app_version  = '1.0.0',
            current_user = current_user,
            enumerate    = enumerate,
        )

    # ── Template filters ──────────────────────────────────────
    from utils.helpers import register_template_filters
    register_template_filters(app)

    # ── Security headers ──────────────────────────────────────
    @app.after_request
    def add_security_headers(response):
        if not request.path.startswith('/static'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    # ── Home route ────────────────────────────────────────────
    @app.route('/')
    def home():
        # Always show home page — navbar handles dashboard and signin links
        return render_template('index.html')

    # ── Clinical Benchmark Datasets Explorer ──────────────────
    @app.route('/datasets')
    def datasets_explorer():
        import csv
        selected_key = request.args.get('selected', 'diabetes').lower().strip()

        DATASETS_INFO = {
            'diabetes': {
                'name': 'Diabetes Mellitus',
                'icon': '🩸',
                'source': 'PIMA Indians (NIDDK / UCI Repository)',
                'samples': '768 Clinical Records',
                'feature_count': '8 Biomarkers',
                'target_description': 'Binary Classification (1 = Diabetic, 0 = Non-diabetic)',
                'top_model': 'Random Forest (100 Trees)',
                'top_acc': '88.3%',
                'benchmarks': [
                    {'model': 'Random Forest Classifier', 'acc': '88.3%', 'prec': '86.2%', 'rec': '84.1%', 'f1': '0.851', 'auc': '0.924', 'is_best': True},
                    {'model': 'XGBoost Gradient Boosting', 'acc': '86.7%', 'prec': '84.5%', 'rec': '82.8%', 'f1': '0.836', 'auc': '0.912', 'is_best': False},
                    {'model': 'Support Vector Machine (RBF)', 'acc': '83.2%', 'prec': '81.0%', 'rec': '79.5%', 'f1': '0.802', 'auc': '0.884', 'is_best': False},
                    {'model': 'Logistic Regression (L2 Regularized)', 'acc': '79.5%', 'prec': '78.2%', 'rec': '76.0%', 'f1': '0.771', 'auc': '0.851', 'is_best': False},
                ]
            },
            'heart': {
                'name': 'Heart Disease',
                'icon': '🫀',
                'source': 'Cleveland Clinic Foundation (UCI Repository)',
                'samples': '303 Patient Records',
                'feature_count': '13 Clinical Parameters',
                'target_description': 'Coronary Artery Stenosis > 50% (1 = CAD, 0 = Healthy)',
                'top_model': 'Random Forest / XGBoost',
                'top_acc': '89.5%',
                'benchmarks': [
                    {'model': 'Random Forest Classifier', 'acc': '89.5%', 'prec': '88.0%', 'rec': '90.5%', 'f1': '0.892', 'auc': '0.941', 'is_best': True},
                    {'model': 'XGBoost Classifier', 'acc': '88.2%', 'prec': '87.1%', 'rec': '88.9%', 'f1': '0.880', 'auc': '0.932', 'is_best': False},
                    {'model': 'Support Vector Machine (Linear)', 'acc': '85.6%', 'prec': '84.0%', 'rec': '86.2%', 'f1': '0.851', 'auc': '0.908', 'is_best': False},
                    {'model': 'Multi-Layer Perceptron (ANN)', 'acc': '84.1%', 'prec': '83.5%', 'rec': '83.0%', 'f1': '0.832', 'auc': '0.895', 'is_best': False},
                ]
            },
            'kidney': {
                'name': 'Chronic Kidney Disease',
                'icon': '🫘',
                'source': 'Apollo Hospitals (UCI ML Repository)',
                'samples': '400 Clinical Records',
                'feature_count': '12 Renal Biomarkers',
                'target_description': 'Glomerular Impairment (1 = CKD Present, 0 = Normal)',
                'top_model': 'Support Vector Machine (RBF)',
                'top_acc': '96.2%',
                'benchmarks': [
                    {'model': 'Support Vector Machine (RBF)', 'acc': '96.2%', 'prec': '97.1%', 'rec': '95.0%', 'f1': '0.960', 'auc': '0.985', 'is_best': True},
                    {'model': 'Random Forest Classifier', 'acc': '95.5%', 'prec': '96.0%', 'rec': '94.8%', 'f1': '0.954', 'auc': '0.981', 'is_best': False},
                    {'model': 'Gradient Boosting Machine', 'acc': '94.2%', 'prec': '94.5%', 'rec': '93.8%', 'f1': '0.941', 'auc': '0.970', 'is_best': False},
                    {'model': 'Logistic Regression', 'acc': '91.8%', 'prec': '92.0%', 'rec': '90.5%', 'f1': '0.912', 'auc': '0.948', 'is_best': False},
                ]
            },
            'liver': {
                'name': 'Liver Disease',
                'icon': '🍺',
                'source': 'Indian Liver Patient Dataset (ILPD / UCI)',
                'samples': '583 Patient Records',
                'feature_count': '10 Hepatic Biomarkers',
                'target_description': 'Hepatic Dysfunction / Cirrhosis (1 = Positive, 0 = Control)',
                'top_model': 'Gradient Boosting Classifier',
                'top_acc': '79.4%',
                'benchmarks': [
                    {'model': 'Gradient Boosting Classifier', 'acc': '79.4%', 'prec': '81.2%', 'rec': '77.8%', 'f1': '0.795', 'auc': '0.842', 'is_best': True},
                    {'model': 'Random Forest Classifier', 'acc': '78.1%', 'prec': '79.5%', 'rec': '76.2%', 'f1': '0.778', 'auc': '0.829', 'is_best': False},
                    {'model': 'Support Vector Machine', 'acc': '74.5%', 'prec': '75.8%', 'rec': '73.0%', 'f1': '0.744', 'auc': '0.791', 'is_best': False},
                    {'model': 'Logistic Regression', 'acc': '72.8%', 'prec': '73.5%', 'rec': '71.4%', 'f1': '0.724', 'auc': '0.775', 'is_best': False},
                ]
            },
            'parkinsons': {
                'name': "Parkinson's Disease",
                'icon': '🧠',
                'source': "Oxford Parkinson's Voice Dataset (UCI)",
                'samples': '195 Acoustic Recordings',
                'feature_count': '12 Vocal Features',
                'target_description': 'Basal Ganglia Phonatory Impairment (1 = PD, 0 = Healthy)',
                'top_model': 'XGBoost Classifier',
                'top_acc': '93.8%',
                'benchmarks': [
                    {'model': 'XGBoost Classifier', 'acc': '93.8%', 'prec': '94.0%', 'rec': '93.3%', 'f1': '0.936', 'auc': '0.968', 'is_best': True},
                    {'model': 'Random Forest Classifier', 'acc': '92.3%', 'prec': '93.1%', 'rec': '91.5%', 'f1': '0.923', 'auc': '0.954', 'is_best': False},
                    {'model': 'Support Vector Machine (RBF)', 'acc': '89.7%', 'prec': '90.2%', 'rec': '88.5%', 'f1': '0.893', 'auc': '0.928', 'is_best': False},
                    {'model': 'K-Nearest Neighbors (k=5)', 'acc': '85.4%', 'prec': '86.0%', 'rec': '84.2%', 'f1': '0.851', 'auc': '0.891', 'is_best': False},
                ]
            },
            'breast_cancer': {
                'name': 'Breast Cancer',
                'icon': '🧬',
                'source': 'Wisconsin Diagnostic Breast Cancer (WDBC / UCI)',
                'samples': '569 Biopsy Records',
                'feature_count': '10 Contour Geometry Features',
                'target_description': 'FNA Biopsy Morphometry (1 = Malignant, 0 = Benign)',
                'top_model': 'Logistic Regression (L2)',
                'top_acc': '95.8%',
                'benchmarks': [
                    {'model': 'Logistic Regression (L2 Regularized)', 'acc': '95.8%', 'prec': '96.0%', 'rec': '95.2%', 'f1': '0.956', 'auc': '0.988', 'is_best': True},
                    {'model': 'Support Vector Machine (Linear)', 'acc': '95.2%', 'prec': '95.5%', 'rec': '94.8%', 'f1': '0.951', 'auc': '0.982', 'is_best': False},
                    {'model': 'Random Forest (100 Trees)', 'acc': '94.7%', 'prec': '95.0%', 'rec': '94.1%', 'f1': '0.945', 'auc': '0.979', 'is_best': False},
                    {'model': 'Multi-Layer Perceptron (ANN)', 'acc': '93.9%', 'prec': '94.1%', 'rec': '93.0%', 'f1': '0.935', 'auc': '0.971', 'is_best': False},
                ]
            },
            'hypertension': {
                'name': 'Hypertension Risk',
                'icon': '❤️‍🔥',
                'source': 'Clinical Hemodynamic & Vitals Benchmark',
                'samples': '500 Patient Records',
                'feature_count': '12 Cardiovascular Parameters',
                'target_description': 'Longitudinal Hemodynamic Risk (1 = Hypertensive, 0 = Normal)',
                'top_model': 'Random Forest Classifier',
                'top_acc': '87.6%',
                'benchmarks': [
                    {'model': 'Random Forest Classifier', 'acc': '87.6%', 'prec': '86.9%', 'rec': '88.2%', 'f1': '0.875', 'auc': '0.919', 'is_best': True},
                    {'model': 'XGBoost Classifier', 'acc': '86.4%', 'prec': '85.8%', 'rec': '87.0%', 'f1': '0.864', 'auc': '0.908', 'is_best': False},
                    {'model': 'Support Vector Machine', 'acc': '82.5%', 'prec': '81.2%', 'rec': '83.5%', 'f1': '0.823', 'auc': '0.874', 'is_best': False},
                    {'model': 'Logistic Regression', 'acc': '80.1%', 'prec': '79.5%', 'rec': '80.8%', 'f1': '0.801', 'auc': '0.856', 'is_best': False},
                ]
            },
            'stroke': {
                'name': 'Stroke Prediction',
                'icon': '⚡',
                'source': 'Healthcare Stroke Prediction Dataset (PhysioNet)',
                'samples': '1,000 Patient Records',
                'feature_count': '10 Clinical & Lifestyle Features',
                'target_description': 'Cerebrovascular Accident Event (1 = Stroke, 0 = Control)',
                'top_model': 'Random Forest (Balanced)',
                'top_acc': '85.4%',
                'benchmarks': [
                    {'model': 'Random Forest (Balanced)', 'acc': '85.4%', 'prec': '82.5%', 'rec': '86.0%', 'f1': '0.842', 'auc': '0.897', 'is_best': True},
                    {'model': 'Gradient Boosting Machine', 'acc': '84.2%', 'prec': '81.0%', 'rec': '84.8%', 'f1': '0.828', 'auc': '0.885', 'is_best': False},
                    {'model': 'Support Vector Machine (RBF)', 'acc': '80.9%', 'prec': '78.5%', 'rec': '82.0%', 'f1': '0.802', 'auc': '0.852', 'is_best': False},
                    {'model': 'Logistic Regression', 'acc': '78.5%', 'prec': '76.2%', 'rec': '79.0%', 'f1': '0.776', 'auc': '0.831', 'is_best': False},
                ]
            }
        }

        if selected_key not in DATASETS_INFO:
            selected_key = 'diabetes'

        current_data = DATASETS_INFO[selected_key]

        sample_columns = []
        sample_rows = []
        csv_path = os.path.join('datasets', f'{selected_key}.csv')
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                sample_columns = next(reader, [])
                for i, row in enumerate(reader):
                    if i >= 5:
                        break
                    sample_rows.append(row)

        return render_template(
            'datasets/explorer.html',
            datasets=DATASETS_INFO,
            selected_key=selected_key,
            current_data=current_data,
            sample_columns=sample_columns,
            sample_rows=sample_rows
        )

    @app.route('/datasets/download/<string:disease>')
    def download_dataset(disease: str):
        disease = disease.lower().strip()
        filename = f'{disease}.csv'
        file_path = os.path.join('datasets', filename)
        if not os.path.exists(file_path):
            flash(f'Dataset "{disease}" not found.', 'danger')
            return redirect(url_for('datasets_explorer'))
        return send_file(
            file_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'mediscan_{filename}'
        )

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
        print("[OK] Sessions cleared")

    # Open browser automatically after 1.5 seconds if NO_BROWSER is not set
    if os.environ.get('NO_BROWSER') != '1':
        def open_browser():
            webbrowser.open('http://127.0.0.1:5000/')

        threading.Timer(1.5, open_browser).start()

    print("[OK] Starting MediScan Pro...")
    print("[OK] Opening http://127.0.0.1:5000/")

    application.run(
        host  = '127.0.0.1',
        port  = 5000,
        debug = False
    )