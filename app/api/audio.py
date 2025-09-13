from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import tempfile
import os
import uuid
from datetime import datetime, timedelta
import librosa
import numpy as np

from app.models.schemas import (
    AudioAnalysisRequest,
    AudioAnalysisResponse,
    TrackInfo,
    AudioFeaturesResponse,
    ErrorResponse,
)
from app.services.audio_analyzer_simple import AudioAnalyzer
from app.services.spotify_service import SpotifyService
from app.services.chatgpt_service import ChatGPTService

router = APIRouter()

# 서비스 인스턴스
audio_analyzer = AudioAnalyzer()
spotify_service = SpotifyService()
# chatgpt_service = ChatGPTService()  # 임시 비활성화

# 분석 결과 저장소 (메모리 기반)
analysis_sessions = {}


@router.post("/analyze", response_model=AudioAnalysisResponse)
async def analyze_audio(
    file: UploadFile = File(...),
    analysis_type: str = Form(...),
    input_type: str = Form(...),
):
    """
    오디오 파일을 분석합니다.

    Args:
        file: 업로드된 오디오 파일
        analysis_type: 분석 유형 ("identification" | "feature_extraction")
        input_type: 입력 유형 ("microphone" | "file" | "spotify")

    Returns:
        분석 결과
    """
    try:
        # 파일 유효성 검사
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")

        # 파일 확장자 검사 (더 유연하게 처리)
        file_extension = os.path.splitext(file.filename)[1].lower()
        allowed_extensions = [
            ".mp3",
            ".wav",
            ".flac",
            ".m4a",
            ".aac",
            ".webm",
            ".mp4",
            ".ogg",
        ]

        # Content-Type 기반으로 실제 형식 확인
        content_type = file.content_type or ""
        actual_extension = file_extension

        if "webm" in content_type:
            actual_extension = ".webm"
        elif "mp4" in content_type:
            actual_extension = ".mp4"
        elif "ogg" in content_type:
            actual_extension = ".ogg"
        elif "wav" in content_type:
            actual_extension = ".wav"

        if actual_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(allowed_extensions)}",
            )

        # 임시 파일로 저장 (실제 형식에 맞는 확장자 사용)
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=actual_extension
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # 오디오 분석
            features = audio_analyzer.extract_features(temp_file_path)

            # 오디오 데이터 로드 (추가 분석용)
            try:
                y, sr = audio_analyzer._load_audio_safely(temp_file_path)
                if y is None or len(y) == 0:
                    y, sr = None, 44100  # 기본값
            except:
                y, sr = None, 44100  # 기본값

            # 실제 계산된 템포 가져오기
            actual_tempo = features.get("tempo", 120)
            if y is not None and len(y) > sr * 5:  # 최소 5초 이상
                try:
                    # calculate_danceability에서 계산된 템포 사용
                    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                    actual_tempo = float(tempo)
                    print(
                        f"실제 계산된 템포: {actual_tempo:.1f} BPM (오디오 길이: {len(y)/sr:.1f}초)"
                    )
                except Exception as e:
                    print(f"템포 계산 실패: {e}")
                    actual_tempo = features.get("tempo", 120)
            else:
                print(
                    f"오디오가 너무 짧음: {len(y)/sr if y is not None else 0:.1f}초, 기본 템포 사용"
                )

            # Spotify Audio Features 형식으로 변환
            audio_features = AudioFeaturesResponse(
                danceability=(
                    audio_analyzer.calculate_danceability(y, sr)
                    if y is not None
                    else 0.5
                ),
                energy=audio_analyzer.calculate_energy(y, sr) if y is not None else 0.5,
                valence=(
                    audio_analyzer.calculate_valence(y, sr) if y is not None else 0.5
                ),
                tempo=actual_tempo,
                key=audio_analyzer.estimate_key_and_mode(temp_file_path)[0],
                mode=audio_analyzer.estimate_key_and_mode(temp_file_path)[1],
                loudness=features.get("rms_mean", 0) * 100,  # 대략적인 변환
                acousticness=0.5,  # 기본값
                instrumentalness=0.5,  # 기본값
                speechiness=0.1,  # 기본값
                liveness=0.1,  # 기본값
                duration_ms=int(features.get("duration", 0) * 1000),
                time_signature=4,  # 기본값
            )

            # ChatGPT 분석 (임시 비활성화)
            analysis_reason = "오디오 특징 분석 완료"
            # if chatgpt_service.api_key:
            #     features_dict = audio_features.dict()
            #     analysis_reason = chatgpt_service.analyze_audio_features(features_dict)

            # 곡 식별 (현재는 기본값 반환)
            track_info = None
            if analysis_type == "identification":
                track_info = TrackInfo(
                    track_name="식별된 곡 없음",
                    artist="Unknown",
                    album="Unknown",
                    confidence=0.0,
                )

            # 세션 ID 생성
            session_id = str(uuid.uuid4())

            # 분석 결과를 세션에 저장
            analysis_sessions[session_id] = {
                "audio_features": audio_features,
                "analysis_reason": analysis_reason,
                "track_info": track_info,
                "timestamp": datetime.now(),
                "analysis_type": analysis_type,
                "input_type": input_type,
            }
            print(f"분석 세션 저장 완료: {session_id}")
            print(
                f"저장된 오디오 특징: danceability={audio_features.danceability:.2f}, energy={audio_features.energy:.2f}, valence={audio_features.valence:.2f}, tempo={audio_features.tempo:.1f}"
            )

            return AudioAnalysisResponse(
                session_id=session_id,
                analysis_type=analysis_type,
                result=track_info,
                audio_features=audio_features,
                analysis_reason=analysis_reason,
            )

        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"오디오 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/analyze/spotify", response_model=AudioAnalysisResponse)
