from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="MusicMatch Test Server")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "MusicMatch Test Server is running!"}


@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Server is running"}


@app.post("/api/v1/audio/analyze")
async def test_analyze(
    file: UploadFile = File(...),
    analysis_type: str = Form(...),
    input_type: str = Form(...),
):
    """테스트용 오디오 분석 엔드포인트"""
    return {
        "message": "Test endpoint working",
        "status": "success",
        "session_id": "test-session-123",
        "audio_features": {
            "danceability": 0.7,
            "energy": 0.8,
            "valence": 0.6,
            "tempo": 120,
            "acousticness": 0.3,
            "instrumentalness": 0.1,
            "liveness": 0.2,
            "speechiness": 0.1,
        },
        "analysis_reason": "테스트용 오디오 분석 결과입니다. 이 곡은 활기찬 댄스 음악으로, 높은 에너지와 중간 정도의 긍정적인 감정을 가지고 있습니다.",
        "track_info": {
            "track_name": "테스트 곡",
            "artist": "테스트 아티스트",
            "album": "테스트 앨범",
            "confidence": 0.95,
        },
    }


@app.post("/api/v1/recommendations/similar")
async def test_recommendations(request: dict):
    """테스트용 추천 엔드포인트"""
    return {
        "recommendations": [
            {
                "spotify_id": "test1",
                "track_name": "추천 곡 1",
                "artist": "추천 아티스트 1",
                "album": "추천 앨범 1",
                "preview_url": None,
                "external_urls": {"spotify": "https://open.spotify.com/track/test1"},
                "recommendation_reason": "비슷한 템포와 에너지를 가지고 있어 추천합니다.",
            },
            {
                "spotify_id": "test2",
                "track_name": "추천 곡 2",
                "artist": "추천 아티스트 2",
                "album": "추천 앨범 2",
                "preview_url": None,
                "external_urls": {"spotify": "https://open.spotify.com/track/test2"},
                "recommendation_reason": "유사한 음악적 특성을 보여 추천합니다.",
            },
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
