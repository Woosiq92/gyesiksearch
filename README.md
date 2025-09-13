# DJ계티Match - 음악 식별 및 유사곡 추천 시스템

## 프로젝트 개요
사용자가 제공한 오디오 입력을 통해 음악을 식별하고, Spotify API와 ChatGPT를 활용하여 음악의 특성을 분석한 후 유사한 곡을 추천하는 시스템입니다.

## 주요 기능
- **3가지 입력 방식**: 마이크 녹음, 파일 업로드, Spotify 검색
- **오디오 식별**: 곡 식별 또는 특징 추출 모드
- **Spotify API 분석**: 12가지 Audio Features 활용
- **ChatGPT 분석**: 음악적 특성 해석 및 추천 근거 생성
- **유사곡 추천**: 1-10곡 추천 (사용자 선택)

## 기술 스택
- **백엔드**: Python FastAPI, librosa, scikit-learn
- **프론트엔드**: React.js, Material-UI, Web Audio API
- **데이터베이스**: PostgreSQL
- **외부 API**: Spotify Web API, OpenAI API

## 프로젝트 구조
```
musicmatch-project/
├── backend/          # FastAPI 백엔드 서버
├── frontend/         # React 프론트엔드
├── database/         # 데이터베이스 스키마 및 마이그레이션
├── docs/            # 프로젝트 문서
├── tests/           # 테스트 파일
└── README.md        # 프로젝트 설명
```

## 설치 및 실행

### 백엔드 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 프론트엔드 실행
```bash
cd frontend
npm install
npm start
```

## API 문서
백엔드 서버 실행 후 `http://localhost:8000/docs`에서 Swagger UI를 확인할 수 있습니다.

## 라이선스
MIT License




