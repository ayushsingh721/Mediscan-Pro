# ============================================================
# routes/dashboard_routes.py — MediScan Pro Healthcare Dashboard
# ============================================================

import json
import logging
from datetime import datetime, date
from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, jsonify, session, Response
)
from flask_login import login_required, current_user

from database.db import (
    db, User, UserProfile, PredictionHistory,
    DailyHealthTask, HealthReport
)
from utils.helpers import (
    log_activity, sanitize_input,
    format_prediction_for_display,
    get_health_tips, calculate_days_since,
    validate_password_strength, build_json_response
)
from utils.health_insights import generate_health_insights
from utils.pdf_generator import generate_pdf_report
from utils.ai_health_tips import get_personalized_ai_tip

logger = logging.getLogger('mediscan.dashboard')

dashboard_bp = Blueprint(
    'dashboard', __name__,
    template_folder='../templates/dashboard'
)


# ============================================================
# MAIN HEALTH DASHBOARD
# ============================================================
@dashboard_bp.route('/')
@dashboard_bp.route('/index')
@login_required
def index():
    try:
        user = User.get_by_id(current_user.id)
        if not user.profile:
            profile = UserProfile(user_id=user.id, updated_at=datetime.utcnow())
            profile.save()

        total_predictions  = user.total_predictions
        risk_summary       = PredictionHistory.get_risk_summary(user.id)
        disease_stats      = PredictionHistory.get_disease_stats(user.id)
        recent_raw         = PredictionHistory.get_by_user(user.id, limit=5)
        recent_predictions = [format_prediction_for_display(p) for p in recent_raw]
        last_prediction    = recent_raw[0] if recent_raw else None
        days_since_last    = calculate_days_since(last_prediction.created_at) if last_prediction else None
        overall_risk       = last_prediction.risk_level if last_prediction else 'N/A'
        reports_downloaded = session.get('reports_downloaded', 0)
        health_tips        = get_health_tips(count=3)
        disease_modules    = _get_disease_modules()
        task_stats         = user.today_tasks_stats
        health_streak      = user.health_streak

        ai_tip             = get_personalized_ai_tip(user)

        return render_template(
            'dashboard/dashboard.html',
            user               = user,
            profile            = user.profile,
            bmi_category       = user.bmi_category,
            total_predictions  = total_predictions,
            risk_summary       = risk_summary,
            disease_stats      = disease_stats,
            recent_predictions = recent_predictions,
            days_since_last    = days_since_last,
            overall_risk       = overall_risk,
            reports_downloaded = reports_downloaded,
            health_tips        = health_tips,
            ai_tip             = ai_tip,
            disease_modules    = disease_modules,
            task_stats         = task_stats,
            health_streak      = health_streak,
            page_title         = 'Health Dashboard',
        )

    except Exception as e:
        logger.error(f'Dashboard error for user {current_user.id}: {e}', exc_info=True)
        flash(f'Dashboard error: {str(e)}', 'danger')
        return redirect(url_for('auth.logout'))


# ============================================================
# DYNAMIC AI HEALTH TIP ENDPOINT (AJAX)
# ============================================================
@dashboard_bp.route('/ai-health-tip', methods=['GET', 'POST'])
@login_required
def get_ai_tip_endpoint():
    """
    Returns an AI personalized health tip dynamically calibrated for the logged-in user.
    """
    user = User.get_by_id(current_user.id)
    category = request.args.get('category')
    if not category and request.is_json:
        category = (request.get_json(silent=True) or {}).get('category')
    
    tip = get_personalized_ai_tip(user, requested_category=category)
    return jsonify({
        'success': True,
        'tip': tip
    })


# ============================================================
# PREDICTION HISTORY & TIMELINE
# ============================================================
@dashboard_bp.route('/history')
@login_required
def history():
    page           = request.args.get('page',     1,  type=int)
    per_page       = request.args.get('per_page', 10, type=int)
    disease_filter = request.args.get('disease',  '', type=str)
    risk_filter    = request.args.get('risk',     '', type=str)
    search_q       = request.args.get('q',        '', type=str).strip()

    query = PredictionHistory.query.filter_by(user_id=current_user.id)

    if search_q:
        query = query.filter(
            db.or_(
                PredictionHistory.disease_name.ilike(f'%{search_q}%'),
                PredictionHistory.result.ilike(f'%{search_q}%'),
                PredictionHistory.model_used.ilike(f'%{search_q}%')
            )
        )

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
        search_q       = search_q,
        disease_names  = disease_names,
        page_title     = 'Health Timeline & Reports',
    )


