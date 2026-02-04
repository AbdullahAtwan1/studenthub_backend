from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# 1️⃣ إعداد OAuth2 (لو عندك تسجيل دخول)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # هنا تحلل التوكن للتحقق من المستخدم
    if token != "my-secret-token":  # مثال بسيط
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return {"username": "testuser"}

