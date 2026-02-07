from fastapi import FastAPI, Security
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine
from app.db.database import Base

# Routers
from app.routers.auth import router as auth_router
from app.routers.students import router as students_router
from app.routers.slider import router as slider_router
from app.routers.stats import router as stats_router

from app.routers.courses_admin import router as courses_admin_router
from app.routers.majors_admin import router as majors_admin_router
from app.routers.doctors_admin import router as doctors_admin_router
from app.routers.doctors_public import router as doctors_public_router
from app.routers.course_materials import router as course_materials_router

from app.routers.events_admin import router as events_admin_router
from app.routers.events_public import router as events_public_router


from app.routers.course_materials_upload import (
    router as course_materials_upload_router
)

# Voting
from app.routers.voting_admin import router as voting_admin_router
from app.routers.voting_public import router as voting_public_router

from app.core.security_scheme import api_key_scheme


# ---------------------------------------------------------
# CREATE APP
# ---------------------------------------------------------
app = FastAPI(title="StudentHub Backend")


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# STARTUP
# ---------------------------------------------------------
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully.")


# ---------------------------------------------------------
# STATIC FILES
# ---------------------------------------------------------
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ---------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------

# AUTH
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# STUDENTS (profile picture, profile actions)
app.include_router(students_router)

# PUBLIC
app.include_router(doctors_public_router)

# VOTING PUBLIC
app.include_router(voting_public_router)

# ADMIN
app.include_router(stats_router)
app.include_router(slider_router)
app.include_router(majors_admin_router)
app.include_router(doctors_admin_router)
app.include_router(courses_admin_router)

# VOTING ADMIN
app.include_router(voting_admin_router)

# COURSE MATERIALS (JSON / LIST)
app.include_router(course_materials_router)

# COURSE MATERIAL UPLOAD (FILES)
app.include_router(course_materials_upload_router)

# EVENTS PUBLIC
app.include_router(events_public_router)

# EVENTS ADMIN
app.include_router(events_admin_router)



# ---------------------------------------------------------
# SECURITY TEST
# ---------------------------------------------------------
@app.get("/secure-check")
def secure_check(authorization: str = Security(api_key_scheme)):
    return {"Authorization Header": authorization}


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------
@app.get("/")
def root():
    return {"message": "StudentHub backend is running successfully!"}
