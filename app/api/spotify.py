from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Dict, Any
import os
from app.core.config import settings

router = APIRouter()

# Spotify OAuth 설정
SPOTIFY_SCOPE = "user-read-private user-read-email user-read-recently-played user-top-read user-read-playback-state user-modify-playback-state"


def get_spotify_oauth():
    """Spotify OAuth 객체 생성"""
    return SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPE,
    )


@router.get("/login")
async def spotify_login():
    """Spotify 로그인 페이지로 리다이렉트"""
    try:
        sp_oauth = get_spotify_oauth()
        auth_url = sp_oauth.get_authorize_url()
        return RedirectResponse(url=auth_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify 로그인 오류: {str(e)}")


@router.get("/callback")
async def spotify_callback(code: str = None, error: str = None):
    """Spotify OAuth 콜백 처리"""
    if error:
        raise HTTPException(status_code=400, detail=f"Spotify 인증 오류: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="인증 코드가 없습니다")

    try:
        sp_oauth = get_spotify_oauth()
        token_info = sp_oauth.get_access_token(code)

        if not token_info:
            raise HTTPException(status_code=400, detail="토큰 발급 실패")

        # Spotify 클라이언트 생성
        sp = spotipy.Spotify(auth=token_info["access_token"])

        # 사용자 정보 가져오기
        user_info = sp.current_user()

        return {
            "success": True,
            "user": {
                "id": user_info["id"],
                "name": user_info["display_name"],
                "email": user_info.get("email", ""),
                "country": user_info.get("country", ""),
                "followers": user_info["followers"]["total"],
            },
            "token": token_info["access_token"],
            "refresh_token": token_info.get("refresh_token"),
            "expires_in": token_info["expires_in"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify 콜백 처리 오류: {str(e)}")


@router.get("/user-profile")
async def get_user_profile(token: str):
    """사용자 프로필 정보 가져오기"""
    try:
        sp = spotipy.Spotify(auth=token)
        user_info = sp.current_user()

        return {
            "id": user_info["id"],
            "name": user_info["display_name"],
            "email": user_info.get("email", ""),
            "country": user_info.get("country", ""),
            "followers": user_info["followers"]["total"],
            "images": user_info.get("images", []),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"사용자 프로필 가져오기 오류: {str(e)}"
        )


@router.get("/user-top-tracks")
async def get_user_top_tracks(
    token: str, time_range: str = "medium_term", limit: int = 20
):
    """사용자의 인기 트랙 가져오기"""
    try:
        sp = spotipy.Spotify(auth=token)
        results = sp.current_user_top_tracks(time_range=time_range, limit=limit)

        tracks = []
        for track in results["items"]:
            track_info = {
                "id": track["id"],
                "name": track["name"],
                "artists": [artist["name"] for artist in track["artists"]],
                "album": {
                    "name": track["album"]["name"],
                    "images": track["album"]["images"],
                },
                "preview_url": track["preview_url"],
                "external_urls": track["external_urls"],
                "popularity": track["popularity"],
            }
            tracks.append(track_info)

        return {"tracks": tracks}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"인기 트랙 가져오기 오류: {str(e)}"
        )


@router.get("/user-recently-played")
async def get_user_recently_played(token: str, limit: int = 20):
    """사용자의 최근 재생 곡 가져오기"""
    try:
        sp = spotipy.Spotify(auth=token)
        results = sp.current_user_recently_played(limit=limit)

        tracks = []
        for item in results["items"]:
            track = item["track"]
            track_info = {
                "id": track["id"],
                "name": track["name"],
                "artists": [artist["name"] for artist in track["artists"]],
                "album": {
                    "name": track["album"]["name"],
                    "images": track["album"]["images"],
                },
                "preview_url": track["preview_url"],
                "external_urls": track["external_urls"],
                "popularity": track["popularity"],
                "played_at": item["played_at"],
            }
            tracks.append(track_info)

        return {"tracks": tracks}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"최근 재생 곡 가져오기 오류: {str(e)}"
        )


@router.get("/search")
async def search_tracks(q: str, limit: int = 10, access_token: str = None):
    """Spotify 트랙 검색"""
    try:
        if access_token:
            # 사용자 토큰으로 검색 (더 많은 결과)
            sp = spotipy.Spotify(auth=access_token)
        else:
            # 기본 클라이언트 자격 증명으로 검색
            sp = spotipy.Spotify(
                client_credentials_manager=spotipy.oauth2.SpotifyClientCredentials(
                    client_id=settings.SPOTIFY_CLIENT_ID,
                    client_secret=settings.SPOTIFY_CLIENT_SECRET
                )
            )
        
        results = sp.search(q=q, type='track', limit=limit)
        
        tracks = []
        for track in results['tracks']['items']:
            track_info = {
                "id": track["id"],
                "name": track["name"],
                "artists": [artist["name"] for artist in track["artists"]],
                "album": {
                    "name": track["album"]["name"],
                    "images": track["album"]["images"],
                },
                "preview_url": track["preview_url"],
                "external_urls": track["external_urls"],
                "popularity": track["popularity"],
            }
            tracks.append(track_info)
        
        return {"tracks": tracks}
        
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Spotify 검색 오류: {str(e)}"
        )
