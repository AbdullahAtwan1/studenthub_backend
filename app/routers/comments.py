from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.comment import Comment
from app.schemas.comment import CommentCreate
from app.dependencies import get_current_user

router = APIRouter(prefix="/comments", tags=["Comments"])

@router.post("/{post_id}")
def add_comment(
    post_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    new_comment = Comment(
        user_id=user.id,
        post_id=post_id,
        content=comment.content,
        image=comment.image
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment
