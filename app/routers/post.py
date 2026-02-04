from fastapi import APIRouter,UploadFile,File, Depends
from sqlalchemy.orm import Session
from app.models.post import Post
from app.schemas.post import PostCreate
from app.dependencies import get_current_user
import uuid
import os
from app.db.database import get_db

router = APIRouter(prefix="/posts", tags=["Posts"])

@router.post("/")
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    new_post = Post(
        user_id=user.id,
        content=post.content,
        image=post.image
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@router.get("/my-posts")
def get_my_posts(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    return db.query(Post).filter(Post.user_id == user.id).all()

@router.post("/upload-image")
def upload_post_image(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"uploads/posts/{filename}"

    os.makedirs("uploads/posts", exist_ok=True)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    return {
        "image_url": f"/uploads/posts/{filename}"
    }

