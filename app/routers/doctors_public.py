from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app.db.session import get_db
from app.schemas.doctor import DoctorCreate, DoctorOut
from app.db.models import Doctor

router = APIRouter(prefix="/doctors", tags=["Doctors"])


# -------------------------
# GET ALL DOCTORS
# -------------------------
@router.get("", response_model=List[DoctorOut])
def list_doctors(db: Session = Depends(get_db)):
    return db.query(Doctor).order_by(Doctor.full_name).all()


# -------------------------
# ADD DOCTOR
# -------------------------
@router.post("", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(data: DoctorCreate, db: Session = Depends(get_db)):
    doctor = Doctor(
        full_name=data.full_name,
        email=data.email,
        department=data.department,  # ✅ REQUIRED FIX
    )

    db.add(doctor)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor with this email already exists",
        )

    db.refresh(doctor)
    return doctor


# -------------------------
# DELETE DOCTOR
# -------------------------
@router.delete("/{doctor_id}", status_code=status.HTTP_200_OK)
def delete_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    db.delete(doctor)
    db.commit()

    return {"message": "Doctor deleted successfully"}
