import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Paper,
  Tabs,
  Tab,
  Alert
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import MicIcon from '@mui/icons-material/Mic';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import SearchIcon from '@mui/icons-material/Search';

function HomePage() {
  const navigate = useNavigate();
  const [selectedTab, setSelectedTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setSelectedTab(newValue);
  };

  const handleStartAnalysis = () => {
    navigate('/analysis', { state: { inputType: selectedTab === 0 ? 'microphone' : selectedTab === 1 ? 'file' : 'spotify' } });
  };

  return (
    <Box>
      <Typography 
        variant="h3" 
        component="h1" 
        gutterBottom 
        align="center" 
        sx={{ 
          mb: { xs: 2, sm: 4 },
          fontSize: { xs: '2rem', sm: '3rem' }
        }}
      >
        🎵 MusicMatch
      </Typography>
      
      <Typography 
        variant="h5" 
        component="h2" 
        gutterBottom 
        align="center" 
        sx={{ 
          mb: { xs: 2, sm: 4 }, 
          color: 'text.secondary',
          fontSize: { xs: '1.2rem', sm: '1.5rem' }
        }}
      >
        음악을 분석하고 유사한 곡을 찾아보세요
      </Typography>

      <Grid container spacing={{ xs: 2, sm: 3 }} justifyContent="center">
        <Grid item xs={12} md={8}>
          <Card elevation={3}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography 
                variant="h6" 
                gutterBottom
                sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}
              >
                분석 방법을 선택하세요
              </Typography>
              
              <Tabs
                value={selectedTab}
                onChange={handleTabChange}
                sx={{ mb: 3 }}
                variant={window.innerWidth < 600 ? "scrollable" : "standard"}
                scrollButtons="auto"
                centered={window.innerWidth >= 600}
              >
                <Tab 
                  icon={<MicIcon />} 
                  label="마이크 녹음" 
                  sx={{ minWidth: { xs: 'auto', sm: '120px' } }}
                />
                <Tab 
                  icon={<UploadFileIcon />} 
                  label="파일 업로드" 
                  sx={{ minWidth: { xs: 'auto', sm: '120px' } }}
                />
                <Tab 
                  icon={<SearchIcon />} 
                  label="Spotify 검색" 
                  sx={{ minWidth: { xs: 'auto', sm: '120px' } }}
                />
              </Tabs>

              <Paper elevation={1} sx={{ p: { xs: 2, sm: 3 }, mb: 3 }}>
                {selectedTab === 0 && (
                  <Box>
                    <Typography 
                      variant="h6" 
                      gutterBottom
                      sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}
                    >
                      🎤 마이크 녹음
                    </Typography>
                    <Typography 
                      variant="body1" 
                      color="text.secondary"
                      sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}
                    >
                      마이크를 사용하여 최대 30초간 음악을 녹음하고 분석합니다.
                      실시간 파형을 확인하며 녹음 품질을 모니터링할 수 있습니다.
                    </Typography>
                  </Box>
                )}
                
                {selectedTab === 1 && (
                  <Box>
                    <Typography 
                      variant="h6" 
                      gutterBottom
                      sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}
                    >
                      📁 파일 업로드
                    </Typography>
                    <Typography 
                      variant="body1" 
                      color="text.secondary"
                      sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}
                    >
                      MP3, WAV, FLAC, M4A, AAC 형식의 오디오 파일을 업로드하여 분석합니다.
                      최대 50MB까지 지원합니다.
                    </Typography>
                  </Box>
                )}
                
                {selectedTab === 2 && (
                  <Box>
                    <Typography 
                      variant="h6" 
                      gutterBottom
                      sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}
                    >
                      🔍 Spotify 검색
                    </Typography>
                    <Typography 
                      variant="body1" 
                      color="text.secondary"
                      sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}
                    >
                      Spotify에서 곡을 검색하여 바로 분석할 수 있습니다.
                      곡명, 아티스트, 앨범명으로 검색 가능합니다.
                    </Typography>
                  </Box>
                )}
              </Paper>

              <Button
                variant="contained"
                size="large"
                fullWidth
                onClick={handleStartAnalysis}
                sx={{ 
                  backgroundColor: '#1db954',
                  '&:hover': {
                    backgroundColor: '#1ed760',
                  },
                  py: { xs: 1.5, sm: 2 },
                  fontSize: { xs: '1rem', sm: '1.1rem' }
                }}
              >
                분석 시작하기
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                주요 기능
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  🎵 곡 식별
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  업로드한 오디오가 기존 곡인지 식별합니다.
                </Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  📊 특징 분석
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  12가지 Audio Features를 분석하여 음악적 특성을 파악합니다.
                </Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  🤖 AI 분석
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  ChatGPT를 활용하여 음악의 감정과 분위기를 분석합니다.
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  🎯 유사곡 추천
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  분석 결과를 바탕으로 유사한 곡을 추천합니다.
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Alert severity="info" sx={{ mt: 4 }}>
        <Typography variant="body2">
          <strong>참고:</strong> Spotify API와 OpenAI API 키가 설정되어 있어야 모든 기능을 사용할 수 있습니다.
        </Typography>
      </Alert>
    </Box>
  );
}

export default HomePage;




