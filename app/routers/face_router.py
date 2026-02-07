from fastapi import APIRouter, UploadFile, File
from deepface import DeepFace
import os
import uuid
import shutil
import glob

router = APIRouter(prefix="/face", tags=["Face Verification"])

ID_DIR = "uploads/student_ids" 
TEMP_DIR = "uploads/temp"      

os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/verify_live")
async def verify_live_face(
    student_id: str,
    selfie: UploadFile = File(...)
):
    try:
        
        id_images = glob.glob(f"{ID_DIR}/{student_id}_*")

        if not id_images:
            return {
                "verified": False,
                "error": "Student ID card image not found"
            }

        
        id_card_path = id_images[0]

       
        selfie_path = os.path.join(
            TEMP_DIR,
            f"live_{uuid.uuid4().hex}.jpg"
        )

        with open(selfie_path, "wb") as buffer:
            shutil.copyfileobj(selfie.file, buffer)

        
        result = DeepFace.verify(
            img1_path=id_card_path,
            img2_path=selfie_path,
            model_name="ArcFace",
            detector_backend="retinaface",
            enforce_detection=True
        )

    
        os.remove(selfie_path)

        
        distance = result.get("distance")
        threshold = result.get("threshold")

        similarity = None
        if distance is not None and threshold is not None:
            similarity = max(0, (1 - (distance / threshold))) * 100

        return {
            "verified": result["verified"],
            "distance": distance,
            "threshold": threshold,
            "similarity": round(similarity, 2) if similarity else None
        }

    except Exception as e:
        return {
            "verified": False,
            "error": str(e)
        }
