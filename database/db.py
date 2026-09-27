# ============================================================
# database/db.py — MediScan Pro Database & Healthcare Models
# ============================================================

import os
import uuid
from datetime import datetime, date, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ============================================================
# USER MODEL
# ============================================================
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name  = db.Column(db.String(50),  nullable=False)
    last_name   = db.Column(db.String(50),  nullable=False)
    email       = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password    = db.Column(db.String(255), nullable=False)
    age         = db.Column(db.Integer,     nullable=True)
    gender      = db.Column(db.String(10),  nullable=True)
    phone       = db.Column(db.String(20),  nullable=True)
    is_active   = db.Column(db.Boolean,     default=True,      nullable=False)
    is_verified = db.Column(db.Boolean,     default=False,     nullable=False)
    role        = db.Column(db.String(20),  default='patient', nullable=False)
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow, nullable=False)
    updated_at  = db.Column(db.DateTime,    default=datetime.utcnow, nullable=False)
    last_login  = db.Column(db.DateTime,    nullable=True)

    # Relationships
    predictions = db.relationship(
        'PredictionHistory',
        backref   = 'user',
        lazy      = 'dynamic',
        cascade   = 'all, delete-orphan'
    )

    profile = db.relationship(
        'UserProfile',
        backref   = 'user',
        uselist   = False,
        cascade   = 'all, delete-orphan'
    )

    tasks = db.relationship(
        'DailyHealthTask',
        backref   = 'user',
        lazy      = 'dynamic',
        cascade   = 'all, delete-orphan'
    )

    reports = db.relationship(
        'HealthReport',
        backref   = 'user',
        lazy      = 'dynamic',
        cascade   = 'all, delete-orphan'
    )

    def set_password(self, plain_password):
        self.password = generate_password_hash(plain_password).decode('utf-8')

    def check_password(self, plain_password):
        return check_password_hash(self.password, plain_password)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def initials(self):
        try:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        except Exception:
            return "U"

    @property
    def total_predictions(self):
        try:
            return self.predictions.count()
        except Exception:
            return 0

    @property
    def recent_predictions(self):
        try:
            return self.predictions.order_by(
                PredictionHistory.created_at.desc()
            ).limit(5).all()
        except Exception:
            return []

    @property
    def latest_prediction(self):
        try:
            return self.predictions.order_by(
                PredictionHistory.created_at.desc()
            ).first()
        except Exception:
            return None

    @property
    def current_bmi(self):
        if self.profile and self.profile.bmi:
            return self.profile.bmi
        return None

    @property
    def bmi_category(self):
        if not self.current_bmi:
            return {'label': 'Not set', 'badge': 'secondary', 'color': 'var(--text-3)'}
        bmi = self.current_bmi
        if bmi < 18.5:
            return {'label': 'Underweight', 'badge': 'warning', 'color': 'var(--amber)'}
        elif bmi < 25.0:
            return {'label': 'Normal Weight', 'badge': 'success', 'color': 'var(--green)'}
        elif bmi < 30.0:
            return {'label': 'Overweight', 'badge': 'warning', 'color': 'var(--amber)'}
        else:
            return {'label': 'Obesity', 'badge': 'danger', 'color': 'var(--red)'}

    @property
    def today_tasks_stats(self):
        today = date.today()
        today_tasks = DailyHealthTask.query.filter_by(
            user_id=self.id, target_date=today
        ).all()
        if not today_tasks:
            # Auto populate default wellness tasks for today
            DailyHealthTask.generate_default_tasks_for_user(self.id)
            today_tasks = DailyHealthTask.query.filter_by(
                user_id=self.id, target_date=today
            ).all()

        total = len(today_tasks)
        completed = sum(1 for t in today_tasks if t.is_completed)
        pct = round((completed / total * 100)) if total > 0 else 0
        return {
            'tasks': today_tasks,
            'total': total,
            'completed': completed,
            'pct': pct,
        }

    @property
    def health_streak(self):
        """Calculates consecutive days with at least one completed task."""
        streak = 0
        current_check = date.today()
        for i in range(30):
            day = current_check - timedelta(days=i)
            done = DailyHealthTask.query.filter_by(
                user_id=self.id, target_date=day, is_completed=True
            ).first()
            if done:
                streak += 1
            else:
                # If checking today and no tasks completed yet, don't break streak if yesterday was completed
                if i == 0:
                    continue
                break
        return streak

    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(
            email=email.lower().strip()
        ).first()

    @classmethod
    def get_by_id(cls, user_id):
        return cls.query.get(int(user_id))

    @classmethod
    def email_exists(cls, email):
        return cls.query.filter_by(
            email=email.lower().strip()
        ).first() is not None

    def update_last_login(self):
        try:
            self.last_login = datetime.utcnow()
            db.session.commit()
        except Exception:
            db.session.rollback()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


