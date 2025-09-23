import openai
from typing import Dict, Any, List, Optional
from app.core.config import settings


class ChatGPTService:
    """ChatGPT API 연동을 위한 서비스 클래스"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = None

        print(f"ChatGPT 서비스 초기화 시작 - API 키 존재: {self.api_key is not None}")
        if self.api_key:
            print(f"API 키 길이: {len(self.api_key)}")
            print(f"API 키 시작 부분: {self.api_key[:10]}...")

        if self.api_key:
            try:
                # 환경변수에 API 키 설정 후 클라이언트 초기화
                import os

                os.environ["OPENAI_API_KEY"] = self.api_key

                # 간단한 클라이언트 초기화 (proxies 인수 문제 회피)
                self.client = openai.OpenAI()
                print(f"ChatGPT 서비스 초기화 성공 - 클라이언트 생성됨")
            except Exception as e:
                print(f"OpenAI 클라이언트 초기화 실패: {e}")
                # 최종 대안: 직접 API 호출 방식 사용
                self.client = None
                print("ChatGPT 서비스는 직접 API 호출 방식으로 작동합니다.")
        else:
            print("OpenAI API 키가 설정되지 않았습니다.")
            print(f"Settings에서 가져온 API 키: {settings.OPENAI_API_KEY}")

    def analyze_audio_features(
        self,
        audio_features: Dict[str, Any],
        track_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Audio Features를 분석하여 음악적 특성을 설명합니다.

        Args:
            audio_features: Spotify Audio Features
            track_info: 곡 정보 (선택사항)

        Returns:
            분석 결과 텍스트
        """
        if not self.client and not self.api_key:
            print("ChatGPT 클라이언트와 API 키가 모두 없습니다.")
            return "ChatGPT API 설정이 필요합니다."

        try:
            print(f"ChatGPT 분석 시작 - 오디오 특징: {audio_features}")
            # 프롬프트 생성
            prompt = self._create_analysis_prompt(audio_features, track_info)
            print(f"생성된 프롬프트: {prompt}")

            # 클라이언트가 있으면 사용, 없으면 직접 API 호출
            if self.client:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "당신은 음악 분석 전문가입니다. 간결하고 명확하게 곡의 특성을 분석해주세요. 각 항목은 한 줄로만 설명해주세요.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=200,
                    temperature=0.7,
                )
                result = response.choices[0].message.content.strip()
            else:
                # 직접 API 호출
                import requests

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                data = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": "당신은 음악 분석 전문가입니다. 간결하고 명확하게 곡의 특성을 분석해주세요. 각 항목은 한 줄로만 설명해주세요.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 200,
                    "temperature": 0.7,
                }
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                )
                response.raise_for_status()
                result = response.json()["choices"][0]["message"]["content"].strip()

            print(f"ChatGPT 분석 결과: {result}")
            return result

        except Exception as e:
            print(f"ChatGPT 분석 중 오류 발생: {str(e)}")
            return f"음악 분석 중 오류가 발생했습니다: {str(e)}"

    def generate_recommendation_reason(
        self,
        original_features: Dict[str, Any],
        recommended_track: Dict[str, Any],
        similarity_score: float,
    ) -> str:
        """
        추천 근거를 생성합니다.

        Args:
            original_features: 원본 곡의 Audio Features
            recommended_track: 추천 곡 정보
            similarity_score: 유사도 점수

        Returns:
            추천 근거 텍스트
        """
        if not self.client:
            return f"이 곡은 유사도 {similarity_score:.1f}%로 추천되었습니다."

        try:
            prompt = f"""
다음 곡을 추천하는 간단한 이유를 한 줄로 설명해주세요:

원본 곡: 에너지 {original_features.get('energy', 0):.1f}, 밝음 {original_features.get('valence', 0):.1f}, 템포 {original_features.get('tempo', 0):.0f}BPM
추천 곡: {recommended_track.get('track_name', 'Unknown')} - {recommended_track.get('artist_name', 'Unknown')}
유사도: {similarity_score:.1f}%

친근하고 간결하게 추천 이유를 한 줄로 설명해주세요.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # 더 정확한 추천 근거 생성
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 음악 추천 전문가입니다. 곡의 특징을 바탕으로 친근하고 설득력 있는 추천 근거를 제공해주세요.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=100,  # 간결한 추천 근거를 위해 토큰 감소
                temperature=0.8,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"이 곡은 유사도 {similarity_score:.1f}%로 추천되었습니다."

    def analyze_mood_and_genre(self, audio_features: Dict[str, Any]) -> Dict[str, str]:
        """
        곡의 분위기와 장르를 분석합니다.

        Args:
            audio_features: Spotify Audio Features

        Returns:
            분석 결과 딕셔너리
        """
        if not self.client:
            return {
                "mood": "분석 불가",
                "genre": "분석 불가",
                "description": "ChatGPT API 설정이 필요합니다.",
            }

        try:
            prompt = f"""
