-- 데이터베이스 초기화 스크립트
-- PostgreSQL에서 실행하세요

-- 데이터베이스 생성
CREATE DATABASE musicmatch;

-- 사용자 생성 (선택사항)
-- CREATE USER musicmatch_user WITH PASSWORD 'your_password';
-- GRANT ALL PRIVILEGES ON DATABASE musicmatch TO musicmatch_user;

-- 테이블 생성
\c musicmatch;

-- 분석 세션 테이블
CREATE TABLE analysis_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    input_type VARCHAR(20) NOT NULL CHECK (input_type IN ('microphone', 'file', 'spotify')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- 추천 결과 테이블
CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    spotify_track_id VARCHAR(22) NOT NULL,
    track_name VARCHAR(255) NOT NULL,
    artist_name VARCHAR(255) NOT NULL,
    album_name VARCHAR(255) NOT NULL,
    similarity_score DECIMAL(5,2) NOT NULL,
    audio_features JSONB,
    recommendation_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id) ON DELETE CASCADE
);

-- Audio Features 테이블
CREATE TABLE audio_features (
    spotify_track_id VARCHAR(22) PRIMARY KEY,
    danceability DECIMAL(3,2),
    energy DECIMAL(3,2),
    valence DECIMAL(3,2),
    tempo DECIMAL(6,2),
    key_value INTEGER,
    mode_value INTEGER,
    loudness DECIMAL(6,2),
    acousticness DECIMAL(3,2),
    instrumentalness DECIMAL(3,2),
    speechiness DECIMAL(3,2),
    liveness DECIMAL(3,2),
    duration_ms INTEGER,
    time_signature INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_analysis_sessions_created_at ON analysis_sessions(created_at);
CREATE INDEX idx_recommendations_session_id ON recommendations(session_id);
CREATE INDEX idx_recommendations_created_at ON recommendations(created_at);
CREATE INDEX idx_audio_features_updated_at ON audio_features(updated_at);

-- 만료된 세션 정리를 위한 함수
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM analysis_sessions 
    WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- 샘플 데이터 삽입 (선택사항)
INSERT INTO analysis_sessions (session_id, input_type, expires_at) 
VALUES ('sample-session-1', 'file', CURRENT_TIMESTAMP + INTERVAL '30 days');

-- 완료 메시지
SELECT 'Database setup completed successfully!' as message;




