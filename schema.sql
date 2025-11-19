-- PRD 준수 데이터베이스 스키마
-- 프롬프트 경진대회 자동 평가 플랫폼 v2.0

-- 대회 테이블
CREATE TABLE IF NOT EXISTS competitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    model TEXT DEFAULT 'gpt-4o',  -- 사용할 LLM 모델
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 참가자 테이블 (실무자)
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    department TEXT,  -- 부서
    position TEXT,    -- 직급
    FOREIGN KEY (competition_id) REFERENCES competitions(id)
);

-- 과제 테이블 (4가지 입력 요소 포함)
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER NOT NULL,
    name TEXT NOT NULL,  -- e.g., "Task A", "Task B", "Task C"
    description TEXT,
    
    -- 1. 요구사항 (Rubric)
    requirements TEXT,  -- 과제 요구사항 및 평가 기준
    
    -- 2. 대상 파일
    input_file_path TEXT,  -- 참가자 프롬프트에 입력될 파일 (PDF/TXT/Excel)
    input_file_type TEXT,  -- 'pdf', 'txt', 'excel', or NULL
    input_file_content TEXT,  -- 파싱된 텍스트 내용
    
    -- 3. 정답 산출물 (Golden Set)
    golden_output TEXT,  -- 정답 결과물
    
    -- 4. 마스터 평가 프롬프트
    master_grading_prompt TEXT,  -- 채점용 마스터 프롬프트
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (competition_id) REFERENCES competitions(id)
);

-- 제출물 테이블
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    assignment_id INTEGER NOT NULL,
    
    -- 참가자가 제출한 프롬프트
    prompt_text TEXT NOT NULL,
    
    -- 3회 실행 결과 (temperature=0.1)
    execution_output_1 TEXT,  -- 1차 실행 결과
    execution_output_2 TEXT,  -- 2차 실행 결과
    execution_output_3 TEXT,  -- 3차 실행 결과
    
    -- 평가 결과 (마스터 평가 프롬프트의 출력, temperature=0)
    grading_result JSON,  -- {"accuracy": 50, "clarity": 30, "consistency": 20, "total": 100, "feedback": {...}}
    
    -- 상태
    status TEXT DEFAULT 'pending',  -- 'pending', 'executing', 'grading', 'completed', 'failed', 'manual_review'
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    graded_at TIMESTAMP,
    
    FOREIGN KEY (competition_id) REFERENCES competitions(id),
    FOREIGN KEY (participant_id) REFERENCES participants(id),
    FOREIGN KEY (assignment_id) REFERENCES assignments(id),
    UNIQUE(participant_id, assignment_id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_participants_competition ON participants(competition_id);
CREATE INDEX IF NOT EXISTS idx_assignments_competition ON assignments(competition_id);
CREATE INDEX IF NOT EXISTS idx_submissions_competition ON submissions(competition_id);
CREATE INDEX IF NOT EXISTS idx_submissions_participant ON submissions(participant_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
