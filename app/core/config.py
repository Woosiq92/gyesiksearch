from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API 설정
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "MusicMatch"

    # 데이터베이스 설정 (현재 사용하지 않음)
    # DATABASE_URL: str = "postgresql://user:password@localhost/musicmatch"

    # Spotify API 설정
    SPOTIFY_CLIENT_ID: Optional[str] = None
    SPOTIFY_CLIENT_SECRET: Optional[str] = None
    SPOTIFY_REDIRECT_URI: str = "http://127.0.0.1:3000/callback"

    # OpenAI API 설정
    OPENAI_API_KEY: Optional[str] = None

    # 파일 업로드 설정
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_AUDIO_FORMATS: list = [".mp3", ".wav", ".flac", ".m4a", ".aac"]
    UPLOAD_DIR: str = "uploads"

    # 오디오 분석 설정
    MAX_RECORDING_DURATION: int = 30  # 초
    AUDIO_SAMPLE_RATE: int = 44100

    # 보안 설정
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS 설정
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://musiksearch.netlify.app",  # Netlify URL
        "https://your-app-name.herokuapp.com",  # Heroku URL
        "https://your-app-name.up.railway.app",  # Railway URL
        "https://your-app-name.onrender.com",  # Render URL
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 추가 필드 허용


# 전역 설정 인스턴스
settings = Settings()

# 환경 변수에서 설정 로드
if os.path.exists(".env"):
    try:
        settings = Settings(_env_file=".env")
    except Exception:
        # .env 파일에 문제가 있으면 기본 설정 사용
        settings = Settings()
else:
    settings = Settings()
