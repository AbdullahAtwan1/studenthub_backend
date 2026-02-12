from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db.session import engine
from app.db.base_class import Base
import app.models  # يستورد كل الـ models (user, otp, message, post ...)

from app.routers.auth import router as auth_router
from app.routers import chat, notifications, messages, post,likes,comments,saved_posts
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.saved_post import SavedPost
from app.dependencies import get_current_user

router = APIRouter(prefix="/saved-posts", tags=["Saved Posts"])

@router.post("/{post_id}")
def save_post(post_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    saved = SavedPost(user_id=user.id, post_id=post_id)
    db.add(saved)
    db.commit()
    return {"message": "Post saved"}
 
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.saved_post import SavedPost
from app.dependencies import get_current_user

router = APIRouter(prefix="/saved-posts", tags=["Saved Posts"])

@router.post("/{post_id}")
def save_post(post_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    saved = SavedPost(user_id=user.id, post_id=post_id)
    db.add(saved)
    db.commit()
    return {"message": "Post saved"}


app = FastAPI(title="StudentHub Backend")

# ✅ Create tables
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")

# ✅ Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(notifications.router, tags=["Notifications"])
app.include_router(messages.router, tags=["Messages"])
app.include_router(post.router, tags=["Posts"])
app.include_router(likes.router)
app.include_router(comments.router)
app.include_router(saved_posts.router)


# ✅ Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def root():
    return {"message": "StudentHub backend is running successfully!"}
