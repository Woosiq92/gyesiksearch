from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
async def test_analyze():
    return {
        "message": "Test endpoint working",
        "status": "success",
        "audio_features": {
            "danceability": 0.5,
            "energy": 0.5,
            "valence": 0.5,
            "tempo": 120,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
