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
