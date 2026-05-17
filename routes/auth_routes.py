# ============================================================
# routes/auth_routes.py — MediScan Pro Authentication Routes
# ============================================================

import os
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, session, jsonify
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)

from database.db import db, User
# from utils.helpers import (
#     validate_email, validate_password_strength,
#     sanitize_input, log_activity, generate_csrf_token
# )

from utils.helpers import (
    sanitize_input,
    validate_email,
    validate_password_strength,
    log_activity,
    build_json_response
)

# ── Blueprint Definition ──────────────────────────────────────
# All routes in this file will be prefixed with /auth (set in app.py)
# Example: login() → accessible at /auth/login
auth_bp = Blueprint(
    'auth',
    __name__,
    template_folder='../templates/auth'
)


# ============================================================
# SIGNUP ROUTE
# ============================================================
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    GET  → Renders the signup form.
    POST → Validates inputs, creates new user, redirects to dashboard.
    """

    # Redirect already-authenticated users away from signup page
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    # ── Handle POST (form submission) ─────────────────────────
    if request.method == 'POST':

        # ── Extract & sanitize form fields ───────────────────
        first_name = sanitize_input(request.form.get('first_name', ''))
        last_name  = sanitize_input(request.form.get('last_name',  ''))
        email      = sanitize_input(request.form.get('email',      '')).lower()
        password   = request.form.get('password',         '')
        confirm_pw = request.form.get('confirm_password', '')

        # ── Server-side validation ────────────────────────────
        errors = []

        if not first_name or len(first_name) < 2:
            errors.append('First name must be at least 2 characters.')

        if not last_name or len(last_name) < 2:
            errors.append('Last name must be at least 2 characters.')

        if not email or not validate_email(email):
            errors.append('Please enter a valid email address.')

        if not password:
            errors.append('Password is required.')
        else:
            pw_check = validate_password_strength(password)
            if not pw_check['valid']:
                errors.append(pw_check['message'])

        if password != confirm_pw:
            errors.append('Passwords do not match.')

        if User.email_exists(email):
            errors.append('An account with this email already exists.')

        # ── Return errors if validation failed ────────────────
        if errors:
            return render_template(
                'auth/login.html',
                active_tab='signup',
                errors=errors,
                form_data={
                    'first_name': first_name,
                    'last_name' : last_name,
                    'email'     : email,
                }
            )

        # ── Create and persist new user ───────────────────────
        try:
            new_user = User(
                first_name = first_name,
                last_name  = last_name,
                email      = email,
                created_at = datetime.utcnow(),
                updated_at = datetime.utcnow(),
                is_active  = True,
                is_verified= False,
                role       = 'patient'
            )
            new_user.set_password(password)
            new_user.save()

            # ── Auto-login after successful registration ──────
            login_user(new_user, remember=True)
            new_user.update_last_login()

            # ── Log activity ──────────────────────────────────
            log_activity(
                user_id  = new_user.id,
                action   = 'SIGNUP',
                details  = f'New account created for {email}'
            )

            flash(
                f'Welcome to MediScan Pro, {first_name}! '
                f'Your account has been created successfully.',
                'success'
            )
            return redirect(url_for('dashboard.index'))

        except Exception as e:
            db.session.rollback()
            flash('An unexpected error occurred. Please try again.', 'danger')
            return render_template(
                'auth/login.html',
                active_tab='signup',
                errors=[str(e)]
            )

    # ── Handle GET (render empty form) ────────────────────────
    return render_template('auth/login.html', active_tab='signup')


# ============================================================
# LOGIN ROUTE
# ============================================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  → Renders the login form.
    POST → Validates credentials, creates session, redirects to dashboard.
    """

    # Redirect already-authenticated users
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    # ── Handle POST (form submission) ─────────────────────────
    if request.method == 'POST':

        # ── Extract form fields ───────────────────────────────
        email      = sanitize_input(request.form.get('email', '')).lower()
        password   = request.form.get('password', '')
        remember   = request.form.get('remember_me') == 'on'

        # ── Basic presence validation ─────────────────────────
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template(
                'auth/login.html',
                active_tab='signin',
                form_data={'email': email}
            )

        # ── Lookup user by email ──────────────────────────────
        user = User.get_by_email(email)

        # ── Validate credentials ──────────────────────────────
        # We check both conditions together to prevent
        # "user enumeration" attacks (attacker can't tell
        # whether the email or password was wrong).
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            log_activity(
                user_id = user.id if user else None,
                action  = 'LOGIN_FAILED',
                details = f'Failed login attempt for email: {email}'
            )
            return render_template(
                'auth/login.html',
                active_tab='signin',
                form_data={'email': email}
            )

        # ── Check account is active ───────────────────────────
        if not user.is_active:
            flash(
                'Your account has been deactivated. '
                'Please contact support.',
                'warning'
            )
            return render_template('auth/login.html', active_tab='signin')

        # ── Create authenticated session ──────────────────────
        # remember=True sets a persistent cookie (stays after browser close)
        # remember=False creates a session cookie (cleared when browser closes)
        login_user(user, remember=remember)
        user.update_last_login()

        # ── Store basic user info in session ──────────────────
        session['user_id']   = user.id
        session['user_name'] = user.full_name
        session['user_role'] = user.role

        # ── Log successful login ──────────────────────────────
        log_activity(
            user_id = user.id,
            action  = 'LOGIN_SUCCESS',
            details = f'User {email} logged in successfully'
        )

        flash(f'Welcome back, {user.first_name}!', 'success')

        # ── Redirect to originally requested page (if any) ────
        # Flask-Login stores the URL the user tried to visit
        # before being redirected to login in 'next' parameter.
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        return redirect(url_for('dashboard.index'))

    # ── Handle GET (render empty form) ────────────────────────
    return render_template('auth/login.html', active_tab='signin')


