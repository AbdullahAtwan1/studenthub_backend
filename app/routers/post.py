from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.post import Post
from app.models.post_image import PostImage
from app.dependencies import get_current_user
import shutil, os

router = APIRouter(prefix="/posts", tags=["Posts"])

@router.post("/")
def create_post(
    content: str = None,
    images: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    post = Post(user_id=user.id, content=content)
    db.add(post)
    db.commit()
    db.refresh(post)

    if images:
        os.makedirs("uploads", exist_ok=True)
        for img in images:
            path = f"uploads/{img.filename}"
            with open(path, "wb") as buffer:
                shutil.copyfileobj(img.file, buffer)
            db.add(PostImage(post_id=post.id, image_path=path))

        db.commit()

    return {"message": "Post created successfully"}
