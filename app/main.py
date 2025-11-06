from fastapi import FastAPI, Security
from fastapi.staticfiles import StaticFiles
from app.db.session import engine
from app.db.base_class import Base
import app.models
from app.routers.auth import router as auth_router
from app.core.security_scheme import api_key_scheme

app = FastAPI(title="StudentHub Authentication")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully.")

# ✅ Attach the header scheme globally
@app.get("/secure-check")
def secure_check(authorization: str = Security(api_key_scheme)):
    return {"Authorization Header": authorization}

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.get("/")
def root():
    return {"message": "StudentHub backend is running successfully!"}
