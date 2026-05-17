# ============================================================
# database/db.py — Fixed Version
# ============================================================

import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash, check_password_hash

db = SQLAlchemy()


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

    predictions = db.relationship(
        'PredictionHistory',
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


def init_db():
    db.create_all()


def reset_db():
    db.drop_all()
    db.create_all()