# ============================================================
# PREDICTION DETAIL
# ============================================================
@dashboard_bp.route('/history/<int:prediction_id>')
@login_required
def prediction_detail(prediction_id):
    prediction = PredictionHistory.get_by_id(
        prediction_id, current_user.id
    )
    if not prediction:
        flash('Prediction record not found.', 'warning')
        return redirect(url_for('dashboard.history'))

    # Generate insights for detail view
    import json
    try:
        input_data = json.loads(prediction.input_data or '{}')
    except Exception:
        input_data = {}

    insights = generate_health_insights(
        disease_key  = prediction.disease_name.lower().replace(' ', '_'),
        result       = prediction.result,
        risk_level   = prediction.risk_level,
        input_data   = input_data,
        user_profile = current_user.profile
    )

    return render_template(
        'dashboard/prediction_detail.html',
        prediction = format_prediction_for_display(prediction),
        insights   = insights,
        page_title = f'{prediction.disease_name} — Assessment Detail',
    )


# ============================================================
# DELETE PREDICTION
# ============================================================
@dashboard_bp.route('/history/<int:prediction_id>/delete', methods=['POST'])
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
            f'Deleted assessment #{prediction_id} for {name}'
        )
        flash(f'Assessment record for {name} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting prediction {prediction_id}: {e}')
        flash('Failed to delete assessment record.', 'danger')
    return redirect(url_for('dashboard.history'))


# ============================================================
# HEALTH PROFILE VIEW
# ============================================================
@dashboard_bp.route('/profile')
@login_required
def profile():
    user = User.get_by_id(current_user.id)
    if not user.profile:
        profile_obj = UserProfile(user_id=user.id, updated_at=datetime.utcnow())
        profile_obj.save()

    total_predictions  = user.total_predictions
    risk_summary       = PredictionHistory.get_risk_summary(user.id)
    disease_stats      = PredictionHistory.get_disease_stats(user.id)
    recent_raw         = PredictionHistory.get_by_user(user.id, limit=5)
    recent_predictions = [format_prediction_for_display(p) for p in recent_raw]

    return render_template(
        'dashboard/profile.html',
        user               = user,
        profile            = user.profile,
        bmi_category       = user.bmi_category,
        total_predictions  = total_predictions,
        risk_summary       = risk_summary,
        disease_stats      = disease_stats,
        recent_predictions = recent_predictions,
        page_title         = 'My Health Profile',
    )


# ============================================================
# UPDATE HEALTH PROFILE
# ============================================================
@dashboard_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    first_name = sanitize_input(request.form.get('first_name', ''))
    last_name  = sanitize_input(request.form.get('last_name',  ''))
    age        = request.form.get('age', type=int)
    gender     = sanitize_input(request.form.get('gender', ''))
    phone      = sanitize_input(request.form.get('phone',  ''))

    # Health Profile Fields
    height_cm  = request.form.get('height_cm', type=float)
    weight_kg  = request.form.get('weight_kg', type=float)
    blood_group = sanitize_input(request.form.get('blood_group', ''))
    smoking_status = sanitize_input(request.form.get('smoking_status', 'Non-smoker'))
    alcohol_status = sanitize_input(request.form.get('alcohol_status', 'None'))
    activity_level = sanitize_input(request.form.get('activity_level', 'Moderately Active'))
    existing_conditions = sanitize_input(request.form.get('existing_conditions', ''))
    allergies = sanitize_input(request.form.get('allergies', ''))
    emergency_contact_name = sanitize_input(request.form.get('emergency_contact_name', ''))
    emergency_contact_phone = sanitize_input(request.form.get('emergency_contact_phone', ''))

    errors = []
    if not first_name or len(first_name) < 2:
        errors.append('First name must be at least 2 characters.')
    if not last_name or len(last_name) < 2:
        errors.append('Last name must be at least 2 characters.')
    if age and (age < 1 or age > 120):
        errors.append('Age must be between 1 and 120.')
    if height_cm and (height_cm < 40 or height_cm > 250):
        errors.append('Height must be between 40 cm and 250 cm.')
    if weight_kg and (weight_kg < 10 or weight_kg > 300):
        errors.append('Weight must be between 10 kg and 300 kg.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('dashboard.profile'))

    try:
        user = User.get_by_id(current_user.id)
        user.first_name = first_name
        user.last_name  = last_name
        user.age        = age
        user.gender     = gender
        user.phone      = phone
        user.updated_at = datetime.utcnow()

        if not user.profile:
            user.profile = UserProfile(user_id=user.id)

        user.profile.height_cm = height_cm
        user.profile.weight_kg = weight_kg
        user.profile.blood_group = blood_group
        user.profile.smoking_status = smoking_status
        user.profile.alcohol_status = alcohol_status
        user.profile.activity_level = activity_level
        user.profile.existing_conditions = existing_conditions
        user.profile.allergies = allergies
        user.profile.emergency_contact_name = emergency_contact_name
        user.profile.emergency_contact_phone = emergency_contact_phone
        user.profile.calculate_bmi()
        user.profile.updated_at = datetime.utcnow()

        db.session.commit()
        log_activity(current_user.id, 'PROFILE_UPDATE', 'Health profile updated')
        flash('Health profile and clinical metrics updated successfully.', 'success')

    except Exception as e:
        db.session.rollback()
        logger.error(f'Failed to update profile for user {current_user.id}: {e}')
        flash('Failed to update profile. Please try again.', 'danger')

    return redirect(url_for('dashboard.profile'))


# ============================================================
# CHANGE PASSWORD
# ============================================================
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
        errors.append('New passwords do not match.')
    if current_pw == new_pw:
        errors.append('New password must differ from current password.')

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('dashboard.profile'))

    try:
        user = User.get_by_id(current_user.id)
        user.set_password(new_pw)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        logout_user()
        session.clear()
        flash('Password updated successfully. Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error changing password: {e}')
        flash('Failed to update password. Please try again.', 'danger')
        return redirect(url_for('dashboard.profile'))


