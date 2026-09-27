# ============================================================
# routes/auth_routes.py — MediScan Pro Authentication Routes
# ============================================================

import os
import secrets
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, session, jsonify, make_response, current_app
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)

from database.db import db, User, UserProfile
from utils.helpers import (
    sanitize_input,
    validate_email,
    validate_password_strength,
    log_activity,
    build_json_response
)

auth_bp = Blueprint(
    'auth',
    __name__,
    template_folder='../templates/auth'
)

# In-memory reset token store for self-service password recovery: {token: {'email': email, 'expires': dt}}
RESET_TOKENS = {}


# ============================================================
# SIGNUP ROUTE
# ============================================================
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    GET  → Renders the signup form.
    POST → Validates inputs, creates new user, initializes profile, redirects to dashboard.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        first_name = sanitize_input(request.form.get('first_name', ''))
        last_name  = sanitize_input(request.form.get('last_name',  ''))
        email      = sanitize_input(request.form.get('email',      '')).lower()
        password   = request.form.get('password',         '')
        confirm_pw = request.form.get('confirm_password', '')

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

        try:
            new_user = User(
                first_name  = first_name,
                last_name   = last_name,
                email       = email,
                created_at  = datetime.utcnow(),
                updated_at  = datetime.utcnow(),
                is_active   = True,
                is_verified = False,
                role        = 'patient'
            )
            new_user.set_password(password)
            new_user.save()

            # Initialize an empty health profile
            profile = UserProfile(
                user_id    = new_user.id,
                updated_at = datetime.utcnow()
            )
            profile.save()

            login_user(new_user, remember=True)
            new_user.update_last_login()

            log_activity(
                user_id = new_user.id,
                action  = 'SIGNUP',
                details = f'New account created for {email}'
            )

            flash(
                f'Welcome to MediScan Pro, {first_name}! Your clinical health account is ready.',
                'success'
            )
            return redirect(url_for('dashboard.index'))

        except Exception as e:
            db.session.rollback()
            flash('An unexpected error occurred during account creation. Please try again.', 'danger')
            return render_template(
                'auth/login.html',
                active_tab='signup',
                errors=[str(e)]
            )

    return render_template('auth/login.html', active_tab='signup')


