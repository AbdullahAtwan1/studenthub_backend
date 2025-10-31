from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db.session import engine
from app.db.base_class import Base
import app.models  # ✅ this imports BOTH user and otp automatically
from app.routers.auth import router as auth_router


app = FastAPI(title="StudentHub Authentication")

# ✅ Create tables after models are imported
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully.")

# ✅ Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ✅ Authentication routes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.get("/")
def root():
    return {"message": "StudentHub backend is running successfully!"}