다음 Spotify Audio Features를 분석하여 곡의 분위기와 장르를 추정해주세요:

- Danceability: {audio_features.get('danceability', 0):.2f} (춤추기 좋은 정도)
- Energy: {audio_features.get('energy', 0):.2f} (에너지/강렬함)
- Valence: {audio_features.get('valence', 0):.2f} (정서적 긍정성)
- Tempo: {audio_features.get('tempo', 0):.0f} BPM
- Key: {audio_features.get('key', 0)} (조성)
- Mode: {audio_features.get('mode', 1)} (장조/단조)
- Acousticness: {audio_features.get('acousticness', 0):.2f} (어쿠스틱 여부)
- Instrumentalness: {audio_features.get('instrumentalness', 0):.2f} (보컬 유무)
- Speechiness: {audio_features.get('speechiness', 0):.2f} (대화/랩 비율)

다음 형식으로 응답해주세요:
분위기: [분위기 설명]
장르: [추정 장르]
설명: [전체적인 곡의 특성 설명]
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # 더 정확한 장르 및 분위기 분석
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 음악 분석 전문가입니다. Audio Features를 바탕으로 곡의 분위기와 장르를 정확하게 분석해주세요.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,  # 더 상세한 분석
                temperature=0.6,
            )

            content = response.choices[0].message.content.strip()

            # 응답 파싱
            lines = content.split("\n")
            result = {}

            for line in lines:
                if line.startswith("분위기:"):
                    result["mood"] = line.replace("분위기:", "").strip()
                elif line.startswith("장르:"):
                    result["genre"] = line.replace("장르:", "").strip()
                elif line.startswith("설명:"):
                    result["description"] = line.replace("설명:", "").strip()

            return result

        except Exception as e:
            return {
                "mood": "분석 오류",
                "genre": "분석 오류",
                "description": f"분석 중 오류가 발생했습니다: {str(e)}",
            }

    def _create_analysis_prompt(
        self,
        audio_features: Dict[str, Any],
        track_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """분석 프롬프트를 생성합니다."""

        track_name = track_info.get("name", "Unknown") if track_info else "Unknown"
        artist_name = (
            track_info.get("artists", ["Unknown"])[0] if track_info else "Unknown"
        )

        prompt = f"""
다음 곡의 Audio Features를 분석해주세요:

주요 특징:
- 에너지: {audio_features.get('energy', 0):.1f}/1.0
- 밝음: {audio_features.get('valence', 0):.1f}/1.0  
- 춤추기 좋음: {audio_features.get('danceability', 0):.1f}/1.0
- 템포: {audio_features.get('tempo', 0):.0f} BPM

다음 형식으로 간단하게 분석해주세요:

🎵 **분위기**: [한 줄로 분위기 설명]
🎯 **장르**: [추정 장르]
💡 **추천 상황**: [언제 듣기 좋은지 한 줄로]
"""
        return prompt
