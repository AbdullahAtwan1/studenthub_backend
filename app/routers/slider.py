import os
from typing import List, Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.schemas.slider import HomeSliderCreate, HomeSliderOut, HomeSliderUpdate
from app.services.slider_service import (
    bulk_reorder_slider,
    create_slider_item,
    delete_slider_item,
    get_all_slider_items,
    update_slider_item,
)

from app.core.security import get_current_user
from app.core.permissions import require_role
from app.models.user import User, UserRole

router = APIRouter(
    prefix="/admin/slider",
    tags=["Admin Slider"],
)

UPLOAD_DIR = "uploads/slider"


def ensure_upload_dir():
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================
# Upload new slider image
# =========================
@router.post("/upload", response_model=HomeSliderOut)
async def upload_slider_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])

    ensure_upload_dir()

    filename = file.filename
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    image_url = f"/uploads/slider/{filename}"

    slider_data = HomeSliderCreate(
        image_url=image_url,
        order_index=0,
        is_active=True,
    )

    slider = create_slider_item(db, slider_data)
    return slider


# =========================
# List slider items
# =========================
@router.get("", response_model=List[HomeSliderOut])
def list_slider_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])
    return get_all_slider_items(db, only_active=False)


# =========================
# Reorder slider
# =========================
class ReorderBody(BaseModel):
    order: Dict[int, int]


@router.put("/reorder-all", response_model=List[HomeSliderOut])
def reorder_slider(
    body: ReorderBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])
    return bulk_reorder_slider(db, body.order)


# =========================
# Update slider
# =========================
@router.put("/{slider_id}", response_model=HomeSliderOut)
def update_slider(
    slider_id: int,
    data: HomeSliderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])

    slider = update_slider_item(db, slider_id, data)
    if not slider:
        raise HTTPException(status_code=404, detail="Slider item not found")
    return slider


# =========================
# Delete slider
# =========================
@router.delete("/{slider_id}")
def delete_slider(
    slider_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(current_user, [UserRole.system_admin, UserRole.developer])

    ok = delete_slider_item(db, slider_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Slider item not found")
    return {"detail": "Deleted"}
