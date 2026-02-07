from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.slider import HomeSlider
from app.schemas.slider import HomeSliderCreate, HomeSliderUpdate


def create_slider_item(db: Session, data: HomeSliderCreate) -> HomeSlider:
    slider = HomeSlider(
        image_url=data.image_url,
        order_index=data.order_index,
        is_active=data.is_active,
    )
    db.add(slider)
    db.commit()
    db.refresh(slider)
    return slider


def get_all_slider_items(db: Session, only_active: bool = False) -> List[HomeSlider]:
    query = db.query(HomeSlider)
    if only_active:
        query = query.filter(HomeSlider.is_active.is_(True))
    return query.order_by(HomeSlider.order_index.asc(), HomeSlider.id.asc()).all()


def get_slider_item(db: Session, slider_id: int) -> Optional[HomeSlider]:
    return db.query(HomeSlider).filter(HomeSlider.id == slider_id).first()


def update_slider_item(
    db: Session, slider_id: int, data: HomeSliderUpdate
) -> Optional[HomeSlider]:
    slider = get_slider_item(db, slider_id)
    if not slider:
        return None

    if data.order_index is not None:
        slider.order_index = data.order_index
    if data.is_active is not None:
        slider.is_active = data.is_active

    db.commit()
    db.refresh(slider)
    return slider


def delete_slider_item(db: Session, slider_id: int) -> bool:
    slider = get_slider_item(db, slider_id)
    if not slider:
        return False

    db.delete(slider)
    db.commit()
    return True


def bulk_reorder_slider(
    db: Session, id_to_order: dict[int, int]
) -> List[HomeSlider]:
    """id_to_order: {slider_id: new_order_index}"""
    sliders = db.query(HomeSlider).filter(HomeSlider.id.in_(id_to_order.keys())).all()

    for slider in sliders:
        if slider.id in id_to_order:
            slider.order_index = id_to_order[slider.id]

    db.commit()
    for slider in sliders:
        db.refresh(slider)
    return sliders
