# DJ계티Match 배포 가이드

## 🚀 Railway 배포 (추천)

### 1. Railway 계정 생성
- [Railway.app](https://railway.app) 방문
- GitHub 계정으로 로그인

### 2. 프로젝트 배포
1. "New Project" 클릭
2. "Deploy from GitHub repo" 선택
3. `musicmatch-project` 저장소 선택
4. 자동 배포 시작

### 3. 환경 변수 설정
Railway 대시보드에서 다음 환경 변수 추가:
```
SPOTIFY_CLIENT_ID=1f3de70d040c4c8bba3165f559e90be7
SPOTIFY_CLIENT_SECRET=818a7a8355504b35bf7212ff01af013b
SPOTIFY_REDIRECT_URI=https://your-app-name.up.railway.app/callback
OPENAI_API_KEY=your_openai_api_key
```

### 4. 프론트엔드 배포
- Railway에서 별도 서비스로 React 앱 배포
- 또는 Netlify/Vercel 사용

## 🌐 Render 배포

### 1. Render 계정 생성
- [Render.com](https://render.com) 방문
- GitHub 계정으로 로그인

### 2. 백엔드 배포
1. "New Web Service" 클릭
2. GitHub 저장소 연결
3. 설정:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 3. 프론트엔드 배포
1. "New Static Site" 클릭
2. 빌드 설정:
   - Build Command: `npm run build`
   - Publish Directory: `build`

## 🔧 배포 전 체크리스트

- [ ] `.env` 파일에 실제 API 키 설정
- [ ] `requirements.txt` 최신화
- [ ] `Procfile` 생성
- [ ] `Dockerfile` 생성 (선택사항)
- [ ] CORS 설정 업데이트
- [ ] 데이터베이스 설정 (필요시)

## 📱 모바일 앱 배포 (선택사항)

### React Native
- Expo 사용하여 모바일 앱 빌드
- Google Play Store / App Store 배포

### PWA (Progressive Web App)
- Service Worker 추가
- 오프라인 기능 구현
- 앱 스토어 배포 가능