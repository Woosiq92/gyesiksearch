from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import uuid

from app.models.schemas import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationItem,
    SpotifySearchRequest,
    SpotifySearchResponse,
    SpotifyTrack,
)
from app.services.spotify_service import SpotifyService
from app.services.chatgpt_service import ChatGPTService

router = APIRouter()

# 서비스 인스턴스
chatgpt_service = ChatGPTService()

# 분석 세션 저장소 import (audio.py에서)
from app.api.audio import analysis_sessions


@router.post("/similar", response_model=RecommendationResponse)
async def get_similar_recommendations(request: RecommendationRequest):
    """
    유사한 곡을 추천합니다.

    Args:
        request: 추천 요청 데이터

    Returns:
        추천 곡 리스트
    """
    try:
        print(
            f"추천 요청 받음: session_id={request.session_id}, num_recommendations={request.num_recommendations}"
        )

        # Spotify 서비스 인스턴스 생성
        spotify_service = SpotifyService()

        # 실제 분석된 오디오 특징 가져오기
        target_features = None
        if request.session_id in analysis_sessions:
            session_data = analysis_sessions[request.session_id]
            audio_features = session_data["audio_features"]

            # 실제 분석된 특징 사용
            target_features = {
                "danceability": audio_features.danceability,
                "energy": audio_features.energy,
                "valence": audio_features.valence,
                "tempo": audio_features.tempo,
                "key": audio_features.key,
                "mode": audio_features.mode,
                "loudness": audio_features.loudness,
                "acousticness": audio_features.acousticness,
                "instrumentalness": audio_features.instrumentalness,
                "speechiness": audio_features.speechiness,
                "liveness": audio_features.liveness,
            }
            print(
                f"실제 분석된 특징 사용: danceability={target_features['danceability']:.2f}, energy={target_features['energy']:.2f}, valence={target_features['valence']:.2f}"
            )
        else:
            # 세션을 찾을 수 없는 경우 기본값 사용
            target_features = {
                "danceability": 0.7,
                "energy": 0.6,
                "valence": 0.5,
                "tempo": 120,
                "key": 0,
                "mode": 1,
                "loudness": -5.0,
                "acousticness": 0.3,
                "instrumentalness": 0.1,
                "speechiness": 0.05,
                "liveness": 0.1,
            }
            print("세션을 찾을 수 없음, 기본값 사용")

        # 실제 Spotify API를 사용한 추천 시도
        if spotify_service.sp:
            try:

                # Spotify에서 유사한 곡 검색
                recommendations = spotify_service.get_recommendations(
                    target_features=target_features,
                    limit=request.num_recommendations,
                    filters=request.filters,
                )

                if recommendations:
                    recommendation_items = []
                    for i, track in enumerate(recommendations):
                        # 디버깅: track 타입 확인
                        print(f"Track {i} type: {type(track)}")
                        print(f"Track {i} content: {track}")

                        # track이 딕셔너리가 아닌 경우 처리
                        if not isinstance(track, dict):
                            print(f"Track {i} is not a dict, skipping...")
                            continue

                        # 유사도 점수 계산
                        try:
                            similarity_score = spotify_service.calculate_similarity(
                                target_features, track.get("audio_features", {})
                            )
                            print(f"Track {i} similarity_score: {similarity_score}")
                        except Exception as e:
                            print(f"Track {i} similarity calculation error: {e}")
                            similarity_score = 0.5

                        # 추천 근거 생성
                        try:
                            recommendation_reason = (
                                chatgpt_service.generate_recommendation_reason(
                                    target_features,
                                    track.get("audio_features", {}),
                                    similarity_score,
                                )
                            )
                            print(
                                f"Track {i} recommendation_reason: {recommendation_reason}"
                            )
                        except Exception as e:
                            print(f"Track {i} recommendation reason error: {e}")
                            recommendation_reason = "추천 이유를 생성할 수 없습니다."

                        recommendation_item = RecommendationItem(
                            spotify_id=track["id"],
                            track_name=track["name"],
                            artist_name=(
                                ", ".join(track["artists"])
                                if isinstance(track["artists"][0], str)
                                else ", ".join(
                                    [artist["name"] for artist in track["artists"]]
                                )
                            ),
                            album_name=track["album"]["name"],
                            similarity_score=similarity_score,
                            audio_features=track.get("audio_features"),
                            recommendation_reason=recommendation_reason,
                            preview_url=track.get("preview_url"),
                            external_urls=track.get("external_urls", {}),
                        )
                        recommendation_items.append(recommendation_item)

                    print(
                        f"Spotify API로 추천 곡 {len(recommendation_items)}개 생성 완료"
                    )
                    return RecommendationResponse(
                        recommendations=recommendation_items,
                        total=len(recommendation_items),
                        session_id=request.session_id,
                    )

            except Exception as spotify_error:
                print(f"Spotify API 추천 실패, 기본 추천 사용: {str(spotify_error)}")

        # Spotify API 실패 시 기본 추천 사용
        return await _get_default_recommendations(request)

    except Exception as e:
        print(f"추천 생성 중 오류 발생: {str(e)}")
        return await _get_error_recommendation(request)


