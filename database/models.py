# ============================================================
# database/models.py — Re-export models for modular imports
# ============================================================

from database.db import (
    db,
    User,
    UserProfile,
    PredictionHistory,
    DailyHealthTask,
    HealthReport,
    init_db,
    reset_db
)

__all__ = [
    'db',
    'User',
    'UserProfile',
    'PredictionHistory',
    'DailyHealthTask',
    'HealthReport',
    'init_db',
    'reset_db'
]