# ============================================================
# LOGIN ROUTE
# ============================================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  → Renders the login form.
    POST → Validates credentials, sets up session, redirects to dashboard.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email    = sanitize_input(request.form.get('email', '')).lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember_me') == 'on'

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template(
                'auth/login.html',
                active_tab='signin',
                form_data={'email': email}
            )

        user = User.get_by_email(email)

        if not user or not user.check_password(password):
            flash('Invalid email or password. Please verify your credentials.', 'danger')
            log_activity(
                user_id = user.id if user else None,
                action  = 'LOGIN_FAILED',
                details = f'Failed login attempt for {email}'
            )
            return render_template(
                'auth/login.html',
                active_tab='signin',
                form_data={'email': email}
            )

        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'warning')
            return render_template('auth/login.html', active_tab='signin')

        login_user(user, remember=remember)
        user.update_last_login()

        session['user_id']   = user.id
        session['user_name'] = user.full_name
        session['user_role'] = user.role

        log_activity(
            user_id = user.id,
            action  = 'LOGIN_SUCCESS',
            details = f'User {email} logged in successfully'
        )

        flash(f'Welcome back, {user.first_name}!', 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html', active_tab='signin')


# ============================================================
# LOGOUT ROUTE
# ============================================================
@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    Unconditionally logs out user, clears all session state and cookies,
    and redirects to login page with anti-cache headers.
    Does not require @login_required to prevent redirect loops on stale sessions.
    """
    user_id = current_user.id if current_user.is_authenticated else None
    user_name = current_user.full_name if current_user.is_authenticated else 'User'

    if current_user.is_authenticated:
        try:
            logout_user()
        except Exception:
            pass

    # Clear entire Flask session
    session.clear()

    if user_id:
        try:
            log_activity(
                user_id = user_id,
                action  = 'LOGOUT',
                details = f'{user_name} logged out'
            )
        except Exception:
            pass

    flash('You have been logged out securely.', 'info')
    response = make_response(redirect(url_for('auth.login')))

    # Explicitly invalidate session and remember cookies
    cookie_name = current_app.config.get('SESSION_COOKIE_NAME', 'session')
    response.delete_cookie(cookie_name)
    response.delete_cookie('session')
    response.delete_cookie('remember_token')

    # Security anti-caching headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response



# ============================================================
# FORGOT PASSWORD WORKFLOW
# ============================================================
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Self-service password recovery.
    Allows user to request a password reset for their registered email.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = sanitize_input(request.form.get('email', '')).lower()
        if not email or not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('auth/forgot_password.html')

        user = User.get_by_email(email)
        if user:
            token = secrets.token_urlsafe(32)
            RESET_TOKENS[token] = {
                'email': email,
                'expires': datetime.utcnow() + timedelta(hours=1)
            }
            # Provide direct reset link on screen for immediate testing & demo convenience
            flash(
                'Password reset authorization generated successfully. Proceed below to set your new password.',
                'success'
            )
            return redirect(url_for('auth.reset_password', token=token))
        else:
            flash('If an account exists with that email, a password recovery procedure has been initiated.', 'info')
            return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Allows user to set a new password with a valid recovery token.
    """
    token_data = RESET_TOKENS.get(token)
    if not token_data or datetime.utcnow() > token_data['expires']:
        flash('Password reset link is invalid or has expired. Please request a new one.', 'warning')
        return redirect(url_for('auth.forgot_password'))

    email = token_data['email']
    user  = User.get_by_email(email)

    if not user:
        flash('User account not found.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_pw     = request.form.get('password', '')
        confirm_pw = request.form.get('confirm_password', '')

        errors = []
        if not new_pw:
            errors.append('New password is required.')
        else:
            pw_check = validate_password_strength(new_pw)
            if not pw_check['valid']:
                errors.append(pw_check['message'])

        if new_pw != confirm_pw:
            errors.append('Passwords do not match.')

        if errors:
            return render_template('auth/reset_password.html', token=token, email=email, errors=errors)

        try:
            user.set_password(new_pw)
            user.updated_at = datetime.utcnow()
            db.session.commit()

            # Clean up token
            RESET_TOKENS.pop(token, None)

            log_activity(
                user_id = user.id,
                action  = 'PASSWORD_RESET',
                details = f'Password reset completed for {email}'
            )

            flash('Your password has been successfully reset! Please sign in with your new credentials.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash('Failed to reset password. Please try again.', 'danger')

    return render_template('auth/reset_password.html', token=token, email=email)


# ============================================================
# ACCOUNT DELETION
# ============================================================
@auth_bp.route('/account/delete', methods=['POST'])
@login_required
def delete_account():
    """
    Safely deletes the user account and associated records (profiles, predictions, tasks, reports).
    Requires password verification.
    """
    confirm_password = request.form.get('confirm_password', '')

    if not current_user.check_password(confirm_password):
        flash('Incorrect password. Account deletion canceled.', 'danger')
        return redirect(url_for('dashboard.profile'))

    user_id = current_user.id
    email   = current_user.email

    try:
        user = User.get_by_id(user_id)
        logout_user()
        session.clear()

        user.delete()

        log_activity(
            user_id = user_id,
            action  = 'ACCOUNT_DELETED',
            details = f'Account {email} permanently deleted by user request'
        )

        flash('Your account and all associated health data have been permanently removed.', 'info')
        return redirect(url_for('home'))

    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting your account. Please try again.', 'danger')
        return redirect(url_for('dashboard.profile'))


# ============================================================
# AJAX EMAIL & PASSWORD CHECKS
# ============================================================
@auth_bp.route('/check-email', methods=['POST'])
def check_email():
    data  = request.get_json(silent=True) or {}
    email = sanitize_input(data.get('email', '')).lower()

    if not email or not validate_email(email):
        return jsonify({'available': False, 'error': 'Invalid email format'})

    available = not User.email_exists(email)
    return jsonify({'available': available})


@auth_bp.route('/check-password', methods=['POST'])
def check_password_strength():
    data     = request.get_json(silent=True) or {}
    password = data.get('password', '')

    result = validate_password_strength(password)
    return jsonify(result)