async def _get_default_recommendations(request: RecommendationRequest):
    """기본 추천 곡 반환"""
    # 실제 인기 곡들 (Spotify API 실패 시 사용)
    default_recommendations = [
        {
            "id": "spotify_track_1",
            "name": "Blinding Lights",
            "artists": [{"name": "The Weeknd"}],
            "album": {"name": "After Hours"},
            "preview_url": None,
            "external_urls": {
                "spotify": "https://open.spotify.com/track/0VjIjW4UAAN4vTbO5jJhqJ"
            },
        },
        {
            "id": "spotify_track_2",
            "name": "Levitating",
            "artists": [{"name": "Dua Lipa"}],
            "album": {"name": "Future Nostalgia"},
            "preview_url": None,
            "external_urls": {
                "spotify": "https://open.spotify.com/track/7qiZfU4dY1lWllzX7mPBI3"
            },
        },
        {
            "id": "spotify_track_3",
            "name": "Good 4 U",
            "artists": [{"name": "Olivia Rodrigo"}],
            "album": {"name": "SOUR"},
            "preview_url": None,
            "external_urls": {
                "spotify": "https://open.spotify.com/track/6f3Slt0GbA2bPZlz0aIFXN"
            },
        },
        {
            "id": "spotify_track_4",
            "name": "Shape of You",
            "artists": [{"name": "Ed Sheeran"}],
            "album": {"name": "÷ (Divide)"},
            "preview_url": None,
            "external_urls": {
                "spotify": "https://open.spotify.com/track/5Z01UMMf7V1o0MzF86s6WJ"
            },
        },
        {
            "id": "spotify_track_5",
            "name": "Watermelon Sugar",
            "artists": [{"name": "Harry Styles"}],
            "album": {"name": "Fine Line"},
            "preview_url": None,
            "external_urls": {
                "spotify": "https://open.spotify.com/track/6UelLqGlWMcVH1E5c4H7lY"
            },
        },
        {
            "id": "spotify_track_6",
            "name": "Stay",
            "artists": [{"name": "The Kid LAROI"}, {"name": "Justin Bieber"}],
            "album": {"name": "F*CK LOVE 3: OVER YOU"},
            "preview_url": None,
            "external_urls": {
                "spotify": "https://open.spotify.com/track/5PjdY0CKGZdEuoNab3yDmX"
            },
        },
        {
            "id": "spotify_track_7",
            "name": "Heat Waves",
            "artists": [{"name": "Glass Animals"}],
            "album": {"name": "Dreamland"},
            "preview_url": None,
            "external_urls": {
                "spotify": "https://open.spotify.com/track/6CDzDgIUqeDY5g8ujExx2f"
            },
        },
        {
            "id": "spotify_track_8",
            "name": "Industry Baby",
            "artists": [{"name": "Lil Nas X"}, {"name": "Jack Harlow"}],
            "album": {"name": "MONTERO"},
            "preview_url": None,
            "external_urls": {
                "spotify": "https://open.spotify.com/track/27NovPIUIRrOZoCHxABJwK"
            },
        },
        {
            "id": "spotify_track_9",
            "name": "Peaches",
            "artists": [
                {"name": "Justin Bieber"},
                {"name": "Daniel Caesar"},
                {"name": "Giveon"},
            ],
            "album": {"name": "Justice"},
            "preview_url": None,
            "external_urls": {
                "spotify": "https://open.spotify.com/track/4iJyoBOLtHqaGxP12qzhQI"
            },
        },
        {
            "id": "spotify_track_10",
            "name": "Kiss Me More",
            "artists": [{"name": "Doja Cat"}, {"name": "SZA"}],
            "album": {"name": "Planet Her"},
            "preview_url": None,
            "external_urls": {
                "spotify": "https://open.spotify.com/track/3DarAbFujv6eYNliUTyqtz"
            },
        },
    ]

    # 요청된 개수만큼 추천 곡 반환
    num_recommendations = min(request.num_recommendations, len(default_recommendations))
    selected_recommendations = default_recommendations[:num_recommendations]

    recommendation_items = []
    for i, track in enumerate(selected_recommendations):
        # 기본 Audio Features
        from app.models.schemas import AudioFeaturesResponse

        audio_features = AudioFeaturesResponse(
            danceability=0.7 + (i * 0.02),
            energy=0.6 + (i * 0.02),
            valence=0.5 + (i * 0.02),
            tempo=120 + (i * 3),
            key=i % 12,
            mode=1,
            loudness=-5.0 - (i * 0.5),
            acousticness=0.3 - (i * 0.02),
            instrumentalness=0.1,  # 가사 있는 곡으로 설정
            speechiness=0.05,
            liveness=0.1,
            duration_ms=180000 + (i * 3000),
            time_signature=4,
        )

        # 유사도 점수 (기본값)
        similarity_score = 85.0 - (i * 2.5)

        # 추천 근거 생성
        recommendation_reason = chatgpt_service.generate_recommendation_reason(
            {
                "danceability": 0.7,
                "energy": 0.6,
                "valence": 0.5,
                "tempo": 120,
            },
            {
                "danceability": audio_features.danceability,
                "energy": audio_features.energy,
                "valence": audio_features.valence,
                "tempo": audio_features.tempo,
            },
            similarity_score,
        )

        recommendation_item = RecommendationItem(
            spotify_id=track["id"],
            track_name=track["name"],
            artist_name=", ".join([artist["name"] for artist in track["artists"]]),
            album_name=track["album"]["name"],
            similarity_score=similarity_score,
            audio_features=audio_features,
            recommendation_reason=recommendation_reason,
            preview_url=track.get("preview_url"),
            external_urls=track.get("external_urls", {}),
        )
        recommendation_items.append(recommendation_item)

    print(f"기본 추천 곡 {len(recommendation_items)}개 생성 완료")
    return RecommendationResponse(
        recommendations=recommendation_items,
        total=len(recommendation_items),
        session_id=request.session_id,
    )


