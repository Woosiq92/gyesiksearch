from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api import audio, recommendations, spotify
from app.core.config import settings

app = FastAPI(
    title="MusicMatch API",
    description="음악 식별 및 유사곡 추천 시스템 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://gyesiksearch.netlify.app",
        "https://web-production-7d56.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(audio.router, prefix="/api/v1/audio", tags=["audio"])
app.include_router(
    recommendations.router, prefix="/api/v1/recommendations", tags=["recommendations"]
)
app.include_router(spotify.router, prefix="/api/v1/spotify", tags=["spotify"])


@app.get("/")
async def root():
    return {"message": "MusicMatch API 서버가 실행 중입니다!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
