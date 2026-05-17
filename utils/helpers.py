# ============================================================
# utils/helpers.py — MediScan Pro Utility & Helper Functions
# ============================================================

import re
import os
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional, Union

print("helpers.py loaded")

# ── Configure module-level logger ────────────────────────────
# All activity logs from this module go to mediscan.log
logging.basicConfig(
    level    = logging.INFO,
    format   = '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers = [
        logging.StreamHandler(),                          # prints to terminal
        logging.FileHandler('instance/mediscan.log',      # writes to log file
                            encoding='utf-8'),
    ]
)
logger = logging.getLogger('mediscan')



# ============================================================
# INPUT SANITIZATION
# ============================================================
def sanitize_input(value: str) -> str:
    """
    Cleans user-supplied string input.
    Strips leading/trailing whitespace and removes characters
    commonly used in XSS and SQL injection attacks.

    Args:
        value: Raw string from request.form or request.args

    Returns:
        Cleaned string safe for storage and display

    Example:
        sanitize_input('  <script>alert(1)</script>  ')
        → 'scriptalert1script'
    """
    if not isinstance(value, str):
        return ''

    # Strip surrounding whitespace
    value = value.strip()

    # Remove HTML tags (basic XSS prevention)
    value = re.sub(r'<[^>]*>', '', value)

    # Remove null bytes (can break databases and logs)
    value = value.replace('\x00', '')

    return value


# ============================================================
# EMAIL VALIDATION
# ============================================================
def validate_email(email: str) -> bool:
    """
    Validates an email address against RFC 5322 simplified pattern.

    Args:
        email: Email string to validate

    Returns:
        True if valid, False otherwise

    Example:
        validate_email('user@example.com')  → True
        validate_email('not-an-email')       → False
    """
    if not email or not isinstance(email, str):
        return False

    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


# ============================================================
# PASSWORD STRENGTH VALIDATION
# ============================================================
def validate_password_strength(password: str) -> dict:
    """
    Evaluates password strength against security criteria.
    Returns a detailed result used by both signup route
    and the AJAX password strength endpoint.

    Args:
        password: Plain-text password string

    Returns:
        Dict with keys:
            valid    (bool)  → meets minimum requirements
            score    (int)   → 0–5 strength score
            strength (str)   → 'Very Weak' / 'Weak' / 'Fair' / 'Good' / 'Strong'
            message  (str)   → human-readable feedback
            checks   (dict)  → individual rule pass/fail results

    Example:
        validate_password_strength('MyP@ss123')
        → {'valid': True, 'score': 4, 'strength': 'Good', ...}
    """
    if not password:
        return {
            'valid'   : False,
            'score'   : 0,
            'strength': 'Very Weak',
            'message' : 'Password is required.',
            'checks'  : {},
        }

    checks = {
        'length'     : len(password) >= 8,
        'uppercase'  : bool(re.search(r'[A-Z]', password)),
        'lowercase'  : bool(re.search(r'[a-z]', password)),
        'digit'      : bool(re.search(r'\d',    password)),
        'special'    : bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
    }

    score = sum(checks.values())   # 0–5

    strength_map = {
        0: 'Very Weak',
        1: 'Very Weak',
        2: 'Weak',
        3: 'Fair',
        4: 'Good',
        5: 'Strong',
    }

    # Build actionable feedback message
    missing = []
    if not checks['length']:
        missing.append('at least 8 characters')
    if not checks['uppercase']:
        missing.append('an uppercase letter')
    if not checks['lowercase']:
        missing.append('a lowercase letter')
    if not checks['digit']:
        missing.append('a number')
    if not checks['special']:
        missing.append('a special character (!@#$...)')

    if missing:
        message = 'Password must contain ' + ', '.join(missing) + '.'
    else:
        message = 'Password meets all security requirements.'

    # Minimum requirement: length + at least 2 other checks
    valid = checks['length'] and score >= 3

    return {
        'valid'   : valid,
        'score'   : score,
        'strength': strength_map[score],
        'message' : message,
        'checks'  : checks,
    }