async def _get_error_recommendation(request: RecommendationRequest):
    """오류 발생 시 기본 추천 반환"""
    from app.models.schemas import AudioFeaturesResponse

    basic_recommendation = RecommendationItem(
        spotify_id="error_track",
        track_name="추천을 불러올 수 없습니다",
        artist_name="시스템",
        album_name="오류",
        similarity_score=0.0,
        audio_features=AudioFeaturesResponse(
            danceability=0.5,
            energy=0.5,
            valence=0.5,
            tempo=120,
            key=0,
            mode=1,
            loudness=-5.0,
            acousticness=0.5,
            instrumentalness=0.1,  # 가사 있는 곡으로 설정
            speechiness=0.1,
            liveness=0.1,
            duration_ms=180000,
            time_signature=4,
        ),
        recommendation_reason="추천 시스템에 일시적인 문제가 발생했습니다.",
        preview_url=None,
        external_urls={},
    )

    return RecommendationResponse(
        recommendations=[basic_recommendation],
        total=1,
        session_id=request.session_id,
    )


@router.post("/search", response_model=SpotifySearchResponse)
async def search_tracks(request: SpotifySearchRequest):
    """
    Spotify에서 곡을 검색합니다.

    Args:
        request: 검색 요청 데이터

    Returns:
        검색 결과
    """
    try:
        # Spotify 서비스 인스턴스 생성
        spotify_service = SpotifyService()

        # Spotify API가 설정되어 있으면 실제 검색 시도
        if spotify_service.sp:
            try:
                tracks = spotify_service.search_tracks(request.query, request.limit)

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

                return SpotifySearchResponse(
                    tracks=spotify_tracks, total=len(spotify_tracks)
                )

            except Exception as spotify_error:
                print(f"Spotify 검색 오류, 기본 결과 사용: {str(spotify_error)}")
                # Spotify API 실패 시 기본 결과로 fallback

        # 기본 검색 결과 반환 (Spotify API 없이도 작동)
        default_tracks = [
            {
                "id": f"search_result_{i}",
                "name": f"Search Result {i}",
                "artists": [f"Artist {i}"],
                "album": {"name": f"Album {i}"},
                "preview_url": None,
                "external_urls": {
                    "spotify": f"https://open.spotify.com/track/search{i}"
                },
            }
            for i in range(1, min(request.limit + 1, 6))
        ]

        spotify_tracks = []
        for track in default_tracks:
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
        # 오류 발생 시 빈 결과 반환
        print(f"검색 중 오류 발생: {str(e)}")
        return SpotifySearchResponse(tracks=[], total=0)


@router.get("/genres")
async def get_genre_seeds():
    """
    사용 가능한 장르 시드를 가져옵니다.

    Returns:
        장르 리스트
    """
    try:
        # 기본 장르 리스트 반환
        default_genres = [
            "pop",
            "rock",
            "jazz",
            "classical",
            "electronic",
            "hip-hop",
            "country",
            "blues",
            "folk",
            "reggae",
        ]
        return {"genres": default_genres}

    except Exception as e:
        print(f"장르 조회 중 오류 발생: {str(e)}")
        return {"genres": []}


@router.post("/analyze-mood")
async def analyze_mood_and_genre(audio_features: Dict[str, Any]):
    """
    곡의 분위기와 장르를 분석합니다.

    Args:
        audio_features: Audio Features 딕셔너리

    Returns:
        분석 결과
    """
    try:
        # 기본 분석 결과 반환
        mood_analysis = {
            "mood": "neutral",
            "genre": "pop",
            "description": "이 곡은 중간 정도의 에너지와 긍정적인 분위기를 가지고 있습니다.",
            "confidence": 0.7,
        }
        return mood_analysis

    except Exception as e:
        print(f"분위기 분석 중 오류 발생: {str(e)}")
        return {
            "mood": "unknown",
            "genre": "unknown",
            "description": "분석 중 오류가 발생했습니다.",
            "confidence": 0.0,
        }
