from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

# 요청 모델
class AudioAnalysisRequest(BaseModel):
    analysis_type: str  # "identification" | "feature_extraction"
    input_type: str    # "microphone" | "file" | "spotify"

class SpotifySearchRequest(BaseModel):
    query: str
    limit: int = 20

class RecommendationRequest(BaseModel):
    session_id: str
    num_recommendations: int = 10
    filters: Optional[Dict[str, Any]] = None

# 응답 모델
class AudioFeaturesResponse(BaseModel):
    danceability: Optional[float] = None
    energy: Optional[float] = None
    valence: Optional[float] = None
    tempo: Optional[float] = None
    key: Optional[int] = None
    mode: Optional[int] = None
    loudness: Optional[float] = None
    acousticness: Optional[float] = None
    instrumentalness: Optional[float] = None
    speechiness: Optional[float] = None
    liveness: Optional[float] = None
    duration_ms: Optional[int] = None
    time_signature: Optional[int] = None

class TrackInfo(BaseModel):
    track_name: str
    artist: str
    album: str
    release_year: Optional[int] = None
    spotify_id: Optional[str] = None
    confidence: Optional[float] = None

class AudioAnalysisResponse(BaseModel):
    session_id: str
    analysis_type: str
    result: Optional[TrackInfo] = None
    audio_features: Optional[AudioFeaturesResponse] = None
    analysis_reason: Optional[str] = None

class SpotifyTrack(BaseModel):
    id: str
    name: str
    artists: List[Dict[str, Any]]
    album: Dict[str, Any]
    preview_url: Optional[str] = None
    external_urls: Dict[str, str]

class SpotifySearchResponse(BaseModel):
    tracks: List[SpotifyTrack]
    total: int

class RecommendationItem(BaseModel):
    spotify_id: str
    track_name: str
    artist_name: str
    album_name: str
    similarity_score: float
    audio_features: Optional[AudioFeaturesResponse] = None
    recommendation_reason: Optional[str] = None
    preview_url: Optional[str] = None
    external_urls: Dict[str, str]

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]
    total: int
    session_id: str

# 에러 응답 모델
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int