# ============================================================
# NUMERIC INPUT VALIDATION
# ============================================================
def validate_numeric_input(
    value     : str,
    field_name: str,
    min_val   : Optional[float] = None,
    max_val   : Optional[float] = None,
    is_float  : bool = False
) -> dict:
    """
    Validates a numeric form input value for prediction forms.
    Checks that the value is a valid number and within range.

    Args:
        value     : Raw string value from the form
        field_name: Human-readable label for error messages
        min_val   : Minimum allowed value (inclusive)
        max_val   : Maximum allowed value (inclusive)
        is_float  : True to allow decimals, False for integers only

    Returns:
        Dict with keys:
            value (float/int/None) → parsed value if valid, None if invalid
            error (str/None)       → error message if invalid, None if valid

    Example:
        validate_numeric_input('148', 'Glucose Level', 0, 300)
        → {'value': 148, 'error': None}

        validate_numeric_input('abc', 'Glucose Level', 0, 300)
        → {'value': None, 'error': 'Glucose Level must be a valid number.'}
    """
    if not value and value != 0:
        return {
            'value': None,
            'error': f'{field_name} is required.'
        }

    try:
        parsed = float(value) if is_float else int(float(value))
    except (ValueError, TypeError):
        return {
            'value': None,
            'error': f'{field_name} must be a valid number.'
        }

    if min_val is not None and parsed < min_val:
        return {
            'value': None,
            'error': f'{field_name} must be at least {min_val}.'
        }

    if max_val is not None and parsed > max_val:
        return {
            'value': None,
            'error': f'{field_name} must not exceed {max_val}.'
        }

    return {'value': parsed, 'error': None}


# ============================================================
# CSRF TOKEN GENERATOR
# ============================================================
def generate_csrf_token() -> str:
    """
    Generates a cryptographically secure random token.
    Used as a fallback CSRF token generator.

    Returns:
        32-byte hex string token

    Example:
        generate_csrf_token()
        → 'a3f8b2c1d4e5f6a7b8c9d0e1f2a3b4c5'
    """
    import secrets
    return secrets.token_hex(32)


# ============================================================
# ACTIVITY LOGGER
# ============================================================
def log_activity(
    user_id: Optional[int],
    action : str,
    details: str = ''
) -> None:
    """
    Logs user activity to the application log file.
    Used throughout routes for audit trails.
    Silently fails if logging is unavailable (never crashes the app).

    Args:
        user_id : ID of the user performing the action (None for guests)
        action  : Short action code e.g. 'LOGIN_SUCCESS', 'PREDICTION_COMPLETE'
        details : Optional longer description

    Example:
        log_activity(42, 'LOGIN_SUCCESS', 'User john@example.com logged in')
        → Writes: [INFO] mediscan: USER=42 | ACTION=LOGIN_SUCCESS | ...
    """
    try:
        uid     = user_id or 'GUEST'
        message = f'USER={uid} | ACTION={action} | {details}'
        logger.info(message)
    except Exception:
        pass    # Never let logging crash the request cycle


