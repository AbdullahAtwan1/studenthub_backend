import cv2
import numpy as np
import easyocr
import os

LOGO_TEMPLATE = "app/ai/reference/bzu_logo_template.png"
reader = easyocr.Reader(['en', 'ar'], gpu=False)

def verify_bzu_card(uploaded_path: str, student_id: str, student_name: str):

    print("\n===================== BZU CARD VERIFICATION =====================")
    print("📌 Uploaded image:", uploaded_path)
    print("\n🔥🔥 ENTERED verify_bzu_card() 🔥🔥")

    # ---- Load images safely ----
    img_card_color = cv2.imread(uploaded_path)
    img_card = cv2.cvtColor(img_card_color, cv2.COLOR_BGR2GRAY)
    img_logo = cv2.imread(LOGO_TEMPLATE, cv2.IMREAD_GRAYSCALE)

    if img_card is None:
        return False, "Could not read uploaded image", None
    if img_logo is None:
        return False, "Could not read logo template", None

    # ---- ORB Match for logo detection ----
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img_logo, None)
    kp2, des2 = orb.detectAndCompute(img_card, None)

    if des1 is None or des2 is None:
        return False, "Card image too blurry", None

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)

    print("👉 ORB matches:", len(matches))
    if len(matches) < 15:
        return False, "BZU logo not detected", None

    # ---- OCR Text Extraction ----
    ocr_text = reader.readtext(uploaded_path, detail=0)
    full_text = " ".join(ocr_text).lower()

    print("\n📝 OCR TEXT:", full_text)

    # --- Verify student name ---
    # if student_name.lower().split()[0] not in full_text:
    #     return False, "Name mismatch", None

    # --- Verify student ID ---
    if student_id not in full_text:
        return False, "Student ID mismatch", None

    # ---- Extract photo from card ----
    h, w, _ = img_card_color.shape

    # منطقة الصورة حسب تصميم بطاقة بيرزيت
    x1 = int(w * 0.01)
    y1 = int(h * 0.12)
    x2 = int(w * 0.28)
    y2 = int(h * 0.62)

    face_crop = img_card_color[y1:y2, x1:x2]

    # مسار تخزين صورة الطالب
    photo_filename = f"student_{student_id}.jpg"
    save_path = f"uploads/student_faces/{photo_filename}"

    os.makedirs("uploads/student_faces", exist_ok=True)
    cv2.imwrite(save_path, face_crop)

    print("📸 Extracted face saved at:", save_path)

    return True, "Card verified successfully", save_path