# ============================================================
# LOGOUT ROUTE
# ============================================================
@auth_bp.route('/logout')
@login_required
def logout():
    """
    Clears the user session and redirects to the home page.
    @login_required ensures only authenticated users can logout
    (prevents errors from unauthenticated logout attempts).
    """

    user_name = current_user.full_name
    user_id   = current_user.id

    # ── Clear Flask-Login session ─────────────────────────────
    logout_user()

    # ── Clear all custom session variables ───────────────────
    session.clear()

    # ── Log activity ──────────────────────────────────────────
    log_activity(
        user_id = user_id,
        action  = 'LOGOUT',
        details = f'{user_name} logged out'
    )

    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


# ============================================================
# AJAX EMAIL AVAILABILITY CHECK
# ============================================================
@auth_bp.route('/check-email', methods=['POST'])
def check_email():
    """
    AJAX endpoint — called by frontend JavaScript as user types
    their email in the signup form to provide instant feedback.

    Expects JSON body: { "email": "user@example.com" }
    Returns JSON:      { "available": true/false }
    """

    data  = request.get_json(silent=True) or {}
    email = sanitize_input(data.get('email', '')).lower()

    if not email or not validate_email(email):
        return jsonify({'available': False, 'error': 'Invalid email format'})

    available = not User.email_exists(email)
    return jsonify({'available': available})


# ============================================================
# PASSWORD STRENGTH CHECK (AJAX)
# ============================================================
@auth_bp.route('/check-password', methods=['POST'])
def check_password_strength():
    """
    AJAX endpoint — provides real-time password strength feedback
    as the user types in the signup form.

    Expects JSON body: { "password": "mypassword123" }
    Returns JSON:      { "valid": true, "strength": "Strong", "score": 4 }
    """

    data     = request.get_json(silent=True) or {}
    password = data.get('password', '')

    result = validate_password_strength(password)
    return jsonify(result)


# ============================================================
# PROFILE UPDATE ROUTE
# ============================================================
@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """
    Handles profile update form submissions from the dashboard.
    Updates allowed fields only (never email or password here).
    """

    first_name = sanitize_input(request.form.get('first_name', ''))
    last_name  = sanitize_input(request.form.get('last_name',  ''))
    age        = request.form.get('age',    type=int)
    gender     = sanitize_input(request.form.get('gender', ''))
    phone      = sanitize_input(request.form.get('phone',  ''))

    errors = []

    if not first_name or len(first_name) < 2:
        errors.append('First name must be at least 2 characters.')

    if not last_name or len(last_name) < 2:
        errors.append('Last name must be at least 2 characters.')

    if age and (age < 1 or age > 120):
        errors.append('Please enter a valid age between 1 and 120.')

    if errors:
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('dashboard.index'))

    try:
        user            = User.get_by_id(current_user.id)
        user.first_name = first_name
        user.last_name  = last_name
        user.age        = age
        user.gender     = gender
        user.phone      = phone
        user.updated_at = datetime.utcnow()

        db.session.commit()

        log_activity(
            user_id = current_user.id,
            action  = 'PROFILE_UPDATE',
            details = f'Profile updated for user {current_user.email}'
        )

        flash('Profile updated successfully.', 'success')

    except Exception as e:
        db.session.rollback()
        flash('Failed to update profile. Please try again.', 'danger')

    return redirect(url_for('dashboard.index'))


# ============================================================
# CHANGE PASSWORD ROUTE
# ============================================================
@auth_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """
    Handles password change requests.
    Requires the current password for verification before updating.
    """

    current_pw = request.form.get('current_password', '')
    new_pw     = request.form.get('new_password',     '')
    confirm_pw = request.form.get('confirm_password', '')

    errors = []

    if not current_user.check_password(current_pw):
        errors.append('Current password is incorrect.')

    if not new_pw:
        errors.append('New password is required.')
    else:
        pw_check = validate_password_strength(new_pw)
        if not pw_check['valid']:
            errors.append(pw_check['message'])

    if new_pw != confirm_pw:
        errors.append('New passwords do not match.')

    if current_pw == new_pw:
        errors.append('New password must be different from current password.')

    if errors:
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('dashboard.index'))

    try:
        user = User.get_by_id(current_user.id)
        user.set_password(new_pw)
        user.updated_at = datetime.utcnow()
        db.session.commit()

        log_activity(
            user_id = current_user.id,
            action  = 'PASSWORD_CHANGE',
            details = f'Password changed for user {current_user.email}'
        )

        logout_user()
        session.clear()

        flash(
            'Password changed successfully. Please log in with your new password.',
            'success'
        )
        return redirect(url_for('auth.login'))

    except Exception as e:
        db.session.rollback()
        flash('Failed to change password. Please try again.', 'danger')
        return redirect(url_for('dashboard.index'))