# ============================================================
# PREDICTION DISPLAY FORMATTER
# ============================================================
def format_prediction_for_display(prediction) -> dict:
    """
    Converts a PredictionHistory ORM object into a display-ready
    dictionary for Jinja2 templates.

    Adds:
        - Formatted date string
        - Risk level CSS class for colour coding
        - Risk icon for UI display
        - Parsed input_data JSON
        - Confidence bar width (for CSS width property)

    Args:
        prediction: PredictionHistory model instance

    Returns:
        Dict with all prediction fields plus display helpers
    """
    if prediction is None:
        return {}

    # ── Parse stored JSON input data ──────────────────────────
    try:
        input_data = json.loads(prediction.input_data or '{}')
    except (json.JSONDecodeError, TypeError):
        input_data = {}

    # ── Risk level → CSS class mapping ───────────────────────
    risk_css_map = {
        'Low'     : 'success',   # green
        'Moderate': 'warning',   # amber
        'High'    : 'danger',    # red
    }

    # ── Risk level → icon mapping ─────────────────────────────
    risk_icon_map = {
        'Low'     : '✓',
        'Moderate': '⚠',
        'High'    : '!',
    }

    # ── Risk level → emoji mapping for history list ───────────
    risk_emoji_map = {
        'Low'     : '🟢',
        'Moderate': '🟡',
        'High'    : '🔴',
    }

    risk_level    = prediction.risk_level or 'Low'
    confidence    = round(prediction.confidence_pct or 0.0, 1)

    return {
        # Raw fields
        'id'            : prediction.id,
        'user_id'       : prediction.user_id,
        'disease_name'  : prediction.disease_name,
        'result'        : prediction.result,
        'risk_level'    : risk_level,
        'confidence_pct': confidence,
        'precautions'   : prediction.precautions or '',
        'model_used'    : prediction.model_used   or 'Ensemble Classifier',
        'input_data'    : input_data,

        # Display helpers
        'risk_css'      : risk_css_map.get(risk_level,  'secondary'),
        'risk_icon'     : risk_icon_map.get(risk_level, '?'),
        'risk_emoji'    : risk_emoji_map.get(risk_level,'⚪'),
        'bar_width'     : f'{confidence}%',

        # Formatted date strings
        'date_full'     : prediction.created_at.strftime('%B %d, %Y · %I:%M %p'),
        'date_short'    : prediction.created_at.strftime('%b %d, %Y'),
        'date_iso'      : prediction.created_at.isoformat(),

        # Download URL helper
        'download_url'  : f'/dashboard/report/{prediction.id}/download',
        'detail_url'    : f'/dashboard/history/{prediction.id}',
    }


# ============================================================
# DAYS SINCE CALCULATOR
# ============================================================
def calculate_days_since(dt: Optional[datetime]) -> Optional[int]:
    """
    Returns the number of whole days between a past datetime
    and the current UTC time.

    Args:
        dt: A datetime object (typically prediction.created_at)

    Returns:
        Integer number of days, or None if dt is None

    Example:
        calculate_days_since(datetime(2025, 5, 1))  → 7  (if today is May 8)
    """
    if dt is None:
        return None

    # Ensure dt is offset-naive for comparison with utcnow()
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)

    delta = datetime.utcnow() - dt
    return max(0, delta.days)


# ============================================================
# HEALTH TIPS PROVIDER
# ============================================================
def get_health_tips(count: int = 3) -> list:
    """
    Returns a rotating selection of health tips.
    Rotation is based on the day of the year so tips change daily
    but remain consistent across multiple page loads on the same day.

    Args:
        count: Number of tips to return (default 3)

    Returns:
        List of tip dicts with keys: emoji, title, body
    """

    all_tips = [
        {
            'emoji': '💧',
            'title': 'Stay Hydrated',
            'body' : 'Aim for 8–10 glasses of water daily. Proper hydration supports kidney function and flushes toxins effectively.',
        },
        {
            'emoji': '🚶',
            'title': 'Walk 10,000 Steps',
            'body' : 'Regular walking reduces the risk of heart disease by up to 30% and significantly improves blood sugar regulation.',
        },
        {
            'emoji': '🥗',
            'title': 'Eat the Rainbow',
            'body' : 'Colourful vegetables provide powerful antioxidants that protect cells against cancer and chronic disease.',
        },
        {
            'emoji': '😴',
            'title': 'Prioritise Sleep',
            'body' : 'Adults need 7–9 hours of quality sleep. Poor sleep increases risk of diabetes, obesity, and cardiovascular disease.',
        },
        {
            'emoji': '🧘',
            'title': 'Manage Stress',
            'body' : 'Chronic stress elevates cortisol, raising blood pressure and blood sugar. Try meditation, deep breathing, or yoga.',
        },
        {
            'emoji': '🚭',
            'title': 'Avoid Smoking',
            'body' : 'Smoking is the leading preventable cause of cancer and heart disease. Quitting reduces risk within weeks.',
        },
        {
            'emoji': '🩺',
            'title': 'Regular Check-ups',
            'body' : 'Annual health screenings catch problems early when they are most treatable. Do not skip routine tests.',
        },
        {
            'emoji': '🍎',
            'title': 'Whole Foods First',
            'body' : 'Minimally processed whole foods reduce inflammation, improve gut health, and lower chronic disease risk.',
        },
        {
            'emoji': '🏋️',
            'title': 'Strength Training',
            'body' : 'Two sessions of resistance training per week improves insulin sensitivity and protects bone density.',
        },
        {
            'emoji': '☀️',
            'title': 'Vitamin D',
            'body' : 'Vitamin D deficiency is linked to depression, weakened immunity, and increased cancer risk. Get 15 min of sun daily.',
        },
        {
            'emoji': '🫁',
            'title': 'Deep Breathing',
            'body' : 'Five minutes of deep diaphragmatic breathing lowers blood pressure and activates the parasympathetic nervous system.',
        },
        {
            'emoji': '🧠',
            'title': 'Stay Mentally Active',
            'body' : 'Reading, puzzles, and learning new skills build cognitive reserve and reduce the risk of neurodegenerative diseases.',
        },
    ]

    # Rotate based on day of year for daily variety
    day_of_year = datetime.utcnow().timetuple().tm_yday
    start_index = day_of_year % len(all_tips)

    # Wrap around if count exceeds remaining tips
    selected = []
    for i in range(count):
        selected.append(all_tips[(start_index + i) % len(all_tips)])

    return selected