# ============================================================
# USER HEALTH PROFILE MODEL
# ============================================================
class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id                   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id              = db.Column(
                             db.Integer,
                             db.ForeignKey('users.id', ondelete='CASCADE'),
                             nullable=False, unique=True, index=True
                           )
    height_cm            = db.Column(db.Float,       nullable=True)
    weight_kg            = db.Column(db.Float,       nullable=True)
    bmi                  = db.Column(db.Float,       nullable=True)
    blood_group          = db.Column(db.String(10),  nullable=True)
    smoking_status       = db.Column(db.String(30),  nullable=True, default='Non-smoker')
    alcohol_status       = db.Column(db.String(30),  nullable=True, default='None')
    activity_level       = db.Column(db.String(30),  nullable=True, default='Moderately Active')
    existing_conditions  = db.Column(db.Text,        nullable=True)
    allergies            = db.Column(db.Text,        nullable=True)
    emergency_contact_name  = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(30),  nullable=True)
    updated_at           = db.Column(db.DateTime,    default=datetime.utcnow, nullable=False)

    def calculate_bmi(self):
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            height_m = self.height_cm / 100.0
            self.bmi = round(self.weight_kg / (height_m * height_m), 1)
        else:
            self.bmi = None
        return self.bmi

    def save(self):
        self.calculate_bmi()
        self.updated_at = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f"<UserProfile user_id={self.user_id} bmi={self.bmi}>"


# ============================================================
# PREDICTION HISTORY MODEL
# ============================================================
class PredictionHistory(db.Model):
    __tablename__ = 'prediction_history'

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id        = db.Column(
                         db.Integer,
                         db.ForeignKey('users.id', ondelete='CASCADE'),
                         nullable=False, index=True
                     )
    disease_name   = db.Column(db.String(100), nullable=False)
    result         = db.Column(db.String(50),  nullable=False)
    risk_level     = db.Column(db.String(20),  nullable=False)
    confidence_pct = db.Column(db.Float,       nullable=False, default=0.0)
    input_data     = db.Column(db.Text,        nullable=True)
    precautions    = db.Column(db.Text,        nullable=True)
    model_used     = db.Column(db.String(100), nullable=True)
    created_at     = db.Column(
                         db.DateTime,
                         default=datetime.utcnow,
                         nullable=False, index=True
                     )

    # Relationships
    reports = db.relationship(
        'HealthReport',
        backref   = 'prediction',
        lazy      = 'dynamic',
        cascade   = 'all, delete-orphan'
    )

    @classmethod
    def get_by_user(cls, user_id, limit=None):
        try:
            q = cls.query.filter_by(user_id=user_id)\
                         .order_by(cls.created_at.desc())
            return q.limit(limit).all() if limit else q.all()
        except Exception:
            return []

    @classmethod
    def get_by_id(cls, prediction_id, user_id):
        try:
            return cls.query.filter_by(
                id=prediction_id, user_id=user_id
            ).first()
        except Exception:
            return None

    @classmethod
    def get_disease_stats(cls, user_id):
        try:
            from sqlalchemy import func
            rows = db.session.query(
                cls.disease_name,
                func.count(cls.id).label('count')
            ).filter_by(user_id=user_id)\
             .group_by(cls.disease_name).all()
            return {r.disease_name: r.count for r in rows}
        except Exception:
            return {}

    @classmethod
    def get_risk_summary(cls, user_id):
        try:
            from sqlalchemy import func
            rows = db.session.query(
                cls.risk_level,
                func.count(cls.id).label('count')
            ).filter_by(user_id=user_id)\
             .group_by(cls.risk_level).all()
            summary = {'Low': 0, 'Moderate': 0, 'High': 0}
            for r in rows:
                if r.risk_level in summary:
                    summary[r.risk_level] = r.count
            return summary
        except Exception:
            return {'Low': 0, 'Moderate': 0, 'High': 0}

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f"<Prediction id={self.id} disease={self.disease_name}>"