async def analyze_spotify_track(track_id: str = Form(...)):
    """
    Spotify 트랙을 분석합니다.

    Args:
        track_id: Spotify 트랙 ID

    Returns:
        분석 결과
    """
    try:
        # Spotify에서 트랙 정보 가져오기
        track_info = spotify_service.get_track_info(track_id)
        if not track_info:
            raise HTTPException(status_code=404, detail="트랙을 찾을 수 없습니다.")

        # Audio Features 가져오기
        audio_features_data = spotify_service.get_audio_features(track_id)
        if not audio_features_data:
            raise HTTPException(
                status_code=404, detail="Audio Features를 찾을 수 없습니다."
            )

        # Audio Features 변환
        audio_features = AudioFeaturesResponse(
            danceability=audio_features_data.get("danceability"),
            energy=audio_features_data.get("energy"),
            valence=audio_features_data.get("valence"),
            tempo=audio_features_data.get("tempo"),
            key=audio_features_data.get("key"),
            mode=audio_features_data.get("mode"),
            loudness=audio_features_data.get("loudness"),
            acousticness=audio_features_data.get("acousticness"),
            instrumentalness=audio_features_data.get("instrumentalness"),
            speechiness=audio_features_data.get("speechiness"),
            liveness=audio_features_data.get("liveness"),
            duration_ms=audio_features_data.get("duration_ms"),
            time_signature=audio_features_data.get("time_signature"),
        )

        # ChatGPT 분석 (임시 비활성화)
        analysis_reason = "Spotify 트랙 분석 완료"
        # if chatgpt_service.api_key:
        #     analysis_reason = chatgpt_service.analyze_audio_features(
        #         audio_features_data, track_info
        #     )

        # 트랙 정보 변환
        track_info_response = TrackInfo(
            track_name=track_info["name"],
            artist=", ".join(track_info["artists"]),
            album=track_info["album"]["name"],
            spotify_id=track_info["id"],
            confidence=1.0,
        )

        # 세션 ID 생성
        session_id = str(uuid.uuid4())

        return AudioAnalysisResponse(
            session_id=session_id,
            analysis_type="identification",
            result=track_info_response,
            audio_features=audio_features,
            analysis_reason=analysis_reason,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Spotify 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/features/{track_id}", response_model=AudioFeaturesResponse)
async def get_audio_features(track_id: str):
    """
    특정 트랙의 Audio Features를 가져옵니다.

    Args:
        track_id: Spotify 트랙 ID

    Returns:
        Audio Features
    """
    try:
        features_data = spotify_service.get_audio_features(track_id)
        if not features_data:
            raise HTTPException(
                status_code=404, detail="Audio Features를 찾을 수 없습니다."
            )

        return AudioFeaturesResponse(
            danceability=features_data.get("danceability"),
            energy=features_data.get("energy"),
            valence=features_data.get("valence"),
            tempo=features_data.get("tempo"),
            key=features_data.get("key"),
            mode=features_data.get("mode"),
            loudness=features_data.get("loudness"),
            acousticness=features_data.get("acousticness"),
            instrumentalness=features_data.get("instrumentalness"),
            speechiness=features_data.get("speechiness"),
            liveness=features_data.get("liveness"),
            duration_ms=features_data.get("duration_ms"),
            time_signature=features_data.get("time_signature"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Audio Features 조회 중 오류가 발생했습니다: {str(e)}",
        )
