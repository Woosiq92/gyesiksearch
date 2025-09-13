from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    DECIMAL,
    JSON,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True)
    input_type = Column(String(20), nullable=False)  # microphone, file, spotify
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    # 관계
    recommendations = relationship("Recommendation", back_populates="session")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String(36), ForeignKey("analysis_sessions.session_id"), nullable=False
    )
    spotify_track_id = Column(String(22), nullable=False)
    track_name = Column(String(255), nullable=False)
    artist_name = Column(String(255), nullable=False)
    album_name = Column(String(255), nullable=False)
    similarity_score = Column(DECIMAL(5, 2), nullable=False)
    audio_features = Column(JSON, nullable=True)
    recommendation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    session = relationship("AnalysisSession", back_populates="recommendations")


class AudioFeatures(Base):
    __tablename__ = "audio_features"

    spotify_track_id = Column(String(22), primary_key=True)
    danceability = Column(DECIMAL(3, 2), nullable=True)
    energy = Column(DECIMAL(3, 2), nullable=True)
    valence = Column(DECIMAL(3, 2), nullable=True)
    tempo = Column(DECIMAL(6, 2), nullable=True)
    key_value = Column(Integer, nullable=True)
    mode_value = Column(Integer, nullable=True)
    loudness = Column(DECIMAL(6, 2), nullable=True)
    acousticness = Column(DECIMAL(3, 2), nullable=True)
    instrumentalness = Column(DECIMAL(3, 2), nullable=True)
    speechiness = Column(DECIMAL(3, 2), nullable=True)
    liveness = Column(DECIMAL(3, 2), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    time_signature = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