# ============================================================
# FILE UPLOAD VALIDATOR
# ============================================================
def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """
    Validates that an uploaded filename has an allowed extension.

    Args:
        filename          : Original filename from the upload
        allowed_extensions: Set of allowed extensions e.g. {'pdf','jpg'}
                           Defaults to {'pdf','png','jpg','jpeg'}

    Returns:
        True if allowed, False otherwise

    Example:
        allowed_file('report.pdf')   → True
        allowed_file('malware.exe')  → False
    """
    if allowed_extensions is None:
        allowed_extensions = {'pdf', 'png', 'jpg', 'jpeg'}

    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in allowed_extensions
    )


# ============================================================
# SAFE FILENAME GENERATOR
# ============================================================
def generate_safe_filename(original_filename: str, user_id: int) -> str:
    """
    Creates a safe, unique filename for uploaded files.
    Prevents directory traversal and filename collision attacks.

    Args:
        original_filename: The filename provided by the user
        user_id          : The ID of the uploading user

    Returns:
        Safe filename string with timestamp and user prefix

    Example:
        generate_safe_filename('my report.pdf', 42)
        → 'u42_20250508_143022_my_report.pdf'
    """
    import unicodedata

    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', original_filename)

    # Keep only safe characters
    filename = re.sub(r'[^\w\s\-.]', '', filename).strip()

    # Replace spaces with underscores
    filename = re.sub(r'[\s]+', '_', filename)

    # Add user prefix and timestamp for uniqueness
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    return f'u{user_id}_{timestamp}_{filename}'


# ============================================================
# JSON RESPONSE BUILDER
# ============================================================
def build_json_response(
    success : bool,
    message : str  = '',
    data    : Any  = None,
    errors  : list = None,
    status  : int  = 200
) -> tuple:
    """
    Builds a standardised JSON response for AJAX endpoints.
    All AJAX routes return this consistent structure.

    Args:
        success : True if operation succeeded
        message : Human-readable status message
        data    : Any serialisable payload to include
        errors  : List of error strings (for validation failures)
        status  : HTTP status code (default 200)

    Returns:
        Tuple of (flask.Response, int) ready for return from a route

    Example:
        return build_json_response(
            success = True,
            message = 'Prediction complete.',
            data    = {'risk': 'Low', 'confidence': 23.4},
        )
    """
    from flask import jsonify

    payload = {
        'success': success,
        'message': message,
    }

    if data is not None:
        payload['data'] = data

    if errors:
        payload['errors'] = errors

    return jsonify(payload), status


