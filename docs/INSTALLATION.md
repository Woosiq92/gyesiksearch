# 설치 및 실행 가이드

## 1. 사전 요구사항

### 필수 소프트웨어
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Git

### API 키 준비
- Spotify Developer Account에서 Client ID와 Client Secret 발급
- OpenAI API Key 발급

## 2. 프로젝트 설정

### 2.1 저장소 클론
```bash
git clone <repository-url>
cd musicmatch-project
```

### 2.2 환경 변수 설정
```bash
# 환경 변수 파일 복사
cp env.example .env

# .env 파일 편집하여 실제 값 입력
# - SPOTIFY_CLIENT_ID
# - SPOTIFY_CLIENT_SECRET  
# - OPENAI_API_KEY
# - DATABASE_URL
```

## 3. 백엔드 설정

### 3.1 가상환경 생성 및 활성화
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3.2 의존성 설치
```bash
pip install -r requirements.txt
```

### 3.3 데이터베이스 설정
```bash
# PostgreSQL에서 데이터베이스 생성
psql -U postgres
CREATE DATABASE musicmatch;
\q

# 데이터베이스 초기화
psql -U postgres -d musicmatch -f ../database/init.sql
```

### 3.4 백엔드 실행
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 4. 프론트엔드 설정

### 4.1 의존성 설치
```bash
cd frontend
npm install
```

### 4.2 프론트엔드 실행
```bash
npm start
```

## 5. Docker를 사용한 실행 (선택사항)

### 5.1 Docker Compose 실행
```bash
# 데이터베이스만 실행
docker-compose up postgres redis

# 또는 모든 서비스 실행 (백엔드/프론트엔드는 별도 실행)
docker-compose up -d
```

## 6. 접속 및 테스트

### 6.1 웹 애플리케이션
- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000
- API 문서: http://localhost:8000/docs

### 6.2 기능 테스트
1. 홈페이지에서 분석 방법 선택
2. 마이크 녹음, 파일 업로드, 또는 Spotify 검색
3. 분석 결과 확인
4. 유사곡 추천 받기

## 7. 문제 해결

### 7.1 일반적인 문제
- **포트 충돌**: 다른 포트 사용 (예: 8001, 3001)
- **API 키 오류**: .env 파일의 API 키 확인
- **데이터베이스 연결 오류**: PostgreSQL 서비스 실행 확인

### 7.2 로그 확인
```bash
# 백엔드 로그
tail -f backend/logs/app.log

# 프론트엔드 로그
npm start
```

## 8. 개발 환경 설정

### 8.1 코드 포맷팅
```bash
# 백엔드
black backend/
flake8 backend/

# 프론트엔드
npm run format
```

### 8.2 테스트 실행
```bash
# 백엔드 테스트
cd backend
pytest

# 프론트엔드 테스트
cd frontend
npm test
```

## 9. 배포

### 9.1 프로덕션 빌드
```bash
# 프론트엔드 빌드
cd frontend
npm run build

# 백엔드 배포 준비
cd backend
pip install -r requirements.txt
```

### 9.2 환경 변수 설정
- 프로덕션 환경에 맞게 .env 파일 수정
- SECRET_KEY 변경
- 데이터베이스 URL 업데이트

## 10. 추가 설정

### 10.1 SSL 인증서 (HTTPS)
- Let's Encrypt 사용
- Nginx 리버스 프록시 설정

### 10.2 모니터링
- 로그 수집: ELK Stack 또는 Fluentd
- 메트릭 수집: Prometheus + Grafana
- 에러 추적: Sentry

## 11. API 사용법

### 11.1 오디오 분석
```bash
curl -X POST "http://localhost:8000/api/v1/audio/analyze" \
  -F "file=@audio.mp3" \
  -F "analysis_type=feature_extraction" \
  -F "input_type=file"
```

### 11.2 유사곡 추천
```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/similar" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "uuid", "num_recommendations": 10}'
```

## 12. 성능 최적화

### 12.1 캐싱
- Redis를 사용한 API 응답 캐싱
- Audio Features 캐싱

### 12.2 데이터베이스 최적화
- 인덱스 추가
- 쿼리 최적화
- 연결 풀 설정

### 12.3 파일 처리 최적화
- 비동기 파일 처리
- 청크 단위 업로드
- CDN 사용




