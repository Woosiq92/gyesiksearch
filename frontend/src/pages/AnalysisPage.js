import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Grid,
  Paper,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import MicIcon from '@mui/icons-material/Mic';
import StopIcon from '@mui/icons-material/Stop';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import SearchIcon from '@mui/icons-material/Search';
import HomeIcon from '@mui/icons-material/Home';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts';

function AnalysisPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const inputType = location.state?.inputType || 'microphone';
  
  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [recordedAudio, setRecordedAudio] = useState(null);
  const [micTestResult, setMicTestResult] = useState(null);
  const [audioDevices, setAudioDevices] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState('');
  const [recordingDuration, setRecordingDuration] = useState(0);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioRef = useRef(null);
  const recordingTimerRef = useRef(null);

  // 오디오 장치 목록 가져오기
  const getAudioDevices = useCallback(async () => {
    try {
      console.log('오디오 장치 목록 조회 중...');
      
      // 먼저 마이크 권한을 요청해야 장치 목록을 가져올 수 있음
      await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioInputDevices = devices.filter(device => device.kind === 'audioinput');
      
      console.log('사용 가능한 오디오 입력 장치:', audioInputDevices);
      
      setAudioDevices(audioInputDevices);
      
      // 기본 장치 설정
      if (audioInputDevices.length > 0 && !selectedDeviceId) {
        setSelectedDeviceId(audioInputDevices[0].deviceId);
      }
      
      return audioInputDevices;
    } catch (err) {
      console.error('오디오 장치 조회 오류:', err);
      setError('오디오 장치를 조회할 수 없습니다: ' + err.message);
      return [];
    }
  }, [selectedDeviceId]);

  // 컴포넌트 마운트 시 장치 목록 가져오기
  useEffect(() => {
    if (inputType === 'microphone') {
      getAudioDevices();
    }
  }, [inputType, getAudioDevices]);

  // 마이크 녹음 기능
  const startRecording = async () => {
    try {
      console.log('녹음 시작 시도...');
      
      // 마이크 권한 요청 (선택된 장치 사용)
      const audioConstraints = {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 48000,  // 더 높은 샘플링 레이트
        sampleSize: 16,     // 16비트 샘플 크기
        channelCount: 1     // 모노 채널
      };
      
      // 특정 장치가 선택된 경우 해당 장치 사용
      if (selectedDeviceId) {
        audioConstraints.deviceId = { exact: selectedDeviceId };
        console.log('선택된 마이크 장치 ID:', selectedDeviceId);
      }
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: audioConstraints
      });
      
      console.log('마이크 스트림 획득 성공:', stream);
      console.log('오디오 트랙 수:', stream.getAudioTracks().length);
      
      // 고품질 MediaRecorder 옵션 설정 (WAV 우선으로 변경)
      const options = { 
        mimeType: 'audio/wav',  // WAV 형식 우선 사용
        audioBitsPerSecond: 128000  // 128kbps 비트레이트
      };
      
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options.mimeType = 'audio/webm;codecs=opus';
        options.audioBitsPerSecond = 128000;
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
          options.mimeType = 'audio/webm';
          options.audioBitsPerSecond = 128000;
          if (!MediaRecorder.isTypeSupported(options.mimeType)) {
            options.mimeType = 'audio/mp4';
            options.audioBitsPerSecond = 128000;
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
              options.mimeType = 'audio/ogg';
              delete options.audioBitsPerSecond;
            }
          }
        }
      }
      
      console.log('사용할 MIME 타입:', options.mimeType);
      
      mediaRecorderRef.current = new MediaRecorder(stream, options);
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        console.log('데이터 수신:', event.data.size, 'bytes');
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = () => {
        console.log('녹음 중지, 총 청크 수:', audioChunksRef.current.length);
        
        if (audioChunksRef.current.length === 0) {
          console.error('녹음된 데이터가 없습니다!');
          setError('녹음된 데이터가 없습니다. 마이크를 확인하고 다시 시도해주세요.');
          return;
        }
        
        const audioBlob = new Blob(audioChunksRef.current, { type: options.mimeType });
        console.log('생성된 오디오 Blob 크기:', audioBlob.size, 'bytes');
        
        if (audioBlob.size === 0) {
          console.error('빈 오디오 파일이 생성되었습니다!');
          setError('빈 오디오 파일이 생성되었습니다. 마이크를 확인하고 다시 시도해주세요.');
          return;
        }
        
        const audioUrl = URL.createObjectURL(audioBlob);
        console.log('생성된 오디오 URL:', audioUrl);
        
        if (audioRef.current) {
          audioRef.current.src = audioUrl;
          audioRef.current.load(); // 오디오 요소 새로고침
          console.log('오디오 URL 설정 완료');
        }
        
        setRecordedAudio(audioBlob);
        
        // 스트림 정리
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        setError('녹음 중 오류가 발생했습니다.');
      };
      
      // 녹음 시작 (50ms 간격으로 데이터 수집 - 더 자주)
      mediaRecorderRef.current.start(50);
      setIsRecording(true);
      setError(null);
      setRecordingDuration(0);
      
      console.log('녹음 시작됨');
      
      // 녹음 시간 타이머 시작
      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration(prev => {
          const newDuration = prev + 1;
          if (newDuration >= 30) {
            console.log('30초 경과로 자동 중지');
            stopRecording();
          }
          return newDuration;
        });
      }, 1000);
      
    } catch (err) {
      console.error('녹음 시작 오류:', err);
      if (err.name === 'NotAllowedError') {
        setError('마이크 접근 권한이 거부되었습니다. 브라우저 설정에서 마이크 권한을 허용해주세요.');
      } else if (err.name === 'NotFoundError') {
        setError('마이크를 찾을 수 없습니다. 마이크가 연결되어 있는지 확인해주세요.');
      } else {
        setError('마이크 접근 중 오류가 발생했습니다: ' + err.message);
      }
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      console.log('녹음 중지 요청...');
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // 타이머 정리
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
    }
  };

  // 마이크 테스트 기능
  const testMicrophone = async () => {
    try {
      console.log('마이크 테스트 시작...');
      
      const audioConstraints = {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 48000,
        sampleSize: 16,
        channelCount: 1
      };
      
      if (selectedDeviceId) {
        audioConstraints.deviceId = { exact: selectedDeviceId };
        console.log('테스트할 마이크 장치 ID:', selectedDeviceId);
      }
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: audioConstraints 
      });
      
      // 오디오 컨텍스트 생성하여 마이크 레벨 확인
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const microphone = audioContext.createMediaStreamSource(stream);
      
      microphone.connect(analyser);
      analyser.fftSize = 256;
      
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      let maxLevel = 0;
      let testDuration = 0;
      
      const checkLevel = () => {
        analyser.getByteFrequencyData(dataArray);
        const currentLevel = Math.max(...dataArray);
        maxLevel = Math.max(maxLevel, currentLevel);
        testDuration += 100;
        
        if (testDuration < 3000) { // 3초간 테스트
          setTimeout(checkLevel, 100);
        } else {
          // 테스트 완료
          stream.getTracks().forEach(track => track.stop());
          audioContext.close();
          
          const result = {
            success: true,
            maxLevel: maxLevel,
            message: maxLevel > 0 ? 
              `마이크가 정상 작동합니다! (레벨: ${maxLevel})` : 
              '마이크가 감지되지 않습니다. 마이크를 확인해주세요.'
          };
          
          setMicTestResult(result);
          console.log('마이크 테스트 결과:', result);
        }
      };
      
      checkLevel();
      
    } catch (err) {
      console.error('마이크 테스트 오류:', err);
      setMicTestResult({
        success: false,
        message: '마이크 테스트 실패: ' + err.message
      });
    }
  };

  // 파일 업로드 기능
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setRecordedAudio(file);
    }
  };

  // Spotify 검색 기능
  const searchSpotify = async () => {
    if (!searchQuery.trim()) return;
    
    try {
      const response = await fetch(`/api/v1/spotify/search?q=${encodeURIComponent(searchQuery)}&limit=10`);
      const data = await response.json();
      setSearchResults(data.tracks || []);
    } catch (err) {
      setError('검색 중 오류가 발생했습니다.');
    }
  };

  const selectTrack = (track) => {
    setSelectedTrack(track);
  };

  // 분석 시작 함수
  const startAnalysis = () => {
    if (recordedAudio) {
      analyzeAudio(recordedAudio);
    } else if (selectedTrack) {
      analyzeSpotifyTrack(selectedTrack.id);
    }
  };

  // 오디오 분석
  const analyzeAudio = async (audioFile) => {
    setIsAnalyzing(true);
    setError(null);
    
    try {
      const formData = new FormData();
      
      // 파일명이 없는 경우 기본 파일명 설정
      if (audioFile instanceof Blob && !audioFile.name) {
        // Blob의 MIME 타입에 따라 적절한 파일명 설정
        let fileName = 'recording.wav';
        if (audioFile.type.includes('webm')) {
          fileName = 'recording.webm';
        } else if (audioFile.type.includes('mp4')) {
          fileName = 'recording.mp4';
        } else if (audioFile.type.includes('ogg')) {
          fileName = 'recording.ogg';
        }
        formData.append('file', audioFile, fileName);
      } else {
        formData.append('file', audioFile);
      }
      
      formData.append('analysis_type', 'feature_extraction');
      formData.append('input_type', inputType);
      
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'web-production-7c90a.up.railway.app'}/api/v1/audio/analyze`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setAnalysisResult(data);
      } else {
        setError(data.detail || '분석 중 오류가 발생했습니다.');
      }
    } catch (err) {
      setError('분석 중 오류가 발생했습니다.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Spotify 트랙 분석
  const analyzeSpotifyTrack = async (trackId) => {
    setIsAnalyzing(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('track_id', trackId);
      
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/v1/audio/analyze/spotify`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setAnalysisResult(data);
      } else {
        setError(data.detail || '분석 중 오류가 발생했습니다.');
      }
    } catch (err) {
      setError('분석 중 오류가 발생했습니다.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Audio Features를 레이더 차트 데이터로 변환
  const getRadarData = (features) => {
    if (!features) return [];
    
    return [
      { feature: 'Danceability', value: (features.danceability || 0) * 100 },
      { feature: 'Energy', value: (features.energy || 0) * 100 },
      { feature: 'Valence', value: (features.valence || 0) * 100 },
      { feature: 'Acousticness', value: (features.acousticness || 0) * 100 },
      { feature: 'Instrumentalness', value: (features.instrumentalness || 0) * 100 },
      { feature: 'Speechiness', value: (features.speechiness || 0) * 100 },
      { feature: 'Liveness', value: (features.liveness || 0) * 100 },
    ];
  };

  return (
    <Box>
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        mb: { xs: 2, sm: 3 },
        flexDirection: { xs: 'column', sm: 'row' },
        gap: { xs: 1, sm: 0 }
      }}>
        <Typography 
          variant="h4" 
          component="h1" 
          sx={{ 
            flexGrow: 1,
            fontSize: { xs: '1.8rem', sm: '2.125rem' },
            textAlign: { xs: 'center', sm: 'left' }
          }}
        >
          음악 분석
        </Typography>
        <Button
          variant="outlined"
          startIcon={<HomeIcon />}
          onClick={() => navigate('/')}
          sx={{ 
            ml: { xs: 0, sm: 2 },
            width: { xs: '100%', sm: 'auto' },
            minWidth: { xs: 'auto', sm: '120px' }
          }}
        >
          홈으로
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={{ xs: 2, sm: 3 }}>
        {/* 입력 섹션 */}
        <Grid item xs={12} md={6}>
          <Card elevation={3}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography 
                variant="h6" 
                gutterBottom
                sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}
              >
                {inputType === 'microphone' && '🎤 마이크 녹음'}
                {inputType === 'file' && '📁 파일 업로드'}
                {inputType === 'spotify' && '🔍 Spotify 검색'}
              </Typography>

              {inputType === 'microphone' && (
                <Box>
                  {/* 마이크 장치 선택 */}
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>마이크 선택</InputLabel>
                    <Select
                      value={selectedDeviceId}
                      onChange={(e) => setSelectedDeviceId(e.target.value)}
                      label="마이크 선택"
                    >
                      {audioDevices.map((device) => (
                        <MenuItem key={device.deviceId} value={device.deviceId}>
                          {device.label || `마이크 ${device.deviceId.slice(0, 8)}`}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  {/* 음질 정보 */}
                  <Paper elevation={1} sx={{ p: 2, mb: 2, backgroundColor: '#f5f5f5' }}>
                    <Typography variant="body2" color="text.secondary">
                      🎵 <strong>고품질 녹음 설정</strong>
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                      • 샘플링 레이트: 48kHz (CD 품질)
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      • 비트레이트: 128kbps (고품질)
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      • 코덱: Opus (최적화된 압축)
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      • 노이즈 제거 및 에코 캔슬레이션 활성화
                    </Typography>
                  </Paper>
                  
                  {/* 현재 선택된 마이크 정보 */}
                  {selectedDeviceId && (
                    <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        현재 선택된 마이크:
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {audioDevices.find(d => d.deviceId === selectedDeviceId)?.label || 
                         `마이크 ${selectedDeviceId.slice(0, 8)}`}
                      </Typography>
                    </Paper>
                  )}
                  
                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ 
                      display: 'flex', 
                      flexDirection: { xs: 'column', sm: 'row' },
                      gap: { xs: 1, sm: 2 },
                      mb: { xs: 2, sm: 0 }
                    }}>
                      <Button
                        variant="outlined"
                        onClick={testMicrophone}
                        sx={{ 
                          width: { xs: '100%', sm: 'auto' },
                          minWidth: { xs: 'auto', sm: '120px' }
                        }}
                      >
                        마이크 테스트
                      </Button>
                      <Button
                        variant="outlined"
                        onClick={getAudioDevices}
                        sx={{ 
                          width: { xs: '100%', sm: 'auto' },
                          minWidth: { xs: 'auto', sm: '120px' }
                        }}
                      >
                        장치 새로고침
                      </Button>
                    </Box>
                    <Button
                      variant="contained"
                      startIcon={isRecording ? <StopIcon /> : <MicIcon />}
                      onClick={isRecording ? stopRecording : startRecording}
                      disabled={isAnalyzing}
                      color={isRecording ? 'error' : 'primary'}
                      fullWidth
                      sx={{ 
                        py: { xs: 1.5, sm: 1 },
                        fontSize: { xs: '1rem', sm: '0.875rem' }
                      }}
                    >
                      {isRecording ? '녹음 중지' : '녹음 시작'}
                    </Button>
                  </Box>
                  
                  {micTestResult && (
                    <Alert 
                      severity={micTestResult.success ? 'success' : 'error'} 
                      sx={{ mb: 2 }}
                    >
                      {micTestResult.message}
                    </Alert>
                  )}
                  
                  {/* 녹음 가이드 */}
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="body2" gutterBottom>
                      <strong>📝 녹음 가이드:</strong>
                    </Typography>
                    <Typography variant="body2" component="div">
                      • <strong>최소 5초 이상</strong> 녹음하세요 (더 정확한 분석을 위해 10-15초 권장)
                    </Typography>
                    <Typography variant="body2" component="div">
                      • <strong>최대 30초</strong>까지 녹음 가능
                    </Typography>
                    <Typography variant="body2" component="div">
                      • 음악의 <strong>메인 멜로디</strong>나 <strong>코러스 부분</strong>을 녹음하세요
                    </Typography>
                    <Typography variant="body2" component="div">
                      • 주변 소음이 적은 환경에서 녹음하세요
                    </Typography>
                  </Alert>
                  
                  {isRecording && (
                    <Alert severity="warning" sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Box sx={{ 
                            width: 8, 
                            height: 8, 
                            backgroundColor: 'red', 
                            borderRadius: '50%', 
                            mr: 1,
                            animation: 'pulse 1s infinite'
                          }} />
                          <Typography variant="body2">
                            녹음 중... - 소리를 내어보세요!
                          </Typography>
                        </Box>
                        <Typography variant="h6" color="primary" sx={{ fontWeight: 'bold' }}>
                          {recordingDuration}초
                        </Typography>
                      </Box>
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          {recordingDuration < 5 ? 
                            `최소 5초까지 ${5 - recordingDuration}초 더 녹음하세요` :
                            recordingDuration < 10 ?
                            '좋습니다! 더 정확한 분석을 위해 10-15초까지 녹음하세요' :
                            '완벽합니다! 언제든 중지할 수 있습니다'
                          }
                        </Typography>
                      </Box>
                    </Alert>
                  )}
                  
                  {recordedAudio && (
                    <Box sx={{ mt: 2 }}>
                      <Typography 
                        variant="body2" 
                        color="text.secondary" 
                        sx={{ 
                          mb: 1,
                          fontSize: { xs: '0.8rem', sm: '0.875rem' }
                        }}
                      >
                        녹음 완료! 파일 크기: {(recordedAudio.size / 1024).toFixed(1)} KB
                      </Typography>
                      <Box sx={{ 
                        display: 'flex', 
                        flexDirection: { xs: 'column', sm: 'row' },
                        gap: { xs: 1, sm: 2 }
                      }}>
                        <Button
                          variant="outlined"
                          startIcon={<PlayArrowIcon />}
                          onClick={() => {
                            console.log('재생 버튼 클릭됨');
                            if (audioRef.current) {
                              console.log('오디오 요소:', audioRef.current);
                              console.log('오디오 src:', audioRef.current.src);
                              console.log('오디오 readyState:', audioRef.current.readyState);
                              
                              audioRef.current.play().catch(err => {
                                console.error('재생 오류:', err);
                                setError('오디오 재생 중 오류가 발생했습니다: ' + err.message);
                              });
                            } else {
                              console.error('오디오 요소가 없습니다!');
                              setError('오디오 요소를 찾을 수 없습니다.');
                            }
                          }}
                          sx={{ 
                            width: { xs: '100%', sm: 'auto' },
                            minWidth: { xs: 'auto', sm: '120px' }
                          }}
                        >
                          녹음 재생
                        </Button>
                        <Button
                          variant="contained"
                          onClick={startAnalysis}
                          disabled={isAnalyzing}
                          sx={{ 
                            backgroundColor: '#1db954',
                            width: { xs: '100%', sm: 'auto' },
                            minWidth: { xs: 'auto', sm: '120px' }
                          }}
                        >
                          분석 시작
                        </Button>
                      </Box>
                    </Box>
                  )}
                  
                  <audio 
                    ref={audioRef} 
                    controls 
                    style={{ display: recordedAudio ? 'block' : 'none', width: '100%', marginTop: '10px' }}
                    onLoadedData={() => console.log('오디오 데이터 로드됨')}
                    onCanPlay={() => console.log('오디오 재생 가능')}
                    onError={(e) => console.error('오디오 로드 오류:', e)}
                    onLoadStart={() => console.log('오디오 로드 시작')}
                  />
                </Box>
              )}

              {inputType === 'file' && (
                <Box>
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={handleFileUpload}
                    disabled={isAnalyzing}
                    style={{ display: 'none' }}
                    id="file-upload"
                  />
                  <label htmlFor="file-upload">
                    <Button
                      variant="contained"
                      component="span"
                      startIcon={<UploadFileIcon />}
                      disabled={isAnalyzing}
                      sx={{ mb: 2 }}
                    >
                      파일 선택
                    </Button>
                  </label>
                  
                  {recordedAudio && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        선택된 파일: {recordedAudio.name || '녹음 파일'}
                      </Typography>
                      <Button
                        variant="contained"
                        onClick={startAnalysis}
                        disabled={isAnalyzing}
                        sx={{ backgroundColor: '#1db954' }}
                      >
                        분석 시작
                      </Button>
                    </Box>
                  )}
                </Box>
              )}

              {inputType === 'spotify' && (
                <Box>
                  <TextField
                    fullWidth
                    label="곡명, 아티스트, 앨범명으로 검색"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && searchSpotify()}
                    sx={{ mb: 2 }}
                  />
                  <Button
                    variant="contained"
                    startIcon={<SearchIcon />}
                    onClick={searchSpotify}
                    disabled={isAnalyzing || !searchQuery.trim()}
                  >
                    검색
                  </Button>
                  
                  {searchResults.length > 0 && (
                    <List sx={{ mt: 2, maxHeight: 300, overflow: 'auto' }}>
                      {searchResults.map((track) => (
                        <ListItem
                          key={track.id}
                          button
                          onClick={() => selectTrack(track)}
                          selected={selectedTrack?.id === track.id}
                        >
                          <ListItemAvatar>
                            <Avatar
                              src={track.album.images?.[0]?.url}
                              alt={track.name}
                            />
                          </ListItemAvatar>
                          <ListItemText
                            primary={track.name}
                            secondary={`${track.artists.join(', ')} - ${track.album.name}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  )}
                  
                  {selectedTrack && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        선택된 곡: {selectedTrack.name} - {selectedTrack.artists.join(', ')}
                      </Typography>
                      <Button
                        variant="contained"
                        onClick={startAnalysis}
                        disabled={isAnalyzing}
                        sx={{ backgroundColor: '#1db954' }}
                      >
                        분석 시작
                      </Button>
                    </Box>
                  )}
                </Box>
              )}

              {isAnalyzing && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    분석 중...
                  </Typography>
                  <LinearProgress />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* 분석 결과 섹션 */}
        <Grid item xs={12} md={6}>
          {analysisResult && (
            <Card elevation={3}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  분석 결과
                </Typography>

                {analysisResult.result && (
                  <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      🎵 곡 정보
                    </Typography>
                    <Typography variant="body1">
                      <strong>곡명:</strong> {analysisResult.result.track_name}
                    </Typography>
                    <Typography variant="body1">
                      <strong>아티스트:</strong> {analysisResult.result.artist}
                    </Typography>
                    <Typography variant="body1">
                      <strong>앨범:</strong> {analysisResult.result.album}
                    </Typography>
                    {analysisResult.result.confidence && (
                      <Typography variant="body1">
                        <strong>신뢰도:</strong> {(analysisResult.result.confidence * 100).toFixed(1)}%
                      </Typography>
                    )}
                  </Paper>
                )}

                {analysisResult.audio_features && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      📊 Audio Features
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <RadarChart data={getRadarData(analysisResult.audio_features)}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="feature" />
                        <PolarRadiusAxis domain={[0, 100]} />
                        <Radar
                          name="Features"
                          dataKey="value"
                          stroke="#1db954"
                          fill="#1db954"
                          fillOpacity={0.3}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </Box>
                )}

                {analysisResult.analysis_reason && (
                  <Paper elevation={1} sx={{ p: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>
                      🤖 AI 분석
                    </Typography>
                    <Box sx={{ 
                      backgroundColor: '#f8f9fa', 
                      borderRadius: 2, 
                      p: 2,
                      border: '1px solid #e9ecef'
                    }}>
                      {analysisResult.analysis_reason.split('\n').map((line, index) => {
                        if (line.trim()) {
                          // 이모지와 텍스트 분리
                          const emojiMatch = line.match(/^([🎵🎯💡])\s*\*\*(.*?)\*\*:\s*(.*)$/);
                          if (emojiMatch) {
                            const [, emoji, label, content] = emojiMatch;
                            return (
                              <Box key={index} sx={{ 
                                display: 'flex', 
                                alignItems: 'flex-start', 
                                mb: 1,
                                '&:last-child': { mb: 0 }
                              }}>
                                <Typography variant="h6" sx={{ mr: 1, fontSize: '1.2rem' }}>
                                  {emoji}
                                </Typography>
                                <Box>
                                  <Typography variant="subtitle2" sx={{ 
                                    fontWeight: 'bold', 
                                    color: '#1976d2',
                                    mb: 0.5
                                  }}>
                                    {label}
                                  </Typography>
                                  <Typography variant="body2" sx={{ 
                                    color: '#424242',
                                    lineHeight: 1.4
                                  }}>
                                    {content}
                                  </Typography>
                                </Box>
                              </Box>
                            );
                          } else {
                            // 일반 텍스트
                            return (
                              <Typography key={index} variant="body2" sx={{ 
                                mb: 1,
                                color: '#424242',
                                lineHeight: 1.4
                              }}>
                                {line}
                              </Typography>
                            );
                          }
                        }
                        return null;
                      })}
                    </Box>
                  </Paper>
                )}

                <Button
                  variant="contained"
                  fullWidth
                  sx={{ mt: 2 }}
                  onClick={() => navigate('/recommendations', { state: { analysisResult } })}
                >
                  유사곡 추천 받기
                </Button>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}

export default AnalysisPage;




