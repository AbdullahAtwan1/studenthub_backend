from fastapi import FastAPI, Security
from fastapi.staticfiles import StaticFiles

from app.db.session import engine
from app.db.base_class import Base
import app.models

from app.routers.auth import router as auth_router
from app.core.security_scheme import api_key_scheme
from app.routers import slider


# ---------------------------------------------------------
# CREATE ONE SINGLE FASTAPI APP (VERY IMPORTANT)
# ---------------------------------------------------------
app = FastAPI(title="StudentHub Authentication")


# ---------------------------------------------------------
# STARTUP EVENT – CREATE TABLES
# ---------------------------------------------------------
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully.")


# ---------------------------------------------------------
# STATIC FILES (uploads folder)
# ---------------------------------------------------------
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ---------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------
# Auth system
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Slider system
app.include_router(slider.router, prefix="/admin", tags=["Slider"])


# ---------------------------------------------------------
# SECURITY TEST ENDPOINT
# ---------------------------------------------------------
@app.get("/secure-check")
def secure_check(authorization: str = Security(api_key_scheme)):
    return {"Authorization Header": authorization}


# ---------------------------------------------------------
# ROOT ENDPOINT
# ---------------------------------------------------------
@app.get("/")
def root():
    return {"message": "StudentHub backend is running successfully!"}