# ============================================================
# DAILY HEALTH TASK MODEL
# ============================================================
class DailyHealthTask(db.Model):
    __tablename__ = 'daily_health_tasks'

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id         = db.Column(
                          db.Integer,
                          db.ForeignKey('users.id', ondelete='CASCADE'),
                          nullable=False, index=True
                      )
    task_text       = db.Column(db.String(255), nullable=False)
    category        = db.Column(db.String(50),  nullable=False, default='wellness') # hydration, nutrition, exercise, monitoring
    disease_context = db.Column(db.String(100), nullable=True)
    target_date     = db.Column(db.Date,        nullable=False, default=date.today, index=True)
    is_completed    = db.Column(db.Boolean,     nullable=False, default=False)
    completed_at    = db.Column(db.DateTime,    nullable=True)
    created_at      = db.Column(db.DateTime,    default=datetime.utcnow, nullable=False)

    @classmethod
    def get_today_tasks(cls, user_id):
        today = date.today()
        tasks = cls.query.filter_by(user_id=user_id, target_date=today).all()
        if not tasks:
            cls.generate_default_tasks_for_user(user_id)
            tasks = cls.query.filter_by(user_id=user_id, target_date=today).all()
        return tasks

    @classmethod
    def toggle_task(cls, task_id, user_id):
        task = cls.query.filter_by(id=task_id, user_id=user_id).first()
        if task:
            task.is_completed = not task.is_completed
            task.completed_at = datetime.utcnow() if task.is_completed else None
            db.session.commit()
            return task
        return None

    @classmethod
    def generate_default_tasks_for_user(cls, user_id, disease_context=None):
        today = date.today()
        # Avoid duplicating tasks for today
        existing_count = cls.query.filter_by(user_id=user_id, target_date=today).count()
        if existing_count >= 5:
            return

        default_tasks = [
            {'text': 'Drink at least 2.5 litres of water', 'category': 'hydration'},
            {'text': 'Complete a 25–30 minute brisk walk or light exercise', 'category': 'exercise'},
            {'text': 'Incorporate fresh vegetables and whole grains in meals', 'category': 'nutrition'},
            {'text': 'Avoid sugary drinks, processed snacks, and excess salt', 'category': 'nutrition'},
            {'text': 'Aim for 7–8 hours of restful, uninterrupted sleep', 'category': 'wellness'},
        ]

        if disease_context == 'Diabetes Mellitus':
            default_tasks.insert(0, {'text': 'Monitor fasting blood sugar and log your values', 'category': 'monitoring'})
        elif disease_context == 'Heart Disease' or disease_context == 'Hypertension':
            default_tasks.insert(0, {'text': 'Record morning resting blood pressure and pulse', 'category': 'monitoring'})
        elif disease_context == 'Kidney Disease':
            default_tasks.insert(0, {'text': 'Track daily water intake and avoid high-sodium foods', 'category': 'hydration'})

        for item in default_tasks[:5]:
            task = cls(
                user_id=user_id,
                task_text=item['text'],
                category=item['category'],
                disease_context=disease_context,
                target_date=today,
                is_completed=False
            )
            db.session.add(task)
        db.session.commit()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f"<DailyHealthTask id={self.id} user={self.user_id} done={self.is_completed}>"


# ============================================================
# HEALTH REPORT MODEL
# ============================================================
class HealthReport(db.Model):
    __tablename__ = 'health_reports'

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    report_uuid    = db.Column(db.String(36),  nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    user_id        = db.Column(
                         db.Integer,
                         db.ForeignKey('users.id', ondelete='CASCADE'),
                         nullable=False, index=True
                     )
    prediction_id  = db.Column(
                         db.Integer,
                         db.ForeignKey('prediction_history.id', ondelete='CASCADE'),
                         nullable=False, index=True
                     )
    filename       = db.Column(db.String(255), nullable=False)
    file_size      = db.Column(db.Integer,     nullable=True, default=0)
    created_at     = db.Column(db.DateTime,    default=datetime.utcnow, nullable=False)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f"<HealthReport id={self.id} uuid={self.report_uuid}>"


def init_db():
    db.create_all()


def reset_db():
    db.drop_all()
    db.create_all()