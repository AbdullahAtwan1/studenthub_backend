from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.like import Like
from app.dependencies import get_current_user

router = APIRouter(prefix="/likes", tags=["Likes"])

@router.post("/{post_id}")
def like_post(post_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    like = Like(user_id=user.id, post_id=post_id)
    db.add(like)
    db.commit()
    return {"message": "Post liked"}
