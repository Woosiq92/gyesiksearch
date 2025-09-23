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

        print(f"Spotify API 설정 확인:")
        print(
            f"  Client ID: {self.client_id[:10] + '...' if self.client_id else 'None'}"
        )
        print(
            f"  Client Secret: {self.client_secret[:10] + '...' if self.client_secret else 'None'}"
        )

        if self.client_id and self.client_secret:
            try:
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=self.client_id, client_secret=self.client_secret
                )
                self.sp = spotipy.Spotify(
                    client_credentials_manager=client_credentials_manager
                )
                print("✅ Spotify API 연결 성공")

                # 토큰 발급 테스트
                try:
                    token = client_credentials_manager.get_access_token()
                    if isinstance(token, str):
                        print(f"✅ 토큰 발급 성공: {token[:20]}...")
                    else:
                        print(f"✅ 토큰 발급 성공: {type(token)} 타입")
                except Exception as token_error:
                    print(f"❌ 토큰 발급 실패: {token_error}")
                    self.sp = None
                    return

                # 연결 테스트
                test_result = self.sp.search(q="test", type="track", limit=1)
                print(
                    f"✅ Spotify API 테스트 성공: {len(test_result['tracks']['items'])}개 결과"
                )

                # Audio Features 테스트
                if test_result["tracks"]["items"]:
                    test_track_id = test_result["tracks"]["items"][0]["id"]
                    try:
                        test_features = self.sp.audio_features(test_track_id)
                        if test_features and test_features[0]:
                            print(
                                f"✅ Audio Features 테스트 성공: {len(test_features[0])}개 특성"
                            )
                        else:
                            print("❌ Audio Features 테스트 실패: 결과가 비어있음")
                    except Exception as features_error:
                        print(f"❌ Audio Features 테스트 실패: {features_error}")

            except Exception as e:
                print(f"❌ Spotify API 연결 실패: {e}")
                self.sp = None
        else:
            print("❌ Spotify API 키가 설정되지 않음")
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
            print("❌ Spotify API가 설정되지 않음")
            return {}

        try:
            print(f"🎵 Audio Features 요청: {track_id}")

            # 토큰 상태 확인 및 갱신
            try:
                token = self.sp.client_credentials_manager.get_access_token()
                print(f"토큰 상태 확인: {type(token)}")
            except Exception as token_error:
                print(f"토큰 확인 실패: {token_error}")
                return {}

            # Audio Features 요청
            features = self.sp.audio_features(track_id)
            if features and features[0]:
                print(f"✅ Audio Features 성공: {len(features[0])}개 특성")
                return features[0]
            else:
                print("❌ Audio Features 결과가 비어있음")
                return {}

        except Exception as e:
            print(f"❌ Spotify 오디오 특성 가져오기 오류: {e}")
            print(f"오류 타입: {type(e)}")
            print(f"오류 상세: {str(e)}")
            return {}

    def _get_default_audio_features(self) -> Dict[str, Any]:
        """
        Audio Features를 가져올 수 없는 경우 사용할 기본값
        """
        return {
            "danceability": 0.5,
            "energy": 0.5,
            "valence": 0.5,
            "tempo": 120.0,
            "acousticness": 0.5,
            "instrumentalness": 0.1,  # 가사 있는 곡으로 가정
            "speechiness": 0.1,
            "liveness": 0.1,
            "loudness": -5.0,
            "mode": 1,
            "key": 0,
            "time_signature": 4,
            "duration_ms": 180000,
            "analysis_url": "",
            "track_href": "",
            "type": "audio_features",
            "uri": "",
        }

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
                if isinstance(token_response, str):
                    print(f"토큰 발급 성공: {token_response[:20]}...")
                else:
                    print(f"토큰 발급 성공: {type(token_response)} 타입")
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
        두 트랙의 오디오 특성 간 유사도 계산 (개선된 버전)
        """
        print(f"calculate_similarity called with:")
        print(f"  target_features: {target_features}")
        print(f"  track_features: {track_features}")

        if not target_features or not track_features:
            print("  Missing features, returning default 50%")
            return 50.0

        # 더 많은 특성들을 비교하여 정확도 향상
        features_to_compare = [
            "danceability",
            "energy",
            "valence",
            "tempo",
            "acousticness",
            "instrumentalness",
            "speechiness",
            "liveness",
        ]
        similarities = []
        weights = {
            "danceability": 0.25,  # 가장 중요한 특성
            "energy": 0.25,  # 가장 중요한 특성
            "valence": 0.20,  # 감정적 유사성
            "tempo": 0.15,  # 리듬적 유사성
            "acousticness": 0.05,  # 음향적 특성
            "instrumentalness": 0.05,  # 악기 vs 가사
            "speechiness": 0.03,  # 말하기 vs 노래
            "liveness": 0.02,  # 라이브 vs 녹음
        }

        for feature in features_to_compare:
            if feature in target_features and feature in track_features:
                target_val = target_features[feature]
                track_val = track_features[feature]

                # 템포는 다른 스케일이므로 정규화
                if feature == "tempo":
                    # 템포 차이를 0-1 범위로 정규화 (0-200 BPM 범위 가정)
                    tempo_diff = abs(target_val - track_val) / 200.0
                    similarity = 1 - min(tempo_diff, 1.0)
                else:
                    # 다른 특성들은 0-1 범위이므로 직접 계산
                    similarity = 1 - abs(target_val - track_val)

                # 가중치 적용
                weighted_similarity = similarity * weights.get(feature, 0.1)
                similarities.append(weighted_similarity)

                print(
                    f"  {feature}: target={target_val:.3f}, track={track_val:.3f}, "
                    f"similarity={similarity:.3f}, weighted={weighted_similarity:.3f}"
                )

        if similarities:
            # 가중 평균 유사도 계산
            total_weight = sum(
                weights.get(f, 0.1)
                for f in features_to_compare
                if f in target_features and f in track_features
            )
            avg_similarity = (
                sum(similarities) / total_weight if total_weight > 0 else 0.5
            )

            # 0-1 범위를 0-100%로 변환
            percentage = avg_similarity * 100
            print(
                f"  Weighted average similarity: {avg_similarity:.3f} ({percentage:.1f}%)"
            )
            return percentage
        else:
            print("  No comparable features found, returning default 50%")
            return 50.0

    def _generate_search_queries_from_features(
        self, target_features: Dict[str, Any]
    ) -> List[str]:
        """
        분석된 오디오 특징을 기반으로 맞춤형 검색어 생성 (개선된 버전)
        """
        search_queries = []

        # Danceability 기반 장르 선택
        danceability = target_features.get("danceability", 0.5)
        if danceability > 0.7:
            dance_genres = ["dance", "electronic", "pop", "house", "disco", "edm"]
        elif danceability > 0.4:
            dance_genres = ["pop", "rock", "funk", "soul", "r&b", "indie"]
        else:
            dance_genres = [
                "ballad",
                "acoustic",
                "folk",
                "jazz",
                "classical",
                "ambient",
            ]

        # Energy 기반 분위 선택
        energy = target_features.get("energy", 0.5)
        if energy > 0.7:
            energy_moods = [
                "energetic",
                "upbeat",
                "powerful",
                "intense",
                "driving",
                "explosive",
            ]
        elif energy > 0.4:
            energy_moods = [
                "moderate",
                "balanced",
                "steady",
                "smooth",
                "flowing",
                "dynamic",
            ]
        else:
            energy_moods = ["calm", "peaceful", "gentle", "soft", "relaxing", "mellow"]

        # Valence 기반 감정 선택
        valence = target_features.get("valence", 0.5)
        if valence > 0.7:
            valence_moods = [
                "happy",
                "joyful",
                "cheerful",
                "bright",
                "uplifting",
                "positive",
            ]
        elif valence > 0.4:
            valence_moods = [
                "neutral",
                "balanced",
                "moderate",
                "stable",
                "even",
                "centered",
            ]
        else:
            valence_moods = [
                "melancholic",
                "sad",
                "emotional",
                "deep",
                "introspective",
                "moody",
            ]

        # Tempo 기반 템포 선택
        tempo = target_features.get("tempo", 120)
        if tempo > 140:
            tempo_descriptors = ["fast", "upbeat", "energetic", "driving", "bpm"]
        elif tempo > 100:
            tempo_descriptors = [
                "moderate",
                "steady",
                "balanced",
                "flowing",
                "mid-tempo",
            ]
        else:
            tempo_descriptors = ["slow", "relaxed", "calm", "peaceful", "ballad"]

        # Acousticness 기반 음향 특성
        acousticness = target_features.get("acousticness", 0.5)
        if acousticness > 0.7:
            acoustic_descriptors = ["acoustic", "unplugged", "organic", "natural"]
        else:
            acoustic_descriptors = ["electronic", "synthetic", "processed", "digital"]

        # 검색어 조합 생성 (더 다양하고 정확한 검색어)
        for _ in range(8):  # 더 많은 검색어 생성
            genre = random.choice(dance_genres)
            mood = random.choice(energy_moods + valence_moods)
            tempo_desc = random.choice(tempo_descriptors)
            acoustic_desc = random.choice(acoustic_descriptors)

            patterns = [
                f"{genre} {mood}",
                f"{mood} {genre} music",
                f"{tempo_desc} {genre}",
                f"{genre} {tempo_desc} tempo",
                f"{mood} {tempo_desc} music",
                f"{acoustic_desc} {genre}",
                f"{genre} {acoustic_desc}",
                f"{mood} {acoustic_desc} {genre}",
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
