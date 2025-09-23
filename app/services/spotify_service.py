import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Dict, Any, Optional
import requests
import random
from app.core.config import settings


class SpotifyService:
    """Spotify API 연동을 위한 서비스 클래스"""

    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET

        if self.client_id and self.client_secret:
            client_credentials_manager = SpotifyClientCredentials(
                client_id=self.client_id, client_secret=self.client_secret
            )
            self.sp = spotipy.Spotify(
                client_credentials_manager=client_credentials_manager
            )
        else:
            self.sp = None

    def search_track(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        트랙 검색
        """
        if not self.sp:
            raise Exception("Spotify API 설정이 필요합니다.")

        try:
            results = self.sp.search(q=query, type="track", limit=limit)
            tracks = []

            for track in results["tracks"]["items"]:
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

            return tracks

        except Exception as e:
            print(f"Spotify 트랙 검색 오류: {e}")
            return []

    def get_audio_features(self, track_id: str) -> Dict[str, Any]:
        """
        트랙의 오디오 특성 가져오기
        """
        if not self.sp:
            raise Exception("Spotify API 설정이 필요합니다.")

        try:
            features = self.sp.audio_features(track_id)
            if features and features[0]:
                return features[0]
            return {}

        except Exception as e:
            print(f"Spotify 오디오 특성 가져오기 오류: {e}")
            return {}

    def get_recommendations(
        self,
        target_features: Dict[str, Any],
        limit: int = 5,
        filters: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Spotify 추천 API를 사용하여 유사한 곡 추천
        """
        if not self.sp:
            raise Exception("Spotify API 설정이 필요합니다.")

        try:
            # 토큰 상태 확인
            print(f"Spotify Client ID: {self.client_id[:10]}...")
            print(f"Spotify Client Secret: {self.client_secret[:10]}...")

            # 토큰 발급 테스트
            try:
                token_response = self.sp.client_credentials_manager.get_access_token()
                print(f"토큰 발급 성공: {str(token_response)[:20]}...")
            except Exception as token_error:
                print(f"토큰 발급 실패: {token_error}")
                raise token_error

            # Client Credentials Flow는 추천 API를 지원하지 않음
            # 대신 분석된 특징을 기반으로 한 맞춤형 검색
            print("분석된 특징 기반 맞춤형 추천 생성...")

            # 분석된 특징을 기반으로 검색어 생성
            search_queries = self._generate_search_queries_from_features(
                target_features
            )
            print(f"생성된 맞춤형 검색어: {search_queries}")

            all_tracks = []
            for query in search_queries:
                try:
                    # 각 검색어마다 다른 개수로 검색 (더 다양한 결과)
                    search_limit = random.randint(2, 5)
                    search_results = self.sp.search(
                        q=query, type="track", limit=search_limit
                    )
                    tracks = search_results["tracks"]["items"]
                    all_tracks.extend(tracks)
                    print(f"검색어 '{query}': {len(tracks)}개 트랙 발견")
                except Exception as e:
                    print(f"검색 쿼리 '{query}' 실패: {e}")
                    continue

            # 중복 제거 및 랜덤 셔플
            unique_tracks = []
            seen_ids = set()
            for track in all_tracks:
                if track["id"] not in seen_ids:
                    unique_tracks.append(track)
                    seen_ids.add(track["id"])

            # 결과를 랜덤하게 섞고 제한
            random.shuffle(unique_tracks)
            unique_tracks = unique_tracks[: limit * 2]  # 필터링을 위해 더 많이 가져오기

            recommendations = {"tracks": unique_tracks}
            print(f"검색 기반 추천 성공: {len(recommendations['tracks'])}개 트랙")

            print(f"Spotify SDK 추천 성공: {len(recommendations['tracks'])}개 트랙")

            tracks = []
            for track in recommendations["tracks"]:
                # Audio Features 가져오기 (가사 유무 확인을 위해)
                try:
                    audio_features = self.get_audio_features(track["id"])
                    # instrumentalness가 0.5 이상이면 가사 없는 곡으로 판단하여 제외
                    if (
                        audio_features
                        and audio_features.get("instrumentalness", 0) > 0.5
                    ):
                        print(
                            f"가사 없는 곡 제외: {track['name']} (instrumentalness: {audio_features.get('instrumentalness', 0):.2f})"
                        )
                        continue
                except Exception as e:
                    print(f"Audio Features 가져오기 실패: {e}")
                    # Audio Features를 가져올 수 없는 경우 기본값으로 설정하고 포함
                    audio_features = {
                        "danceability": 0.5,
                        "energy": 0.5,
                        "valence": 0.5,
                        "tempo": 120.0,
                        "instrumentalness": 0.1,  # 기본값으로 가사 있는 곡으로 가정
                    }

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
                    "audio_features": audio_features,
                }

                tracks.append(track_info)

                # 요청된 개수만큼 수집되면 중단
                if len(tracks) >= limit:
                    break

            print(f"가사 있는 곡 {len(tracks)}개 추천 완료")
            return tracks

        except Exception as e:
            print(f"Spotify 추천 API 오류: {e}")
            raise Exception(f"추천 생성 실패: {e}")

    def calculate_similarity(
        self, target_features: Dict[str, Any], track_features: Dict[str, Any]
    ) -> float:
        """
        두 트랙의 오디오 특성 간 유사도 계산
        """
        print(f"calculate_similarity called with:")
        print(f"  target_features: {target_features}")
        print(f"  track_features: {track_features}")

        if not target_features or not track_features:
            print("  Missing features, returning default 0.5")
            return 0.5  # 기본값

        # 주요 특성들 비교
        features_to_compare = ["danceability", "energy", "valence"]
        similarities = []

        for feature in features_to_compare:
            if feature in target_features and feature in track_features:
                target_val = target_features[feature]
                track_val = track_features[feature]
                # 유클리드 거리 기반 유사도 (0-1 범위)
                similarity = 1 - abs(target_val - track_val)
                similarities.append(similarity)
                print(
                    f"  {feature}: target={target_val:.3f}, track={track_val:.3f}, similarity={similarity:.3f}"
                )

        if similarities:
            avg_similarity = sum(similarities) / len(similarities)
            # 0-1 범위를 0-100%로 변환
            percentage = avg_similarity * 100
            print(f"  Average similarity: {avg_similarity:.3f} ({percentage:.1f}%)")
            return percentage
        else:
            print("  No comparable features found, returning default 50%")
            return 50.0  # 기본값을 50%로 변경

    def _generate_search_queries_from_features(
        self, target_features: Dict[str, Any]
    ) -> List[str]:
        """
        분석된 오디오 특징을 기반으로 맞춤형 검색어 생성
        """
        search_queries = []

        # Danceability 기반 장르 선택
        danceability = target_features.get("danceability", 0.5)
        if danceability > 0.7:
            dance_genres = ["dance", "electronic", "pop", "house", "disco"]
        elif danceability > 0.4:
            dance_genres = ["pop", "rock", "funk", "soul", "r&b"]
        else:
            dance_genres = ["ballad", "acoustic", "folk", "jazz", "classical"]

        # Energy 기반 분위 선택
        energy = target_features.get("energy", 0.5)
        if energy > 0.7:
            energy_moods = ["energetic", "upbeat", "powerful", "intense", "driving"]
        elif energy > 0.4:
            energy_moods = ["moderate", "balanced", "steady", "smooth", "flowing"]
        else:
            energy_moods = ["calm", "peaceful", "gentle", "soft", "relaxing"]

        # Valence 기반 감정 선택
        valence = target_features.get("valence", 0.5)
        if valence > 0.7:
            valence_moods = ["happy", "joyful", "cheerful", "bright", "uplifting"]
        elif valence > 0.4:
            valence_moods = ["neutral", "balanced", "moderate", "stable", "even"]
        else:
            valence_moods = ["melancholic", "sad", "emotional", "deep", "introspective"]

        # Tempo 기반 템포 선택
        tempo = target_features.get("tempo", 120)
        if tempo > 140:
            tempo_descriptors = ["fast", "upbeat", "energetic", "driving"]
        elif tempo > 100:
            tempo_descriptors = ["moderate", "steady", "balanced", "flowing"]
        else:
            tempo_descriptors = ["slow", "relaxed", "calm", "peaceful"]

        # 검색어 조합 생성
        for _ in range(5):
            genre = random.choice(dance_genres)
            mood = random.choice(energy_moods + valence_moods)
            tempo_desc = random.choice(tempo_descriptors)

            patterns = [
                f"{genre} {mood}",
                f"{mood} {genre} music",
                f"{tempo_desc} {genre}",
                f"{genre} {tempo_desc} tempo",
                f"{mood} {tempo_desc} music",
            ]
            search_queries.append(random.choice(patterns))

        return search_queries

    def get_similar_recommendations(
        self,
        target_features: Dict[str, Any],
        limit: int = 5,
        filters: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        오디오 특성을 기반으로 유사한 곡 추천
        """
        if not self.sp:
            raise Exception("Spotify API 설정이 필요합니다.")

        try:
            # 추천 파라미터 설정
            recommendations_params = {
                "limit": limit * 2,  # 필터링을 위해 더 많이 가져오기
                "target_danceability": target_features.get("danceability", 0.5),
                "target_energy": target_features.get("energy", 0.5),
                "target_valence": target_features.get("valence", 0.5),
                "target_tempo": target_features.get("tempo", 120),
                "target_loudness": target_features.get("loudness", -5.0),
                "target_acousticness": target_features.get("acousticness", 0.5),
                "target_instrumentalness": 0.1,  # 가사 있는 곡을 선호하도록 설정
                "target_speechiness": target_features.get("speechiness", 0.1),
                "target_liveness": target_features.get("liveness", 0.1),
            }

            # Spotify SDK를 사용한 간단한 추천 시도
            print("Spotify SDK를 사용한 추천 시도...")

            # 가장 기본적인 파라미터로 시도
            recommendations = self.sp.recommendations(
                seed_genres=["pop"], limit=limit * 2, market="KR"
            )

            print(f"Spotify SDK 추천 성공: {len(recommendations['tracks'])}개 트랙")

            tracks = []
            for track in recommendations["tracks"]:
                # Audio Features 가져오기 (가사 유무 확인을 위해)
                try:
                    audio_features = self.get_audio_features(track["id"])
                    # instrumentalness가 0.5 이상이면 가사 없는 곡으로 판단하여 제외
                    if (
                        audio_features
                        and audio_features.get("instrumentalness", 0) > 0.5
                    ):
                        print(
                            f"가사 없는 곡 제외: {track['name']} (instrumentalness: {audio_features.get('instrumentalness', 0):.2f})"
                        )
                        continue
                except Exception as e:
                    print(f"Audio Features 가져오기 실패: {e}")
                    # Audio Features를 가져올 수 없는 경우 기본값으로 설정하고 포함
                    audio_features = {
                        "danceability": 0.5,
                        "energy": 0.5,
                        "valence": 0.5,
                        "tempo": 120.0,
                        "instrumentalness": 0.1,  # 기본값으로 가사 있는 곡으로 가정
                    }

                track_info = {
                    "id": track["id"],
                    "name": track["name"],
                    "artists": track["artists"],
                    "album": track["album"],
                    "preview_url": track.get("preview_url"),
                    "external_urls": track.get("external_urls", {}),
                    "popularity": track.get("popularity", 0),
                    "audio_features": audio_features,
                }

                tracks.append(track_info)

                # 요청된 개수만큼 수집되면 중단
                if len(tracks) >= limit:
                    break

            print(f"가사 있는 곡 {len(tracks)}개 추천 완료")
            return tracks

        except Exception as e:
            print(f"Spotify 추천 API 오류: {e}")
            raise Exception(f"추천 생성 실패: {e}")

    def get_track_info(self, track_id: str) -> Dict[str, Any]:
        """
        트랙 정보 가져오기
        """
        if not self.sp:
            raise Exception("Spotify API 설정이 필요합니다.")

        try:
            track = self.sp.track(track_id)
            return {
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

        except Exception as e:
            print(f"Spotify 트랙 정보 가져오기 오류: {e}")
            return {}

    def get_artist_info(self, artist_id: str) -> Dict[str, Any]:
        """
        아티스트 정보 가져오기
        """
        if not self.sp:
            raise Exception("Spotify API 설정이 필요합니다.")

        try:
            artist = self.sp.artist(artist_id)
            return {
                "id": artist["id"],
                "name": artist["name"],
                "genres": artist["genres"],
                "images": artist["images"],
                "popularity": artist["popularity"],
                "followers": artist["followers"]["total"],
            }

        except Exception as e:
            print(f"Spotify 아티스트 정보 가져오기 오류: {e}")
            return {}

    def get_playlist_tracks(
        self, playlist_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        플레이리스트 트랙 가져오기
        """
        if not self.sp:
            raise Exception("Spotify API 설정이 필요합니다.")

        try:
            results = self.sp.playlist_tracks(playlist_id, limit=limit)
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
                }
                tracks.append(track_info)

            return tracks

        except Exception as e:
            print(f"Spotify 플레이리스트 트랙 가져오기 오류: {e}")
            return []

    def get_user_top_tracks(
        self, time_range: str = "medium_term", limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        사용자의 인기 트랙 가져오기 (사용자 인증 필요)
        """
        if not self.sp:
            raise Exception("Spotify API 설정이 필요합니다.")

        try:
            results = self.sp.current_user_top_tracks(
                time_range=time_range, limit=limit
            )
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

            return tracks

        except Exception as e:
            print(f"Spotify 사용자 인기 트랙 가져오기 오류: {e}")
            return []

    def get_user_top_artists(
        self, time_range: str = "medium_term", limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        사용자의 인기 아티스트 가져오기 (사용자 인증 필요)
        """
        if not self.sp:
            raise Exception("Spotify API 설정이 필요합니다.")

        try:
            results = self.sp.current_user_top_artists(
                time_range=time_range, limit=limit
            )
            artists = []

            for artist in results["items"]:
                artist_info = {
                    "id": artist["id"],
                    "name": artist["name"],
                    "genres": artist["genres"],
                    "images": artist["images"],
                    "popularity": artist["popularity"],
                    "followers": artist["followers"]["total"],
                }
                artists.append(artist_info)

            return artists

        except Exception as e:
            print(f"Spotify 사용자 인기 아티스트 가져오기 오류: {e}")
            return []

    def get_recommendations_by_artists(
        self, artist_ids: List[str], limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        아티스트 기반 추천
        """
        if not self.sp:
            raise Exception("Spotify API 설정이 필요합니다.")

        try:
            recommendations = self.sp.recommendations(
                seed_artists=artist_ids[:5], limit=limit, market="KR"  # 최대 5개
            )

            tracks = []
            for track in recommendations["tracks"]:
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

            return tracks

        except Exception as e:
            print(f"Spotify 아티스트 기반 추천 오류: {e}")
            return []

    def get_recommendations_by_tracks(
        self, track_ids: List[str], limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        트랙 기반 추천
        """
        if not self.sp:
            raise Exception("Spotify API 설정이 필요합니다.")

        try:
            recommendations = self.sp.recommendations(
                seed_tracks=track_ids[:5], limit=limit, market="KR"  # 최대 5개
            )

            tracks = []
            for track in recommendations["tracks"]:
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

            return tracks

        except Exception as e:
            print(f"Spotify 트랙 기반 추천 오류: {e}")
            return []