# ============================================================
# PAGINATION HELPER
# ============================================================
def paginate_query(query, page: int, per_page: int = 10):
    """
    Wraps a SQLAlchemy query with pagination.
    Returns a standardised pagination context dict for templates.

    Args:
        query   : SQLAlchemy query object (not yet executed)
        page    : Current page number (1-indexed)
        per_page: Records per page (default 10)

    Returns:
        Dict with keys:
            items      → list of records for current page
            total      → total record count
            pages      → total page count
            page       → current page number
            has_prev   → True if previous page exists
            has_next   → True if next page exists
            prev_num   → previous page number or None
            next_num   → next page number or None
    """
    page     = max(1, page)
    per_page = max(1, min(per_page, 100))   # Clamp between 1 and 100

    paginated = query.paginate(
        page     = page,
        per_page = per_page,
        error_out= False
    )

    return {
        'items'   : paginated.items,
        'total'   : paginated.total,
        'pages'   : paginated.pages,
        'page'    : paginated.page,
        'has_prev': paginated.has_prev,
        'has_next': paginated.has_next,
        'prev_num': paginated.prev_num,
        'next_num': paginated.next_num,
    }


# ============================================================
# DATE FORMATTER
# ============================================================
def format_datetime(
    dt     : Optional[datetime],
    style  : str = 'full'
) -> str:
    """
    Formats a datetime object into a readable string.
    Used in Jinja2 templates via a registered template filter.

    Args:
        dt   : datetime object to format
        style: 'full'  → 'May 08, 2025 · 02:30 PM'
               'short' → 'May 08, 2025'
               'time'  → '02:30 PM'
               'iso'   → '2025-05-08T14:30:00'
               'ago'   → '3 days ago'

    Returns:
        Formatted string, or 'N/A' if dt is None
    """
    if dt is None:
        return 'N/A'

    formats = {
        'full' : '%B %d, %Y · %I:%M %p',
        'short': '%B %d, %Y',
        'time' : '%I:%M %p',
        'iso'  : '%Y-%m-%dT%H:%M:%S',
    }

    if style == 'ago':
        days = calculate_days_since(dt)
        if days == 0:
            return 'Today'
        elif days == 1:
            return 'Yesterday'
        elif days < 7:
            return f'{days} days ago'
        elif days < 30:
            weeks = days // 7
            return f'{weeks} week{"s" if weeks > 1 else ""} ago'
        elif days < 365:
            months = days // 30
            return f'{months} month{"s" if months > 1 else ""} ago'
        else:
            years = days // 365
            return f'{years} year{"s" if years > 1 else ""} ago'

    fmt = formats.get(style, formats['full'])
    return dt.strftime(fmt)


# ============================================================
# REGISTER JINJA2 TEMPLATE FILTERS
# ============================================================
def register_template_filters(app) -> None:
    """
    Registers custom Jinja2 template filters with the Flask app.
    Call this from app.py after the app is created.

    Usage in templates:
        {{ prediction.created_at | datetime_format('ago') }}
        {{ prediction.created_at | datetime_format('short') }}
        {{ user.email | mask_email }}
    """

    @app.template_filter('datetime_format')
    def datetime_format_filter(dt, style='full'):
        return format_datetime(dt, style)

    @app.template_filter('mask_email')
    def mask_email_filter(email: str) -> str:
        """
        Partially hides an email for privacy display.
        Example: john.doe@example.com → jo***@example.com
        """
        if not email or '@' not in email:
            return email
        local, domain = email.split('@', 1)
        masked_local  = local[:2] + '***' if len(local) > 2 else '***'
        return f'{masked_local}@{domain}'

    @app.template_filter('risk_badge')
    def risk_badge_filter(risk_level: str) -> str:
        """
        Converts a risk level string into an HTML badge.
        Example: 'Low' → '<span class="badge badge-success">Low</span>'
        """
        css_map = {
            'Low'     : 'success',
            'Moderate': 'warning',
            'High'    : 'danger',
        }
        css = css_map.get(risk_level, 'secondary')
        return f'<span class="risk-badge risk-{css.lower()}">{risk_level}</span>'