from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ----------------------------
    # App Info
    # ----------------------------
    APP_NAME: str = "StudentHub Backend"
    APP_ENV: str = "dev"
    APP_DEBUG: bool = True

    # ----------------------------
    # Database (MySQL)
    # ----------------------------
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_DB: str

    # ----------------------------
    # Email Configuration
    # ----------------------------
    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USER: str
    EMAIL_PASS: str
    EMAIL_FROM: str

    # ----------------------------
    # OTP Configuration
    # ----------------------------
    OTP_LENGTH: int = 6
    OTP_TTL_MINUTES: int = 15

    # ----------------------------
    # JWT Configuration
    # ----------------------------
    JWT_SECRET: str = "change_this_to_a_long_random_secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Generate the database connection URI"""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"
        )


settings = Settings()
