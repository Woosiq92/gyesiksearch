import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Paper,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Alert
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import HomeIcon from '@mui/icons-material/Home';

function RecommendationsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const analysisResult = location.state?.analysisResult;
  
  const [recommendations, setRecommendations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [numRecommendations] = useState(5); // 5개 고정

  useEffect(() => {
    if (analysisResult) {
      getRecommendations();
    }
  }, [analysisResult, getRecommendations]);

  const getRecommendations = useCallback(async () => {
    if (!analysisResult) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'https://web-production-7c90a.up.railway.app'}/api/v1/recommendations/similar`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: analysisResult.session_id,
          num_recommendations: numRecommendations
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setRecommendations(data.recommendations || []);
      } else {
        setError(data.detail || '추천 생성 중 오류가 발생했습니다.');
      }
    } catch (err) {
      setError('추천 생성 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, [analysisResult, numRecommendations]);

  const handlePlayPreview = (url) => {
    if (url) {
      const audio = new Audio(url);
      audio.play();
    }
  };

  const handleOpenSpotify = (url) => {
    if (url) {
      window.open(url, '_blank');
    }
  };

  if (!analysisResult) {
    return (
      <Box>
        <Alert severity="warning">
          분석 결과가 없습니다. 먼저 음악을 분석해주세요.
        </Alert>
        <Button
          variant="contained"
          onClick={() => navigate('/')}
          sx={{ mt: 2 }}
        >
          홈으로 돌아가기
        </Button>
      </Box>
    );
  }

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
          유사곡 추천
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
        {/* 원본 곡 정보 */}
        <Grid item xs={12} md={4}>
          <Card elevation={3}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography 
                variant="h6" 
                gutterBottom
                sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' } }}
              >
                원본 곡
              </Typography>
              
              {analysisResult.result && (
                <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
                  <Typography variant="subtitle1">
                    {analysisResult.result.track_name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {analysisResult.result.artist}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {analysisResult.result.album}
                  </Typography>
                </Paper>
              )}

              {analysisResult.audio_features && (
                <Box>
                  <Typography variant="subtitle1" gutterBottom>
                    주요 특징
                  </Typography>
                  
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      Danceability: {(analysisResult.audio_features.danceability * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                  
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      Energy: {(analysisResult.audio_features.energy * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                  
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      Valence: {(analysisResult.audio_features.valence * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                  
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      Tempo: {analysisResult.audio_features.tempo?.toFixed(0)} BPM
                    </Typography>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* 추천 설정 */}
        <Grid item xs={12} md={8}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                추천 설정
              </Typography>
              
              <Box sx={{ mb: 3, p: 2, backgroundColor: '#f8f9fa', borderRadius: 2 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  🎵 추천 곡 개수: <strong>5개</strong> (고정)
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  AI가 분석한 음악 특징을 바탕으로 유사한 곡을 추천합니다.
                </Typography>
              </Box>
              
              <Button
                variant="contained"
                onClick={getRecommendations}
                disabled={isLoading}
                sx={{ 
                  backgroundColor: '#1db954',
                  '&:hover': {
                    backgroundColor: '#1ed760',
                  },
                  minWidth: '150px',
                  py: 1.5
                }}
              >
                {isLoading ? '추천 생성 중...' : '🔄 재추천 받기'}
              </Button>
              
              {isLoading && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  새로운 추천 곡을 찾고 있습니다...
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* 추천 결과 */}
        <Grid item xs={12}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                추천 곡 ({recommendations.length}개)
              </Typography>
              
              {recommendations.length > 0 ? (
                <List>
                  {recommendations.map((track, index) => (
                    <ListItem key={track.spotify_id} divider>
                      <ListItemAvatar>
                        <Avatar
                          sx={{ 
                            backgroundColor: '#1db954',
                            color: 'white',
                            fontWeight: 'bold',
                            width: 40,
                            height: 40
                          }}
                        >
                          {index + 1}
                        </Avatar>
                      </ListItemAvatar>
                      
                      <ListItemText
                        primary={
                          <React.Fragment>
                            <Typography variant="subtitle1" component="div">
                              {track.track_name}
                            </Typography>
                            <Chip
                              label={`${track.similarity_score.toFixed(1)}% 유사도`}
                              size="small"
                              color="primary"
                              sx={{ mt: 0.5 }}
                            />
                          </React.Fragment>
                        }
                        secondary={
                          <React.Fragment>
                            <Typography variant="body2" color="text.secondary" component="div">
                              {track.artist_name} - {track.album_name}
                            </Typography>
                            {track.recommendation_reason && (
                              <Box sx={{ 
                                mt: 1, 
                                p: 1.5, 
                                backgroundColor: '#f8f9fa', 
                                borderRadius: 1,
                                border: '1px solid #e9ecef'
                              }}>
                                <Typography variant="body2" component="div" sx={{ 
                                  color: '#1976d2',
                                  fontWeight: 'medium',
                                  mb: 0.5
                                }}>
                                  💡 추천 이유
                                </Typography>
                                <Typography variant="body2" component="div" sx={{ 
                                  color: '#424242',
                                  lineHeight: 1.4,
                                  fontSize: '0.875rem'
                                }}>
                                  {track.recommendation_reason}
                                </Typography>
                              </Box>
                            )}
                          </React.Fragment>
                        }
                      />
                      
                      <Box sx={{ display: 'flex', gap: 1, flexDirection: { xs: 'column', sm: 'row' } }}>
                        {track.preview_url && (
                          <Button
                            size="small"
                            startIcon={<PlayArrowIcon />}
                            onClick={() => handlePlayPreview(track.preview_url)}
                            variant="outlined"
                            sx={{ minWidth: '100px' }}
                          >
                            미리듣기
                          </Button>
                        )}
                        
                        {track.external_urls?.spotify && (
                          <Button
                            size="small"
                            startIcon={<OpenInNewIcon />}
                            onClick={() => handleOpenSpotify(track.external_urls.spotify)}
                            variant="contained"
                            sx={{ 
                              backgroundColor: '#1db954',
                              '&:hover': { backgroundColor: '#1ed760' },
                              minWidth: '100px'
                            }}
                          >
                            Spotify
                          </Button>
                        )}
                      </Box>
                    </ListItem>
                  ))}
                </List>
              ) : !isLoading ? (
                <Typography variant="body1" color="text.secondary" align="center" sx={{ py: 4 }}>
                  추천 곡이 없습니다. 추천을 생성해보세요.
                </Typography>
              ) : null}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default RecommendationsPage;




