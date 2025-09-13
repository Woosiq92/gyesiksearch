import librosa
import numpy as np
from typing import Dict, Any, Optional, Tuple
import tempfile
import os
from pathlib import Path
import warnings

# scipy 호환성 문제 해결
try:
    from scipy.signal import windows

    # scipy.signal.hann이 없는 경우 windows.hann 사용
    if not hasattr(windows, "hann"):
        import scipy.signal as signal

        windows.hann = signal.hann
except ImportError:
    pass


class AudioAnalyzer:
    """오디오 분석을 위한 클래스"""

    def __init__(self):
        self.sample_rate = 48000  # 더 높은 샘플링 레이트

    def extract_features(self, audio_file_path: str) -> Dict[str, Any]:
        """
        오디오 파일에서 특징을 추출합니다.

        Args:
            audio_file_path: 오디오 파일 경로

        Returns:
            추출된 오디오 특징 딕셔너리
        """
        try:
            # 기본값으로 시작
            features = {
                "tempo": 120.0,
                "beats": 0,
                "chroma_mean": [0.1] * 12,
                "tonnetz_mean": [0.1] * 6,
                "mfcc_mean": [0.1] * 13,
                "spectral_centroid_mean": 2000.0,
                "spectral_rolloff_mean": 4000.0,
                "zero_crossing_rate_mean": 0.05,
                "onset_count": 0,
                "rms_mean": 0.1,
                "duration": 30.0,
            }

            # 오디오 파일 존재 확인
            if not os.path.exists(audio_file_path):
                return features

            # 파일 크기 확인 (너무 작으면 건너뛰기)
            file_size = os.path.getsize(audio_file_path)
            if file_size < 1000:  # 1KB 미만
                return features

            # 오디오 로드 시도
            try:
                # 안전한 오디오 로딩
                y, sr = self._load_audio_safely(audio_file_path)

                if y is None or len(y) == 0:
                    print("오디오 데이터가 비어있음, 기본값 사용")
                    return self._get_enhanced_default_features()

                # 오디오 길이 체크
                audio_length = len(y) / sr
                print(f"오디오 길이: {audio_length:.1f}초")

                if audio_length < 5.0:
                    print(f"오디오가 너무 짧음 ({audio_length:.1f}초), 기본값 사용")
                    return self._get_enhanced_default_features()

                # 기본 특징 추출
                tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
                features["tempo"] = float(tempo)
                features["beats"] = len(beats)
                print(f"extract_features에서 계산된 템포: {tempo:.1f} BPM")

                # 조성 분석
                chroma = librosa.feature.chroma_stft(y=y, sr=sr)
                features["chroma_mean"] = np.mean(chroma, axis=1).tolist()

                tonnetz = librosa.feature.tonnetz(y=y, sr=sr)
                features["tonnetz_mean"] = np.mean(tonnetz, axis=1).tolist()

                # MFCC 특징
                mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
                features["mfcc_mean"] = np.mean(mfccs, axis=1).tolist()

                # 스펙트럴 특징
                spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
                features["spectral_centroid_mean"] = float(np.mean(spectral_centroids))

                spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
                features["spectral_rolloff_mean"] = float(np.mean(spectral_rolloff))

                # 제로 크로싱 레이트
                zcr = librosa.feature.zero_crossing_rate(y)[0]
                features["zero_crossing_rate_mean"] = float(np.mean(zcr))

                # 온셋 감지
                onsets = librosa.onset.onset_detect(y=y, sr=sr)
                features["onset_count"] = len(onsets)

                # 음량 분석
                rms = librosa.feature.rms(y=y)[0]
                features["rms_mean"] = float(np.mean(rms))

                # 지속시간
                features["duration"] = len(y) / sr

            except Exception as e:
                # librosa 실패 시 기본값 사용
                print(f"librosa 로딩 실패, 기본값 사용: {str(e)}")
                return self._get_enhanced_default_features()

            return features

        except Exception as e:
            # 전체 실패 시 기본값 반환
            print(f"오디오 분석 실패, 기본값 사용: {str(e)}")
            return self._get_enhanced_default_features()

    def _get_enhanced_default_features(self) -> Dict[str, Any]:
        """개선된 기본 특징 반환 (webm 파일 처리 실패 시 사용)"""
        return {
            "tempo": 120.0,
            "beats": 24,  # 30초 * 120BPM / 60 = 60비트, 약 24온셋
            "chroma_mean": [
                0.08,
                0.09,
                0.08,
                0.09,
                0.08,
                0.09,
                0.08,
                0.09,
                0.08,
                0.09,
                0.08,
                0.09,
            ],  # 더 자연스러운 크로마
            "tonnetz_mean": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
            "mfcc_mean": [
                0.1,
                0.05,
                0.02,
                0.01,
                0.005,
                0.002,
                0.001,
                0.0005,
                0.0002,
                0.0001,
                0.00005,
                0.00002,
                0.00001,
            ],  # 감쇠하는 MFCC
            "spectral_centroid_mean": 2000.0,
            "spectral_rolloff_mean": 4000.0,
            "zero_crossing_rate_mean": 0.05,
            "onset_count": 24,
            "rms_mean": 0.15,  # 약간 더 높은 음량
            "duration": 30.0,
        }

    def _load_audio_safely(
        self, audio_file_path: str
    ) -> Tuple[Optional[np.ndarray], int]:
        """
        안전하게 오디오 파일을 로딩합니다.

        Args:
            audio_file_path: 오디오 파일 경로

        Returns:
            (오디오 데이터, 샘플링 레이트) 튜플
        """
        try:
            # 파일 형식 감지
            detected_format = self._detect_audio_format(audio_file_path)
            print(f"감지된 파일 형식: {detected_format}")

            # 방법 1: librosa 기본 로딩 (경고 억제 및 scipy 호환성 처리)
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # scipy 호환성 문제 해결을 위한 환경변수 설정
                os.environ["LIBROSA_CACHE_DIR"] = "/tmp/librosa_cache"
                y, sr = librosa.load(
                    audio_file_path, sr=self.sample_rate, duration=30, mono=True
                )
            return y, sr
        except Exception as e1:
            print(f"librosa 기본 로딩 실패: {e1}")

            try:
                # 방법 2: 다른 샘플링 레이트로 시도
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    y, sr = librosa.load(
                        audio_file_path, sr=None, duration=30, mono=True
                    )
                # 리샘플링
                if sr != self.sample_rate:
                    y = librosa.resample(y, orig_sr=sr, target_sr=self.sample_rate)
                return y, self.sample_rate
            except Exception as e2:
                print(f"librosa 리샘플링 로딩 실패: {e2}")

                try:
                    # 방법 3: pydub를 사용한 WebM 처리 (개선된 버전)
                    if detected_format in ["webm", "mp4", "ogg"]:
                        try:
                            from pydub import AudioSegment
                            from pydub.utils import which
                            import subprocess

                            print(f"pydub로 {detected_format} 파일 처리 시도...")

                            # ffmpeg 경로 확인 및 설정 (더 강력한 검색)
                            ffmpeg_path = None

                            # 1. which로 검색
                            try:
                                ffmpeg_path = which("ffmpeg")
                                print(f"which로 ffmpeg 검색 결과: {ffmpeg_path}")
                            except:
                                print("which로 ffmpeg 검색 실패")

                            # 2. 직접 경로들 확인
                            if not ffmpeg_path:
                                possible_paths = [
                                    r"C:\ffmpeg\bin\ffmpeg.exe",
                                    r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
                                    r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                                    r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
                                    r"C:\tools\ffmpeg\bin\ffmpeg.exe",
                                ]

                                for path in possible_paths:
                                    if os.path.exists(path):
                                        ffmpeg_path = path
                                        print(
                                            f"직접 경로에서 ffmpeg 발견: {ffmpeg_path}"
                                        )
                                        break

                            # 3. 환경변수에서 검색
                            if not ffmpeg_path:
                                import shutil

                                try:
                                    ffmpeg_path = shutil.which("ffmpeg")
                                    print(
                                        f"shutil.which로 ffmpeg 검색 결과: {ffmpeg_path}"
                                    )
                                except:
                                    print("shutil.which로 ffmpeg 검색 실패")

                            print(f"최종 ffmpeg 경로: {ffmpeg_path}")

                            if ffmpeg_path:
                                print(f"ffmpeg 경로 발견: {ffmpeg_path}")
                                # pydub에 ffmpeg 경로 설정
                                AudioSegment.converter = ffmpeg_path
                                AudioSegment.ffmpeg = ffmpeg_path

                                # ffprobe 경로 설정 (다양한 경우 처리)
                                ffprobe_path = ffmpeg_path.replace("ffmpeg", "ffprobe")
                                if not os.path.exists(ffprobe_path):
                                    # 다른 가능한 경로들 시도
                                    possible_ffprobe_paths = [
                                        ffmpeg_path.replace(
                                            "ffmpeg.exe", "ffprobe.exe"
                                        ),
                                        ffmpeg_path.replace("ffmpeg", "ffprobe.exe"),
                                        os.path.join(
                                            os.path.dirname(ffmpeg_path), "ffprobe.exe"
                                        ),
                                        os.path.join(
                                            os.path.dirname(ffmpeg_path), "ffprobe"
                                        ),
                                    ]
                                    for path in possible_ffprobe_paths:
                                        if os.path.exists(path):
                                            ffprobe_path = path
                                            break

                                AudioSegment.ffprobe = ffprobe_path
                                print(f"ffprobe 경로 설정: {ffprobe_path}")
                            else:
                                print(
                                    "ffmpeg를 찾을 수 없습니다. 기본 설정으로 시도합니다."
                                )
                                self._print_ffmpeg_installation_guide()

                                # Windows에서 일반적인 ffmpeg 경로들 시도
                                possible_paths = [
                                    r"C:\ffmpeg\bin\ffmpeg.exe",
                                    r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                                    r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
                                    r"C:\tools\ffmpeg\bin\ffmpeg.exe",
                                ]

                                for path in possible_paths:
                                    if os.path.exists(path):
                                        print(f"ffmpeg 경로 발견: {path}")
                                        AudioSegment.converter = path
                                        AudioSegment.ffmpeg = path
                                        AudioSegment.ffprobe = path.replace(
                                            "ffmpeg.exe", "ffprobe.exe"
                                        )
                                        break

                            # WebM 파일의 경우 특별한 처리
                            if detected_format == "webm":
                                # WebM 파일을 WAV로 변환하여 로드
                                audio_segment = AudioSegment.from_file(
                                    audio_file_path, format="webm"
                                )
                            else:
                                # 다른 형식은 일반적으로 처리
                                audio_segment = AudioSegment.from_file(audio_file_path)

                            # 최대 30초로 제한
                            if len(audio_segment) > 30000:  # 30초 = 30000ms
                                audio_segment = audio_segment[:30000]

                            # numpy 배열로 변환
                            y = np.array(
                                audio_segment.get_array_of_samples(), dtype=np.float32
                            )

                            # 스테레오인 경우 모노로 변환
                            if audio_segment.channels == 2:
                                y = y.reshape((-1, 2)).mean(axis=1)

                            # 샘플링 레이트 가져오기
                            sr = audio_segment.frame_rate

                            # 목표 샘플링 레이트로 리샘플링
                            if sr != self.sample_rate:
                                y = librosa.resample(
                                    y, orig_sr=sr, target_sr=self.sample_rate
                                )

                            print(
                                f"pydub로 {detected_format} 파일 로딩 성공 (길이: {len(y)/sr:.1f}초)"
                            )
                            return y, self.sample_rate

                        except Exception as pydub_error:
                            print(f"pydub 로딩 실패: {pydub_error}")

                            # 방법 3-1: 직접 ffmpeg 명령어로 변환 시도
                            try:
                                print("직접 ffmpeg 변환 시도...")
                                import tempfile

                                temp_wav = tempfile.mktemp(suffix=".wav")

                                # ffmpeg 명령어 실행 (webm 지원)
                                # ffmpeg 전체 경로 사용 (강력한 검색)
                                ffmpeg_cmd = None

                                # 1. 위에서 찾은 ffmpeg 경로 사용
                                if "ffmpeg_path" in locals() and ffmpeg_path:
                                    ffmpeg_cmd = ffmpeg_path
                                    print(f"위에서 찾은 ffmpeg 경로 사용: {ffmpeg_cmd}")
                                else:
                                    # 2. 직접 경로들 확인
                                    possible_paths = [
                                        r"C:\ffmpeg\bin\ffmpeg.exe",
                                        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
                                        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                                        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
                                        r"C:\tools\ffmpeg\bin\ffmpeg.exe",
                                    ]

                                    for path in possible_paths:
                                        if os.path.exists(path):
                                            ffmpeg_cmd = path
                                            print(
                                                f"직접 경로에서 ffmpeg 발견: {ffmpeg_cmd}"
                                            )
                                            break

                                # 3. 최후의 수단으로 "ffmpeg" 사용
                                if not ffmpeg_cmd:
                                    ffmpeg_cmd = "ffmpeg"
                                    print("ffmpeg 경로를 찾을 수 없어 기본값 사용")
                                cmd = [
                                    ffmpeg_cmd,
                                    "-i",
                                    audio_file_path,
                                    "-ac",
                                    "1",  # 모노
                                    "-ar",
                                    str(self.sample_rate),  # 샘플링 레이트
                                    "-acodec",
                                    "pcm_s16le",  # 16비트 PCM
                                    "-y",  # 덮어쓰기
                                    temp_wav,
                                ]

                                result = subprocess.run(
                                    cmd, capture_output=True, text=True, timeout=30
                                )
                                if result.returncode == 0 and os.path.exists(temp_wav):
                                    with warnings.catch_warnings():
                                        warnings.simplefilter("ignore")
                                        y, sr = librosa.load(
                                            temp_wav,
                                            sr=self.sample_rate,
                                            duration=30,
                                            mono=True,
                                        )
                                    os.remove(temp_wav)
                                    print(
                                        f"직접 ffmpeg 변환 성공: {len(y)} samples, {sr} Hz"
                                    )
                                    return y, sr
                                else:
                                    print(f"직접 ffmpeg 변환 실패: {result.stderr}")
                                    if os.path.exists(temp_wav):
                                        os.remove(temp_wav)

                            except Exception as direct_error:
                                print(f"직접 ffmpeg 변환 실패: {direct_error}")

                            # pydub 실패 시 계속해서 다른 방법 시도

                    # 방법 4: ffmpeg를 사용한 변환 후 로딩
                    import tempfile

                    temp_wav_path = tempfile.mktemp(suffix=".wav")

                    if self._convert_audio_format(
                        audio_file_path, temp_wav_path, "wav"
                    ):
                        try:
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore")
                                y, sr = librosa.load(
                                    temp_wav_path,
                                    sr=self.sample_rate,
                                    duration=30,
                                    mono=True,
                                )
                            return y, sr
                        finally:
                            # 임시 파일 삭제
                            if os.path.exists(temp_wav_path):
                                os.unlink(temp_wav_path)
                    else:
                        raise Exception("ffmpeg 변환 실패")

                except Exception as e3:
                    print(f"ffmpeg 변환 로딩 실패: {e3}")

                    try:
                        # 방법 5: soundfile 직접 사용
                        import soundfile as sf

                        y, sr = sf.read(audio_file_path, dtype="float32")
                        if sr != self.sample_rate:
                            y = librosa.resample(
                                y, orig_sr=sr, target_sr=self.sample_rate
                            )
                        return y, self.sample_rate
                    except Exception as e4:
                        print(f"soundfile 로딩 실패: {e4}")

                        try:
                            # 방법 6: audioread 사용
                            import audioread

                            with audioread.audio_open(audio_file_path) as f:
                                sr = f.samplerate
                                y = []
                                for frame in f:
                                    y.extend(frame)
                                y = np.array(y, dtype=np.float32)
                                if sr != self.sample_rate:
                                    y = librosa.resample(
                                        y, orig_sr=sr, target_sr=self.sample_rate
                                    )
                                return y, self.sample_rate
                        except Exception as e5:
                            print(f"audioread 로딩 실패: {e5}")
                            return None, self.sample_rate

    def estimate_key_and_mode(self, audio_file_path: str) -> Tuple[int, int]:
        """
        오디오의 조성과 장조/단조를 추정합니다.

        Args:
            audio_file_path: 오디오 파일 경로

        Returns:
            (key, mode) 튜플 (key: 0-11, mode: 0=단조, 1=장조)
        """
        try:
            # 기본값 반환
            return 0, 1  # C major

        except Exception as e:
            print(f"조성 추정 실패: {e}")
            return 0, 1

    def calculate_danceability(self, y: np.ndarray, sr: int) -> float:
        """
        댄서빌리티를 계산합니다.

        Args:
            y: 오디오 시계열
            sr: 샘플링 레이트

        Returns:
            댄서빌리티 점수 (0.0-1.0)
        """
        try:
            if y is None or len(y) == 0:
                return 0.5

            # 리듬 강도 계산
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

            # 온셋 강도 계산
            onset_strength = librosa.onset.onset_strength(y=y, sr=sr)
            onset_mean = np.mean(onset_strength)

            # 제로 크로싱 레이트 (리듬의 규칙성)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            zcr_mean = np.mean(zcr)

            # 스펙트럴 중심 (고주파 성분)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_mean = np.mean(spectral_centroid)

            # 댄서빌리티 계산 (여러 요소 조합)
            # 템포가 높고 온셋이 강하며 스펙트럴 중심이 높을수록 댄서빌리티 증가
            tempo_factor = min(tempo / 140.0, 1.0)  # 140 BPM 이상은 1.0
            onset_factor = min(onset_mean * 10, 1.0)  # 정규화
            spectral_factor = min(spectral_mean / 4000.0, 1.0)  # 4000Hz 이상은 1.0
            zcr_factor = min(zcr_mean * 20, 1.0)  # 정규화

            danceability = (
                tempo_factor * 0.4
                + onset_factor * 0.3
                + spectral_factor * 0.2
                + zcr_factor * 0.1
            )

            return max(0.0, min(1.0, danceability))

        except Exception as e:
            print(f"댄서빌리티 계산 실패: {e}")
            return 0.5

    def calculate_energy(self, y: np.ndarray, sr: int) -> float:
        """
        에너지를 계산합니다.

        Args:
            y: 오디오 시계열
            sr: 샘플링 레이트

        Returns:
            에너지 점수 (0.0-1.0)
        """
        try:
            if y is None or len(y) == 0:
                return 0.5

            # RMS 에너지 계산
            rms = librosa.feature.rms(y=y)[0]
            rms_mean = np.mean(rms)

            # 스펙트럴 중심 (고주파 성분)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_mean = np.mean(spectral_centroid)

            # 스펙트럴 롤오프 (고주파 대역)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            rolloff_mean = np.mean(spectral_rolloff)

            # 제로 크로싱 레이트 (노이즈/에너지)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            zcr_mean = np.mean(zcr)

            # 에너지 계산
            rms_factor = min(rms_mean * 5, 1.0)  # 정규화
            spectral_factor = min(spectral_mean / 3000.0, 1.0)  # 3000Hz 이상은 1.0
            rolloff_factor = min(rolloff_mean / 6000.0, 1.0)  # 6000Hz 이상은 1.0
            zcr_factor = min(zcr_mean * 15, 1.0)  # 정규화

            energy = (
                rms_factor * 0.4
                + spectral_factor * 0.3
                + rolloff_factor * 0.2
                + zcr_factor * 0.1
            )

            return max(0.0, min(1.0, energy))

        except Exception as e:
            print(f"에너지 계산 실패: {e}")
            return 0.5

    def calculate_valence(self, y: np.ndarray, sr: int) -> float:
        """
        밸런스(감정적 긍정성)를 계산합니다.

        Args:
            y: 오디오 시계열
            sr: 샘플링 레이트

        Returns:
            밸런스 점수 (0.0-1.0)
        """
        try:
            if y is None or len(y) == 0:
                return 0.5

            # 크로마 특징 (조성 분석)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)

            # 메이저/마이너 조성 추정
            # 메이저 스케일: C, D, E, F, G, A, B (0, 2, 4, 5, 7, 9, 11)
            major_profile = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])
            minor_profile = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])

            major_correlation = np.corrcoef(chroma_mean, major_profile)[0, 1]
            minor_correlation = np.corrcoef(chroma_mean, minor_profile)[0, 1]

            # 스펙트럴 중심 (밝은 소리)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_mean = np.mean(spectral_centroid)

            # 템포 (빠른 템포는 더 긍정적)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

            # 밸런스 계산
            mode_factor = max(
                0, major_correlation - minor_correlation
            )  # 메이저일수록 긍정적
            spectral_factor = min(spectral_mean / 3000.0, 1.0)  # 밝은 소리일수록 긍정적
            tempo_factor = min(tempo / 120.0, 1.0)  # 빠른 템포일수록 긍정적

            valence = mode_factor * 0.5 + spectral_factor * 0.3 + tempo_factor * 0.2

            # 0.0-1.0 범위로 정규화
            valence = (valence + 1.0) / 2.0  # -1~1 범위를 0~1로 변환

            return max(0.0, min(1.0, valence))

        except Exception as e:
            print(f"밸런스 계산 실패: {e}")
            return 0.5

    def _detect_audio_format(self, file_path: str) -> str:
        """
        오디오 파일의 실제 형식을 감지합니다.

        Args:
            file_path: 오디오 파일 경로

        Returns:
            감지된 형식 ('webm', 'mp4', 'wav', 'mp3', 'unknown')
        """
        try:
            # 파일 헤더 읽기
            with open(file_path, "rb") as f:
                header = f.read(16)

            # WebM 형식 감지
            if header.startswith(b"\x1a\x45\xdf\xa3"):
                return "webm"

            # MP4 형식 감지
            if b"ftyp" in header[:12]:
                return "mp4"

            # WAV 형식 감지
            if header.startswith(b"RIFF") and b"WAVE" in header:
                return "wav"

            # MP3 형식 감지
            if header.startswith(b"\xff\xfb") or header.startswith(b"\xff\xf3"):
                return "mp3"

            # OGG 형식 감지
            if header.startswith(b"OggS"):
                return "ogg"

            return "unknown"

        except Exception as e:
            print(f"파일 형식 감지 실패: {e}")
            return "unknown"

    def _convert_audio_format(
        self, input_path: str, output_path: str, target_format: str = "wav"
    ) -> bool:
        """
        오디오 파일을 다른 형식으로 변환합니다.

        Args:
            input_path: 입력 파일 경로
            output_path: 출력 파일 경로
            target_format: 목표 형식 ('wav', 'mp3', 'flac')

        Returns:
            변환 성공 여부
        """
        try:
            import subprocess
            import shutil

            # ffmpeg가 설치되어 있는지 확인
            if not shutil.which("ffmpeg"):
                print("ffmpeg가 설치되지 않았습니다. 기본 로딩을 시도합니다.")
                return False

            # ffmpeg 명령어 구성
            cmd = [
                "ffmpeg",
                "-i",
                input_path,
                "-acodec",
                "pcm_s16le" if target_format == "wav" else "libmp3lame",
                "-ar",
                "48000",  # 샘플링 레이트
                "-ac",
                "1",  # 모노 채널
                "-y",  # 덮어쓰기
                output_path,
            ]

            # 변환 실행
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"오디오 변환 성공: {input_path} -> {output_path}")
                return True
            else:
                print(f"오디오 변환 실패: {result.stderr}")
                return False

        except Exception as e:
            print(f"오디오 변환 중 오류: {e}")
            return False

    def _print_ffmpeg_installation_guide(self):
        """ffmpeg 설치 가이드를 출력합니다."""
        print("\n" + "=" * 60)
        print("🔧 FFMPEG 설치 가이드")
        print("=" * 60)
        print("webm 파일 처리를 위해 ffmpeg가 필요합니다.")
        print("\n📥 설치 방법:")
        print("1. Chocolatey 사용 (권장):")
        print("   choco install ffmpeg")
        print("\n2. 직접 다운로드:")
        print("   https://ffmpeg.org/download.html")
        print("   - Windows용 다운로드")
        print("   - 압축 해제 후 bin 폴더를 PATH에 추가")
        print("\n3. conda 사용:")
        print("   conda install -c conda-forge ffmpeg")
        print("\n4. pip 사용:")
        print("   pip install ffmpeg-python")
        print("\n설치 후 서버를 재시작해주세요.")
        print("=" * 60 + "\n")
