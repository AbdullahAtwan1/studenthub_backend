from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db.session import engine
from app.db.base_class import Base
import app.models  # ✅ this imports BOTH user and otp automatically
from app.routers.auth import router as auth_router
from app.routers import courses, events, polls, chat, notifications, post_course


app = FastAPI(title="StudentHub Authentication")

# create tables (إذا لم يكن يتم في مكان آخر)
Base.metadata.create_all(bind=engine)

# include routers
app.include_router(courses.router)
app.include_router(events.router)
app.include_router(polls.router)
app.include_router(chat.router)
app.include_router(notifications.router)
app.include_router(post_course.router)

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