# ============================================================
# DAILY HEALTH TASKS AJAX TOGGLE
# ============================================================
@dashboard_bp.route('/tasks/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    """AJAX endpoint to check/uncheck a daily task."""
    task = DailyHealthTask.toggle_task(task_id, current_user.id)
    if not task:
        return jsonify({'success': False, 'error': 'Task not found or access denied.'}), 404

    stats = current_user.today_tasks_stats
    return jsonify({
        'success': True,
        'task_id': task.id,
        'is_completed': task.is_completed,
        'total': stats['total'],
        'completed': stats['completed'],
        'pct': stats['pct'],
        'streak': current_user.health_streak
    })


@dashboard_bp.route('/tasks/add', methods=['POST'])
@login_required
def add_custom_task():
    """Allows user to add a personalized daily task."""
    task_text = sanitize_input(request.form.get('task_text', ''))
    category  = sanitize_input(request.form.get('category', 'wellness'))

    if not task_text or len(task_text) < 3:
        flash('Please enter a valid task description (at least 3 characters).', 'warning')
        return redirect(url_for('dashboard.index'))

    try:
        task = DailyHealthTask(
            user_id     = current_user.id,
            task_text   = task_text,
            category    = category,
            target_date = date.today(),
            is_completed= False
        )
        task.save()
        flash('New daily health task added to your checklist!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to add task.', 'danger')

    return redirect(url_for('dashboard.index'))


@dashboard_bp.route('/tasks/reset', methods=['POST'])
@login_required
def reset_daily_tasks():
    """Regenerates a fresh set of daily wellness tasks for today."""
    try:
        DailyHealthTask.query.filter_by(
            user_id=current_user.id, target_date=date.today()
        ).delete()
        DailyHealthTask.generate_default_tasks_for_user(current_user.id)
        db.session.commit()
        flash('Today\'s wellness task checklist has been refreshed.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to reset tasks.', 'danger')
    return redirect(url_for('dashboard.index'))


# ============================================================
# PDF REPORT DOWNLOAD & INLINE PREVIEW
# ============================================================
@dashboard_bp.route('/report/<int:prediction_id>/download')
@login_required
def download_report(prediction_id):
    """Generates and downloads the professional PDF report as an attachment."""
    prediction = PredictionHistory.get_by_id(prediction_id, current_user.id)
    if not prediction:
        flash('Assessment record not found.', 'warning')
        return redirect(url_for('dashboard.history'))

    session['reports_downloaded'] = session.get('reports_downloaded', 0) + 1

    try:
        input_data = json.loads(prediction.input_data or '{}')
    except Exception:
        input_data = {}

    insights = generate_health_insights(
        disease_key  = prediction.disease_name.lower().replace(' ', '_'),
        result       = prediction.result,
        risk_level   = prediction.risk_level,
        input_data   = input_data,
        user_profile = current_user.profile
    )

    pdf_buffer = generate_pdf_report(
        user         = current_user,
        prediction   = prediction,
        user_profile = current_user.profile,
        insights     = insights
    )

    safe_name = prediction.disease_name.replace(' ', '_')
    filename = f"MediScan_Report_{safe_name}_RPT{prediction.id:05d}.pdf"

    # Save record in health_reports table if not already tracked
    existing_report = HealthReport.query.filter_by(
        user_id=current_user.id, prediction_id=prediction.id
    ).first()
    if not existing_report:
        try:
            report_rec = HealthReport(
                user_id       = current_user.id,
                prediction_id = prediction.id,
                filename      = filename,
                file_size     = len(pdf_buffer.getvalue())
            )
            report_rec.save()
        except Exception:
            db.session.rollback()

    return Response(
        pdf_buffer.getvalue(),
        mimetype = 'application/pdf',
        headers  = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


@dashboard_bp.route('/report/<int:prediction_id>/view')
@login_required
def view_report(prediction_id):
    """Streams the PDF inline for viewing/printing in a browser tab."""
    prediction = PredictionHistory.get_by_id(prediction_id, current_user.id)
    if not prediction:
        flash('Assessment record not found.', 'warning')
        return redirect(url_for('dashboard.history'))

    try:
        input_data = json.loads(prediction.input_data or '{}')
    except Exception:
        input_data = {}

    insights = generate_health_insights(
        disease_key  = prediction.disease_name.lower().replace(' ', '_'),
        result       = prediction.result,
        risk_level   = prediction.risk_level,
        input_data   = input_data,
        user_profile = current_user.profile
    )

    pdf_buffer = generate_pdf_report(
        user         = current_user,
        prediction   = prediction,
        user_profile = current_user.profile,
        insights     = insights
    )

    safe_name = prediction.disease_name.replace(' ', '_')
    filename = f"MediScan_Report_{safe_name}_RPT{prediction.id:05d}.pdf"

    return Response(
        pdf_buffer.getvalue(),
        mimetype = 'application/pdf',
        headers  = {
            'Content-Disposition': f'inline; filename="{filename}"'
        }
    )


# ============================================================
# STATS AJAX
# ============================================================
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


# ============================================================
# DISEASE MODULES REGISTRY HELPER
# ============================================================
def _get_disease_modules():
    return [
        {
            'name'    : 'Diabetes Mellitus',
            'slug'    : 'diabetes',
            'icon'    : '🩸',
            'accuracy': '94.2%',
            'description': 'Blood glucose, insulin, and metabolic indices.',
            'url'     : url_for('prediction.predict_form', disease='diabetes'),
        },
        {
            'name'    : 'Heart Disease',
            'slug'    : 'heart',
            'icon'    : '🫀',
            'accuracy': '95.1%',
            'description': 'Cardiovascular parameters, blood pressure, and resting ECG.',
            'url'     : url_for('prediction.predict_form', disease='heart'),
        },
        {
            'name'    : "Parkinson's Disease",
            'slug'    : 'parkinsons',
            'icon'    : '🧠',
            'accuracy': '96.8%',
            'description': 'Acoustic vocal analysis and motor biomarker assessment.',
            'url'     : url_for('prediction.predict_form', disease='parkinsons'),
        },
        {
            'name'    : 'Kidney Disease',
            'slug'    : 'kidney',
            'icon'    : '🩻',
            'accuracy': '96.4%',
            'description': 'Renal filtration, creatinine, blood urea, and electrolytes.',
            'url'     : url_for('prediction.predict_form', disease='kidney'),
        },
        {
            'name'    : 'Liver Disease',
            'slug'    : 'liver',
            'icon'    : '🔬',
            'accuracy': '91.5%',
            'description': 'Hepatic enzymes, bilirubin, and protein synthesis indicators.',
            'url'     : url_for('prediction.predict_form', disease='liver'),
        },
        {
            'name'    : 'Lung Cancer',
            'slug'    : 'lung_cancer',
            'icon'    : '🫁',
            'accuracy': '93.7%',
            'description': 'Pulmonary symptom patterns and risk factor profiling.',
            'url'     : url_for('prediction.predict_form', disease='lung_cancer'),
        },
        {
            'name'    : 'Hypertension',
            'slug'    : 'hypertension',
            'icon'    : '📊',
            'accuracy': '92.9%',
            'description': 'Arterial blood pressure, cholesterol, and lifestyle markers.',
            'url'     : url_for('prediction.predict_form', disease='hypertension'),
        },
        {
            'name'    : 'Breast Cancer',
            'slug'    : 'breast_cancer',
            'icon'    : '🧬',
            'accuracy': '95.8%',
            'description': 'Cytological cellular characteristics and nuclear morphology.',
            'url'     : url_for('prediction.predict_form', disease='breast_cancer'),
        },
    ]