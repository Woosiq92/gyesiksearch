import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Container, AppBar, Toolbar, Typography, Box, IconButton, Button } from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';
import HomePage from './pages/HomePage';
import AnalysisPage from './pages/AnalysisPage';
import RecommendationsPage from './pages/RecommendationsPage';

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const [spotifyToken, setSpotifyToken] = useState(null);
  const [userInfo, setUserInfo] = useState(null);
  
  // Spotify 로그인 상태 확인
  useEffect(() => {
    const token = localStorage.getItem('spotify_token');
    const user = localStorage.getItem('spotify_user');
    
    if (token) {
      setSpotifyToken(token);
      if (user) {
        setUserInfo(JSON.parse(user));
      }
    }
  }, []);
  
  const handleHomeClick = () => {
    navigate('/');
  };
  
  const handleSpotifyLogin = () => {
    // 백엔드의 Spotify 로그인 엔드포인트로 리다이렉트
    const apiUrl = process.env.REACT_APP_API_URL || 'https://web-production-7d56.up.railway.app';
    window.location.href = `${apiUrl}/api/v1/spotify/login`;
  };
  
  const handleSpotifyLogout = () => {
    localStorage.removeItem('spotify_token');
    localStorage.removeItem('spotify_user');
    setSpotifyToken(null);
    setUserInfo(null);
  };
  
  // Spotify 콜백 처리
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const error = urlParams.get('error');
    
    if (code) {
      // 백엔드로 인증 코드 전송
      const apiUrl = process.env.REACT_APP_API_URL || 'https://web-production-7d56.up.railway.app';
      fetch(`${apiUrl}/api/v1/spotify/callback?code=${code}`)
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            localStorage.setItem('spotify_token', data.token);
            localStorage.setItem('spotify_user', JSON.stringify(data.user));
            setSpotifyToken(data.token);
            setUserInfo(data.user);
            
            // URL에서 코드 제거
            window.history.replaceState({}, document.title, window.location.pathname);
          }
        })
        .catch(error => {
          console.error('Spotify 로그인 오류:', error);
        });
    } else if (error) {
      console.error('Spotify 인증 오류:', error);
    }
  }, []);

  return (
    <Box sx={{ 
      flexGrow: 1,
      '@keyframes pulse': {
        '0%': { opacity: 1 },
        '50%': { opacity: 0.5 },
        '100%': { opacity: 1 }
      }
    }}>
      <AppBar position="static" sx={{ backgroundColor: '#1db954' }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            🎵 DJ계티Match
          </Typography>
          
          {/* Spotify 로그인/로그아웃 버튼 */}
          {spotifyToken ? (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" sx={{ color: 'white' }}>
                {userInfo?.name || 'Spotify 사용자'}
              </Typography>
              <IconButton
                color="inherit"
                onClick={handleSpotifyLogout}
                title="Spotify 로그아웃"
              >
                <LogoutIcon />
              </IconButton>
            </Box>
          ) : (
            <Button
              color="inherit"
              startIcon={<LoginIcon />}
              onClick={handleSpotifyLogin}
              sx={{ color: 'white' }}
            >
              Spotify 로그인
            </Button>
          )}
          
          {location.pathname !== '/' && (
            <IconButton
              color="inherit"
              onClick={handleHomeClick}
              sx={{ ml: 2 }}
              title="홈으로 돌아가기"
            >
              <HomeIcon />
            </IconButton>
          )}
        </Toolbar>
      </AppBar>
      
      <Container 
        maxWidth="lg" 
        sx={{ 
          mt: { xs: 2, sm: 4 }, 
          mb: { xs: 2, sm: 4 },
          px: { xs: 1, sm: 2 }
        }}
      >
        <Routes>
          <Route path="/" element={<HomePage spotifyToken={spotifyToken} />} />
          <Route path="/analysis" element={<AnalysisPage spotifyToken={spotifyToken} />} />
          <Route path="/recommendations" element={<RecommendationsPage spotifyToken={spotifyToken} />} />
        </Routes>
      </Container>
    </Box>
  );
}

export default App;




