from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from app.models.schemas import SpotifySearchResponse, SpotifyTrack
from app.services.spotify_service import SpotifyService

router = APIRouter()

# 서비스 인스턴스
spotify_service = SpotifyService()


@router.get("/search")
async def search_tracks(q: str, limit: int = 20):
    """
    Spotify에서 곡을 검색합니다.

    Args:
        q: 검색 쿼리
        limit: 결과 개수 제한

    Returns:
        검색 결과
    """
    try:
        tracks = spotify_service.search_tracks(q, limit)

        spotify_tracks = []
        for track in tracks:
            spotify_track = SpotifyTrack(
                id=track["id"],
                name=track["name"],
                artists=track["artists"],
                album=track["album"],
                preview_url=track.get("preview_url"),
                external_urls=track.get("external_urls", {}),
            )
            spotify_tracks.append(spotify_track)

        return SpotifySearchResponse(tracks=spotify_tracks, total=len(spotify_tracks))

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/track/{track_id}")
async def get_track_info(track_id: str):
    """
    특정 트랙의 상세 정보를 가져옵니다.

    Args:
        track_id: Spotify 트랙 ID

    Returns:
        트랙 정보
    """
    try:
        track_info = spotify_service.get_track_info(track_id)
        if not track_info:
            raise HTTPException(status_code=404, detail="트랙을 찾을 수 없습니다.")

        return track_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"트랙 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/features/{track_id}")
async def get_audio_features(track_id: str):
    """
    특정 트랙의 Audio Features를 가져옵니다.

    Args:
        track_id: Spotify 트랙 ID

    Returns:
        Audio Features
    """
    try:
        features = spotify_service.get_audio_features(track_id)
        if not features:
            raise HTTPException(
                status_code=404, detail="Audio Features를 찾을 수 없습니다."
            )

        return features

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Audio Features 조회 중 오류가 발생했습니다: {str(e)}",
        )


@router.get("/genres")
async def get_genre_seeds():
    """
    사용 가능한 장르 시드를 가져옵니다.

    Returns:
        장르 리스트
    """
    try:
        genres = spotify_service.get_genre_seeds()
        return {"genres": genres}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"장르 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/recommendations")
async def get_recommendations(
    seed_tracks: List[str], limit: int = 10, target_features: Dict[str, Any] = None
):
    """
    Spotify 추천 API를 사용하여 유사한 곡을 가져옵니다.

    Args:
        seed_tracks: 시드 트랙 ID 리스트
        limit: 추천 곡 개수
        target_features: 타겟 Audio Features

    Returns:
        추천 곡 리스트
    """
    try:
        recommendations = spotify_service.get_recommendations(
            seed_tracks=seed_tracks, limit=limit, target_features=target_features
        )

        return {"recommendations": recommendations}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"추천 조회 중 오류가 발생했습니다: {str(e)}"
        )
