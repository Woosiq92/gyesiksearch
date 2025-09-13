import torch
import torchaudio
import numpy as np
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Processor
from typing import Dict, Any, List, Optional
import librosa
import tempfile
import os


class AdvancedAudioAnalyzer:
    """고급 오디오 분석을 위한 클래스 - 딥러닝 모델 활용"""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.sample_rate = 16000  # Wav2Vec2 모델용 샘플링 레이트

        # 모델 로딩 (실제 사용 시에는 사전 훈련된 모델 사용)
        try:
            # 음악 장르 분류 모델 (예시)
            self.genre_model = None  # 실제 모델 로딩
            self.genre_processor = None
            self.model_loaded = False
        except Exception as e:
            print(f"고급 모델 로딩 실패: {e}")
            self.model_loaded = False

    def extract_deep_features(self, audio_file_path: str) -> Dict[str, Any]:
        """
        딥러닝 모델을 사용한 고급 오디오 특징 추출

        Args:
            audio_file_path: 오디오 파일 경로

        Returns:
            고급 오디오 특징 딕셔너리
        """
        try:
            # 오디오 로드 및 전처리
            waveform, sample_rate = torchaudio.load(audio_file_path)

            # 모노로 변환
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)

            # 리샘플링
            if sample_rate != self.sample_rate:
                resampler = torchaudio.transforms.Resample(
                    sample_rate, self.sample_rate
                )
                waveform = resampler(waveform)

            # 길이 조정 (최대 30초)
            max_length = self.sample_rate * 30
            if waveform.shape[1] > max_length:
                waveform = waveform[:, :max_length]
            elif waveform.shape[1] < self.sample_rate * 5:  # 최소 5초
                # 패딩 추가
                padding_length = self.sample_rate * 5 - waveform.shape[1]
                waveform = torch.nn.functional.pad(waveform, (0, padding_length))

            # 특징 추출
            features = {
                "waveform_length": waveform.shape[1],
                "sample_rate": self.sample_rate,
                "rms_energy": torch.sqrt(torch.mean(waveform**2)).item(),
                "zero_crossing_rate": self._calculate_zcr(waveform),
                "spectral_centroid": self._calculate_spectral_centroid(waveform),
                "spectral_rolloff": self._calculate_spectral_rolloff(waveform),
                "mfcc_features": self._extract_mfcc(waveform),
                "chroma_features": self._extract_chroma(waveform),
            }

            # 딥러닝 모델이 로드된 경우 추가 분석
            if self.model_loaded:
                features.update(self._extract_deep_features(waveform))

            return features

        except Exception as e:
            print(f"고급 특징 추출 오류: {e}")
            return self._get_default_features()

    def _calculate_zcr(self, waveform: torch.Tensor) -> float:
        """제로 크로싱 레이트 계산"""
        try:
            # numpy로 변환하여 계산
            audio_np = waveform.squeeze().numpy()
            zcr = np.mean(librosa.feature.zero_crossing_rate(audio_np))
            return float(zcr)
        except:
            return 0.0

    def _calculate_spectral_centroid(self, waveform: torch.Tensor) -> float:
        """스펙트럴 센트로이드 계산"""
        try:
            audio_np = waveform.squeeze().numpy()
            spectral_centroids = librosa.feature.spectral_centroid(
                y=audio_np, sr=self.sample_rate
            )[0]
            return float(np.mean(spectral_centroids))
        except:
            return 2000.0

    def _calculate_spectral_rolloff(self, waveform: torch.Tensor) -> float:
        """스펙트럴 롤오프 계산"""
        try:
            audio_np = waveform.squeeze().numpy()
            spectral_rolloff = librosa.feature.spectral_rolloff(
                y=audio_np, sr=self.sample_rate
            )[0]
            return float(np.mean(spectral_rolloff))
        except:
            return 4000.0

    def _extract_mfcc(self, waveform: torch.Tensor) -> List[float]:
        """MFCC 특징 추출"""
        try:
            audio_np = waveform.squeeze().numpy()
            mfccs = librosa.feature.mfcc(y=audio_np, sr=self.sample_rate, n_mfcc=13)
            return np.mean(mfccs, axis=1).tolist()
        except:
            return [0.0] * 13

    def _extract_chroma(self, waveform: torch.Tensor) -> List[float]:
        """크로마 특징 추출"""
        try:
            audio_np = waveform.squeeze().numpy()
            chroma = librosa.feature.chroma_stft(y=audio_np, sr=self.sample_rate)
            return np.mean(chroma, axis=1).tolist()
        except:
            return [0.0] * 12

    def _extract_deep_features(self, waveform: torch.Tensor) -> Dict[str, Any]:
        """딥러닝 모델을 사용한 특징 추출"""
        try:
            # 실제 구현에서는 사전 훈련된 모델 사용
            # 예: 음악 장르 분류, 감정 분석 등
            return {
                "deep_features": [0.0] * 128,  # 예시 벡터
                "genre_probabilities": [0.1] * 10,  # 예시 장르 확률
                "emotion_scores": [0.2] * 5,  # 예시 감정 점수
            }
        except:
            return {}

    def _get_default_features(self) -> Dict[str, Any]:
        """기본 특징 반환"""
        return {
            "waveform_length": 0,
            "sample_rate": self.sample_rate,
            "rms_energy": 0.1,
            "zero_crossing_rate": 0.05,
            "spectral_centroid": 2000.0,
            "spectral_rolloff": 4000.0,
            "mfcc_features": [0.0] * 13,
            "chroma_features": [0.0] * 12,
        }

    def analyze_music_genre(self, audio_file_path: str) -> Dict[str, float]:
        """
        음악 장르 분석 (딥러닝 모델 사용)

        Args:
            audio_file_path: 오디오 파일 경로

        Returns:
            장르별 확률 딕셔너리
        """
        if not self.model_loaded:
            return self._get_default_genre_probabilities()

        try:
            # 실제 구현에서는 사전 훈련된 장르 분류 모델 사용
            # 예: GTZAN 데이터셋으로 훈련된 모델
            return {
                "pop": 0.2,
                "rock": 0.15,
                "jazz": 0.1,
                "classical": 0.1,
                "electronic": 0.15,
                "hip_hop": 0.1,
                "country": 0.1,
                "blues": 0.05,
                "reggae": 0.03,
                "disco": 0.02,
            }
        except Exception as e:
            print(f"장르 분석 오류: {e}")
            return self._get_default_genre_probabilities()

    def _get_default_genre_probabilities(self) -> Dict[str, float]:
        """기본 장르 확률 반환"""
        return {
            "pop": 0.1,
            "rock": 0.1,
            "jazz": 0.1,
            "classical": 0.1,
            "electronic": 0.1,
            "hip_hop": 0.1,
            "country": 0.1,
            "blues": 0.1,
            "reggae": 0.1,
            "disco": 0.1,
        }

    def analyze_music_emotion(self, audio_file_path: str) -> Dict[str, float]:
        """
        음악 감정 분석

        Args:
            audio_file_path: 오디오 파일 경로

        Returns:
            감정별 점수 딕셔너리
        """
        try:
            # 기본적인 감정 분석 (실제로는 더 정교한 모델 사용)
            features = self.extract_deep_features(audio_file_path)

            # 템포와 에너지 기반 감정 추정
            tempo = self._estimate_tempo(audio_file_path)
            energy = features.get("rms_energy", 0.1)

            emotions = {
                "happy": min(1.0, (tempo - 60) / 120 * energy),
                "sad": max(0.0, 1.0 - (tempo - 60) / 120),
                "angry": min(1.0, energy * 2),
                "calm": max(0.0, 1.0 - energy),
                "energetic": min(1.0, energy * 1.5),
            }

            # 정규화
            total = sum(emotions.values())
            if total > 0:
                emotions = {k: v / total for k, v in emotions.items()}

            return emotions

        except Exception as e:
            print(f"감정 분석 오류: {e}")
            return {
                "happy": 0.2,
                "sad": 0.2,
                "angry": 0.2,
                "calm": 0.2,
                "energetic": 0.2,
            }

    def _estimate_tempo(self, audio_file_path: str) -> float:
        """템포 추정"""
        try:
            y, sr = librosa.load(audio_file_path, sr=self.sample_rate)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            return float(tempo)
        except:
            return 120.0
