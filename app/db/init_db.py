from app.db.base_class import Base
from app.db.session import engine

# ✅ Import ALL models here
from app.models.user import User
from app.models.otp import OTP

def init_db():
    print("✅ Creating all tables...")
    Base.metadata.create_all(bind=engine)
