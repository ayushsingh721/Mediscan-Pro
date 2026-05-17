import json
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, jsonify, session, Response
)
from flask_login import login_required, current_user
from database.db import db, User, PredictionHistory
from utils.helpers import (
    log_activity, sanitize_input,
    format_prediction_for_display,
    get_health_tips, calculate_days_since,
    validate_password_strength
)

dashboard_bp = Blueprint(
    'dashboard', __name__,
    template_folder='../templates/dashboard'
)


# ── Dashboard ─────────────────────────────────────────────────
@dashboard_bp.route('/')
@dashboard_bp.route('/index')
@login_required
def index():
    try:
        user               = User.get_by_id(current_user.id)
        total_predictions  = user.total_predictions
        risk_summary       = PredictionHistory.get_risk_summary(current_user.id)
        disease_stats      = PredictionHistory.get_disease_stats(current_user.id)
        recent_raw         = PredictionHistory.get_by_user(current_user.id, limit=5)
        recent_predictions = [format_prediction_for_display(p) for p in recent_raw]
        last_prediction    = recent_raw[0] if recent_raw else None
        days_since_last    = calculate_days_since(
                                 last_prediction.created_at
                             ) if last_prediction else None
        overall_risk       = last_prediction.risk_level if last_prediction else 'N/A'
        reports_downloaded = session.get('reports_downloaded', 0)
        health_tips        = get_health_tips(count=3)
        disease_modules    = _get_disease_modules()

        return render_template(
            'dashboard/dashboard.html',
            user               = user,
            total_predictions  = total_predictions,
            risk_summary       = risk_summary,
            disease_stats      = disease_stats,
            recent_predictions = recent_predictions,
            days_since_last    = days_since_last,
            overall_risk       = overall_risk,
            reports_downloaded = reports_downloaded,
            health_tips        = health_tips,
            disease_modules    = disease_modules,
            page_title         = 'Dashboard',
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'Dashboard error: {str(e)}', 'danger')
        return redirect(url_for('auth.logout'))


