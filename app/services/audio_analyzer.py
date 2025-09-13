import librosa
import numpy as np
from typing import Dict, Any, Optional, Tuple
import tempfile
import os
from pathlib import Path
from .advanced_audio_analyzer import AdvancedAudioAnalyzer


class AudioAnalyzer:
    """오디오 분석을 위한 클래스"""

    def __init__(self):
        self.sample_rate = 44100
        self.advanced_analyzer = AdvancedAudioAnalyzer()

    def extract_features(self, audio_file_path: str) -> Dict[str, Any]:
        """
        오디오 파일에서 특징을 추출합니다.

        Args:
            audio_file_path: 오디오 파일 경로

        Returns:
            추출된 오디오 특징 딕셔너리
        """
        try:
            # 오디오 로드
            y, sr = librosa.load(audio_file_path, sr=self.sample_rate)

            # 기본 특징 추출
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

            # 조성 분석
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            tonnetz = librosa.feature.tonnetz(y=y, sr=sr)

            # MFCC 특징
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

            # 스펙트럴 특징
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]

            # 리듬 특징
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
            onset_times = librosa.frames_to_time(onset_frames, sr=sr)

            # 음량 분석
            rms = librosa.feature.rms(y=y)[0]

            return {
                "tempo": float(tempo),
                "beats": len(beats),
                "chroma_mean": np.mean(chroma, axis=1).tolist(),
                "tonnetz_mean": np.mean(tonnetz, axis=1).tolist(),
                "mfcc_mean": np.mean(mfccs, axis=1).tolist(),
                "spectral_centroid_mean": float(np.mean(spectral_centroids)),
                "spectral_rolloff_mean": float(np.mean(spectral_rolloff)),
                "zero_crossing_rate_mean": float(np.mean(zero_crossing_rate)),
                "onset_count": len(onset_times),
                "rms_mean": float(np.mean(rms)),
                "duration": len(y) / sr,
            }

        except Exception as e:
            raise Exception(f"오디오 분석 중 오류 발생: {str(e)}")

    def estimate_key_and_mode(self, audio_file_path: str) -> Tuple[int, int]:
        """
        오디오의 조성과 장조/단조를 추정합니다.

        Args:
            audio_file_path: 오디오 파일 경로

        Returns:
            (key, mode) 튜플 (key: 0-11, mode: 0=단조, 1=장조)
        """
        try:
            y, sr = librosa.load(audio_file_path, sr=self.sample_rate)

            # 크로마 특징 추출
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)

            # 조성 추정
            key_profiles = librosa.feature.chroma_stft(y=y, sr=sr)
            key_profile = np.mean(key_profiles, axis=1)

            # 주요 조성과 단조 프로파일
            major_profile = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])  # C major
            minor_profile = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])  # A minor

            # 유사도 계산
            major_similarities = []
            minor_similarities = []

            for i in range(12):
                # 회전된 프로파일
                major_rotated = np.roll(major_profile, i)
                minor_rotated = np.roll(minor_profile, i)

                # 코사인 유사도
                major_sim = np.dot(key_profile, major_rotated) / (
                    np.linalg.norm(key_profile) * np.linalg.norm(major_rotated)
                )
                minor_sim = np.dot(key_profile, minor_rotated) / (
                    np.linalg.norm(key_profile) * np.linalg.norm(minor_rotated)
                )

                major_similarities.append(major_sim)
                minor_similarities.append(minor_sim)

            # 최고 유사도 찾기
            max_major_idx = np.argmax(major_similarities)
            max_minor_idx = np.argmax(minor_similarities)

            if major_similarities[max_major_idx] > minor_similarities[max_minor_idx]:
                return max_major_idx, 1  # 장조
            else:
                return max_minor_idx, 0  # 단조

        except Exception as e:
            # 기본값 반환
            return 0, 1  # C major

    def calculate_danceability(self, audio_file_path: str) -> float:
        """
        춤추기 좋은 정도를 계산합니다.

        Args:
            audio_file_path: 오디오 파일 경로

        Returns:
            danceability 점수 (0.0-1.0)
        """
        try:
            y, sr = librosa.load(audio_file_path, sr=self.sample_rate)

            # 템포 기반 점수
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            tempo_score = min(1.0, max(0.0, (tempo - 60) / 120))  # 60-180 BPM 범위

            # 비트 강도
            onset_strength = librosa.onset.onset_strength(y=y, sr=sr)
            beat_strength = np.mean(onset_strength)
            beat_score = min(1.0, beat_strength / 2.0)

            # 리듬 안정성
            tempo_variation = np.std(librosa.beat.tempo(y=y, sr=sr, aggregate=None))
            stability_score = max(0.0, 1.0 - tempo_variation / 20.0)

            # 종합 점수
            danceability = tempo_score * 0.4 + beat_score * 0.4 + stability_score * 0.2
            return float(min(1.0, max(0.0, danceability)))

        except Exception as e:
            return 0.5  # 기본값

    def calculate_energy(self, audio_file_path: str) -> float:
        """
        에너지/강렬함을 계산합니다.

        Args:
            audio_file_path: 오디오 파일 경로

        Returns:
            energy 점수 (0.0-1.0)
        """
        try:
            y, sr = librosa.load(audio_file_path, sr=self.sample_rate)

            # RMS 에너지
            rms = librosa.feature.rms(y=y)[0]
            rms_energy = np.mean(rms)

            # 스펙트럴 에너지
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_energy = np.mean(spectral_centroids) / 5000.0  # 정규화

            # 다이나믹 범위
            dynamic_range = np.max(y) - np.min(y)

            # 종합 점수
            energy = rms_energy * 0.5 + spectral_energy * 0.3 + dynamic_range * 0.2
            return float(min(1.0, max(0.0, energy)))

        except Exception as e:
            return 0.5  # 기본값

    def calculate_valence(self, audio_file_path: str) -> float:
        """
        정서적 긍정성을 계산합니다.

        Args:
            audio_file_path: 오디오 파일 경로

        Returns:
            valence 점수 (0.0-1.0)
        """
        try:
            y, sr = librosa.load(audio_file_path, sr=self.sample_rate)

            # 조성 기반 점수
            key, mode = self.estimate_key_and_mode(audio_file_path)
            mode_score = float(mode)  # 장조=1, 단조=0

            # 템포 기반 점수
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            tempo_score = min(1.0, max(0.0, (tempo - 80) / 100))  # 80-180 BPM 범위

            # 하모닉스 vs 페르쿠시브
            harmonic, percussive = librosa.effects.hpss(y)
            harmonic_ratio = np.mean(np.abs(harmonic)) / (
                np.mean(np.abs(harmonic)) + np.mean(np.abs(percussive))
            )

            # 종합 점수
            valence = mode_score * 0.4 + tempo_score * 0.3 + harmonic_ratio * 0.3
            return float(min(1.0, max(0.0, valence)))

        except Exception as e:
            return 0.5  # 기본값

    def extract_advanced_features(self, audio_file_path: str) -> Dict[str, Any]:
        """
        고급 오디오 특징 추출 (딥러닝 모델 활용)

        Args:
            audio_file_path: 오디오 파일 경로

        Returns:
            고급 오디오 특징 딕셔너리
        """
        try:
            # 기본 특징 추출
            basic_features = self.extract_features(audio_file_path)

            # 고급 특징 추출
            advanced_features = self.advanced_analyzer.extract_deep_features(
                audio_file_path
            )

            # 장르 분석
            genre_probabilities = self.advanced_analyzer.analyze_music_genre(
                audio_file_path
            )

            # 감정 분석
            emotion_scores = self.advanced_analyzer.analyze_music_emotion(
                audio_file_path
            )

            # 통합된 특징 반환
            return {
                **basic_features,
                **advanced_features,
                "genre_probabilities": genre_probabilities,
                "emotion_scores": emotion_scores,
                "analysis_type": "advanced",
            }

        except Exception as e:
            print(f"고급 특징 추출 오류: {e}")
            # 기본 특징만 반환
            return self.extract_features(audio_file_path)

    def get_music_insights(self, audio_file_path: str) -> Dict[str, Any]:
        """
        음악에 대한 종합적인 인사이트 제공

        Args:
            audio_file_path: 오디오 파일 경로

        Returns:
            음악 인사이트 딕셔너리
        """
        try:
            features = self.extract_advanced_features(audio_file_path)

            # 주요 장르 추출
            genre_probs = features.get("genre_probabilities", {})
            top_genre = (
                max(genre_probs.items(), key=lambda x: x[1])
                if genre_probs
                else ("unknown", 0.0)
            )

            # 주요 감정 추출
            emotion_scores = features.get("emotion_scores", {})
            top_emotion = (
                max(emotion_scores.items(), key=lambda x: x[1])
                if emotion_scores
                else ("neutral", 0.0)
            )

            # 템포 기반 분류
            tempo = features.get("tempo", 120)
            tempo_category = self._categorize_tempo(tempo)

            # 에너지 기반 분류
            energy = features.get("energy", 0.5)
            energy_category = self._categorize_energy(energy)

            return {
                "primary_genre": {"name": top_genre[0], "confidence": top_genre[1]},
                "primary_emotion": {"name": top_emotion[0], "score": top_emotion[1]},
                "tempo_category": tempo_category,
                "energy_category": energy_category,
                "complexity_score": self._calculate_complexity(features),
                "danceability_level": self._categorize_danceability(
                    features.get("danceability", 0.5)
                ),
                "mood_description": self._generate_mood_description(features),
            }

        except Exception as e:
            print(f"음악 인사이트 생성 오류: {e}")
            return {
                "primary_genre": {"name": "unknown", "confidence": 0.0},
                "primary_emotion": {"name": "neutral", "score": 0.0},
                "tempo_category": "medium",
                "energy_category": "medium",
                "complexity_score": 0.5,
                "danceability_level": "moderate",
                "mood_description": "분석할 수 없습니다.",
            }

    def _categorize_tempo(self, tempo: float) -> str:
        """템포 카테고리 분류"""
        if tempo < 80:
            return "slow"
        elif tempo < 120:
            return "medium"
        elif tempo < 160:
            return "fast"
        else:
            return "very_fast"

    def _categorize_energy(self, energy: float) -> str:
        """에너지 카테고리 분류"""
        if energy < 0.3:
            return "low"
        elif energy < 0.7:
            return "medium"
        else:
            return "high"

    def _calculate_complexity(self, features: Dict[str, Any]) -> float:
        """음악 복잡도 계산"""
        try:
            # 다양한 특징을 기반으로 복잡도 계산
            mfcc_variance = np.var(features.get("mfcc_mean", [0.0] * 13))
            chroma_variance = np.var(features.get("chroma_mean", [0.0] * 12))
            onset_count = features.get("onset_count", 0)

            # 정규화된 복잡도 점수
            complexity = min(
                1.0, (mfcc_variance + chroma_variance + onset_count / 100) / 3
            )
            return float(complexity)
        except:
            return 0.5

    def _categorize_danceability(self, danceability: float) -> str:
        """댄서빌리티 레벨 분류"""
        if danceability < 0.3:
            return "low"
        elif danceability < 0.7:
            return "moderate"
        else:
            return "high"

    def _generate_mood_description(self, features: Dict[str, Any]) -> str:
        """분위기 설명 생성"""
        try:
            valence = features.get("valence", 0.5)
            energy = features.get("energy", 0.5)
            tempo = features.get("tempo", 120)

            if valence > 0.7 and energy > 0.6:
                return "밝고 활기찬 분위기"
            elif valence > 0.7 and energy < 0.4:
                return "평온하고 긍정적인 분위기"
            elif valence < 0.3 and energy > 0.6:
                return "강렬하고 어두운 분위기"
            elif valence < 0.3 and energy < 0.4:
                return "차분하고 우울한 분위기"
            elif tempo > 140:
                return "빠르고 역동적인 분위기"
            elif tempo < 80:
                return "느리고 차분한 분위기"
            else:
                return "균형잡힌 중간 템포의 분위기"
        except:
            return "분위기를 분석할 수 없습니다."
