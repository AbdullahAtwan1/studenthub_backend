"""
This file ensures that all SQLAlchemy models are imported
so that Base.metadata.create_all() in main.py recognizes them.
"""

from app.models.user import User
from app.models.otp import OTP

# Optionally, you can define __all__ for clarity
__all__ = ["User", "OTP"]
