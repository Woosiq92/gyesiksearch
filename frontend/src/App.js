import React from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Container, AppBar, Toolbar, Typography, Box, IconButton } from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import HomePage from './pages/HomePage';
import AnalysisPage from './pages/AnalysisPage';
import RecommendationsPage from './pages/RecommendationsPage';

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  
  const handleHomeClick = () => {
    navigate('/');
  };

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
          <Route path="/" element={<HomePage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
        </Routes>
      </Container>
    </Box>
  );
}

export default App;