# ── History ───────────────────────────────────────────────────
@dashboard_bp.route('/history')
@login_required
def history():
    page           = request.args.get('page',     1,  type=int)
    per_page       = request.args.get('per_page', 10, type=int)
    disease_filter = request.args.get('disease',  '', type=str)
    risk_filter    = request.args.get('risk',     '', type=str)

    query = PredictionHistory.query.filter_by(user_id=current_user.id)

    if disease_filter:
        query = query.filter(
            PredictionHistory.disease_name.ilike(f'%{disease_filter}%')
        )
    if risk_filter in ['Low', 'Moderate', 'High']:
        query = query.filter_by(risk_level=risk_filter)

    paginated = query.order_by(
        PredictionHistory.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    formatted = [
        format_prediction_for_display(p) for p in paginated.items
    ]

    disease_names = [
        row[0] for row in db.session.query(
            PredictionHistory.disease_name
        ).filter_by(user_id=current_user.id).distinct().all()
    ]

    return render_template(
        'dashboard/history.html',
        predictions    = formatted,
        pagination     = paginated,
        disease_filter = disease_filter,
        risk_filter    = risk_filter,
        disease_names  = disease_names,
        page_title     = 'Prediction History',
    )


# ── Prediction Detail ─────────────────────────────────────────
@dashboard_bp.route('/history/<int:prediction_id>')
@login_required
def prediction_detail(prediction_id):
    prediction = PredictionHistory.get_by_id(
        prediction_id, current_user.id
    )
    if not prediction:
        flash('Prediction not found.', 'warning')
        return redirect(url_for('dashboard.history'))

    return render_template(
        'dashboard/prediction_detail.html',
        prediction = format_prediction_for_display(prediction),
        page_title = f'{prediction.disease_name} — Detail',
    )


# ── Delete Prediction ─────────────────────────────────────────
@dashboard_bp.route(
    '/history/<int:prediction_id>/delete', methods=['POST']
)
@login_required
def delete_prediction(prediction_id):
    prediction = PredictionHistory.get_by_id(
        prediction_id, current_user.id
    )
    if not prediction:
        flash('Record not found.', 'warning')
        return redirect(url_for('dashboard.history'))
    try:
        name = prediction.disease_name
        prediction.delete()
        log_activity(
            current_user.id, 'DELETE_PREDICTION',
            f'Deleted #{prediction_id}'
        )
        flash(f'{name} prediction deleted.', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to delete.', 'danger')
    return redirect(url_for('dashboard.history'))


# ── Profile ───────────────────────────────────────────────────
@dashboard_bp.route('/profile')
@login_required
def profile():
    user               = User.get_by_id(current_user.id)
    total_predictions  = user.total_predictions
    risk_summary       = PredictionHistory.get_risk_summary(current_user.id)
    disease_stats      = PredictionHistory.get_disease_stats(current_user.id)
    recent_raw         = PredictionHistory.get_by_user(current_user.id, limit=5)
    recent_predictions = [format_prediction_for_display(p) for p in recent_raw]

    return render_template(
        'dashboard/profile.html',
        user               = user,
        total_predictions  = total_predictions,
        risk_summary       = risk_summary,
        disease_stats      = disease_stats,
        recent_predictions = recent_predictions,
        page_title         = 'My Profile',
    )


# ── Update Profile ────────────────────────────────────────────
@dashboard_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    first_name = sanitize_input(request.form.get('first_name', ''))
    last_name  = sanitize_input(request.form.get('last_name',  ''))
    age        = request.form.get('age', type=int)
    gender     = sanitize_input(request.form.get('gender', ''))
    phone      = sanitize_input(request.form.get('phone',  ''))

    errors = []
    if not first_name or len(first_name) < 2:
        errors.append('First name must be at least 2 characters.')
    if not last_name or len(last_name) < 2:
        errors.append('Last name must be at least 2 characters.')
    if age and (age < 1 or age > 120):
        errors.append('Age must be between 1 and 120.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('dashboard.profile'))

    try:
        user            = User.get_by_id(current_user.id)
        user.first_name = first_name
        user.last_name  = last_name
        user.age        = age
        user.gender     = gender
        user.phone      = phone
        user.updated_at = datetime.utcnow()
        db.session.commit()
        log_activity(current_user.id, 'PROFILE_UPDATE', 'Updated')
        flash('Profile updated successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to update profile.', 'danger')

    return redirect(url_for('dashboard.profile'))


# ── Change Password ───────────────────────────────────────────
@dashboard_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    from flask_login import logout_user

    current_pw = request.form.get('current_password', '')
    new_pw     = request.form.get('new_password',     '')
    confirm_pw = request.form.get('confirm_password', '')

    errors = []
    if not current_user.check_password(current_pw):
        errors.append('Current password is incorrect.')
    if not new_pw:
        errors.append('New password is required.')
    else:
        check = validate_password_strength(new_pw)
        if not check['valid']:
            errors.append(check['message'])
    if new_pw != confirm_pw:
        errors.append('Passwords do not match.')
    if current_pw == new_pw:
        errors.append('New password must differ from current.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('dashboard.profile'))

    try:
        user            = User.get_by_id(current_user.id)
        user.set_password(new_pw)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        logout_user()
        session.clear()
        flash('Password changed. Please log in again.', 'success')
        return redirect(url_for('auth.login'))
    except Exception:
        db.session.rollback()
        flash('Failed to change password.', 'danger')
        return redirect(url_for('dashboard.profile'))


# ── Download Report ───────────────────────────────────────────
@dashboard_bp.route('/report/<int:prediction_id>/download')
@login_required
def download_report(prediction_id):
    prediction = PredictionHistory.get_by_id(
        prediction_id, current_user.id
    )
    if not prediction:
        flash('Prediction not found.', 'warning')
        return redirect(url_for('dashboard.history'))

    session['reports_downloaded'] = \
        session.get('reports_downloaded', 0) + 1

    try:
        input_data = json.loads(prediction.input_data or '{}')
    except (json.JSONDecodeError, TypeError):
        input_data = {}

    lines = [
        '=' * 60,
        '     MEDISCAN PRO — DISEASE PREDICTION REPORT',
        '=' * 60,
        '',
        f'Patient Name   : {current_user.full_name}',
        f'Email          : {current_user.email}',
        f'Report Date    : {datetime.utcnow().strftime("%B %d, %Y %I:%M %p")} UTC',
        f'Report ID      : RPT-{prediction.id:05d}',
        '',
        '-' * 60,
        'PREDICTION SUMMARY',
        '-' * 60,
        f'Disease Module : {prediction.disease_name}',
        f'Result         : {prediction.result}',
        f'Risk Level     : {prediction.risk_level}',
        f'Confidence     : {prediction.confidence_pct:.1f}%',
        f'Model Used     : {prediction.model_used or "Ensemble"}',
        f'Assessed On    : {prediction.created_at.strftime("%B %d, %Y")}',
        '',
        '-' * 60,
        'INPUT PARAMETERS',
        '-' * 60,
    ]

    for key, value in input_data.items():
        lines.append(f'{key.replace("_"," ").title():<28}: {value}')

    lines += [
        '',
        '-' * 60,
        'PRECAUTIONS',
        '-' * 60,
        prediction.precautions or 'No precautions recorded.',
        '',
        '=' * 60,
        'DISCLAIMER: AI screening tool only.',
        'Not a medical diagnosis.',
        '=' * 60,
    ]

    filename = (
        f"mediscan_{prediction.disease_name.replace(' ', '_')}"
        f"_RPT{prediction.id:05d}.txt"
    )

    return Response(
        '\n'.join(lines),
        mimetype = 'text/plain',
        headers  = {
            'Content-Disposition':
                f'attachment; filename="{filename}"'
        }
    )


# ── Stats AJAX ────────────────────────────────────────────────
@dashboard_bp.route('/stats')
@login_required
def get_stats():
    risk_summary  = PredictionHistory.get_risk_summary(current_user.id)
    disease_stats = PredictionHistory.get_disease_stats(current_user.id)
    return jsonify({
        'success'      : True,
        'risk_summary' : risk_summary,
        'disease_stats': disease_stats,
        'total'        : sum(risk_summary.values()),
    })


# ── Disease Modules ───────────────────────────────────────────
def _get_disease_modules():
    return [
        {
            'name'    : 'Diabetes Mellitus',
            'slug'    : 'diabetes',
            'icon'    : '🩸',
            'accuracy': '91%',
            'url'     : url_for(
                'prediction.predict_form', disease='diabetes'
            ),
        },
        {
            'name'    : 'Heart Disease',
            'slug'    : 'heart',
            'icon'    : '🫀',
            'accuracy': '94%',
            'url'     : url_for(
                'prediction.predict_form', disease='heart'
            ),
        },
        {
            'name'    : "Parkinson's Disease",
            'slug'    : 'parkinsons',
            'icon'    : '🧠',
            'accuracy': '97%',
            'url'     : url_for(
                'prediction.predict_form', disease='parkinsons'
            ),
        },
        {
            'name'    : 'Kidney Disease',
            'slug'    : 'kidney',
            'icon'    : '🩻',
            'accuracy': '96%',
            'url'     : url_for(
                'prediction.predict_form', disease='kidney'
            ),
        },
        {
            'name'    : 'Liver Disease',
            'slug'    : 'liver',
            'icon'    : '🔬',
            'accuracy': '89%',
            'url'     : url_for(
                'prediction.predict_form', disease='liver'
            ),
        },
        {
            'name'    : 'Lung Cancer',
            'slug'    : 'lung_cancer',
            'icon'    : '🫁',
            'accuracy': '93%',
            'url'     : url_for(
                'prediction.predict_form', disease='lung_cancer'
            ),
        },
        {
            'name'    : 'Hypertension',
            'slug'    : 'hypertension',
            'icon'    : '📊',
            'accuracy': '92%',
            'url'     : url_for(
                'prediction.predict_form', disease='hypertension'
            ),
        },
        {
            'name'    : 'Breast Cancer',
            'slug'    : 'breast_cancer',
            'icon'    : '🧬',
            'accuracy': '95%',
            'url'     : url_for(
                'prediction.predict_form', disease='breast_cancer'
            ),
        },
    ]