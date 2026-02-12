from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.comment import Comment
from app.dependencies import get_current_user
import shutil, os

router = APIRouter(prefix="/comments", tags=["Comments"])

@router.post("/{post_id}")
def add_comment(
    post_id: int,
    text: str = None,
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    image_path = None
    if image:
        os.makedirs("uploads", exist_ok=True)
        image_path = f"uploads/{image.filename}"
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    comment = Comment(
        user_id=user.id,
        post_id=post_id,
        text=text,
        image=image_path
    )
    db.add(comment)
    db.commit()

    return {"message": "Comment added"}
