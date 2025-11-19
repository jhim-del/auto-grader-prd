"""
PRD 준수 FastAPI 백엔드
프롬프트 경진대회 자동 평가 플랫폼 v2.0
"""

import os
import io
import json
import sqlite3
import zipfile
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

from grading_engine import GradingEngine
from file_parser import FileParser


# 환경변수
DATA_DIR = os.environ.get("DATA_DIR", ".")
DB_PATH = os.path.join(DATA_DIR, "competition_prd.db")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

app = FastAPI(title="Auto-Grader PRD v2.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Pydantic 모델 =====

class Competition(BaseModel):
    name: str
    description: Optional[str] = None
    model: str = "gpt-4o-mini"


class Participant(BaseModel):
    name: str
    email: str
    department: Optional[str] = None
    position: Optional[str] = None


class Assignment(BaseModel):
    name: str
    description: Optional[str] = None
    requirements: Optional[str] = None
    golden_output: Optional[str] = None


# ===== 데이터베이스 =====

def get_db():
    """DB 연결 생성"""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """DB 초기화"""
    conn = get_db()
    
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())
    
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")


# ===== API 엔드포인트 =====

@app.on_event("startup")
async def startup():
    """서버 시작 시 DB 초기화"""
    init_db()


@app.get("/")
async def root():
    """루트 경로 -> /app으로 리다이렉트"""
    return RedirectResponse(url="/app")


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0-PRD"}


# ----- 대회 관리 -----

@app.post("/competitions")
async def create_competition(comp: Competition):
    """대회 생성 (F1.1)"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute(
        "INSERT INTO competitions (name, description, model) VALUES (?, ?, ?)",
        (comp.name, comp.description, comp.model)
    )
    comp_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": comp_id, "message": f"Competition '{comp.name}' created"}


@app.get("/competitions")
async def list_competitions():
    """대회 목록"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM competitions ORDER BY created_at DESC")
    competitions = [dict(row) for row in c.fetchall()]
    conn.close()
    return competitions


@app.get("/competitions/{competition_id}")
async def get_competition(competition_id: int):
    """대회 상세 정보"""
    conn = get_db()
    c = conn.cursor()
    
    # 대회 정보
    c.execute("SELECT * FROM competitions WHERE id = ?", (competition_id,))
    comp = c.fetchone()
    if not comp:
        conn.close()
        raise HTTPException(status_code=404, detail="Competition not found")
    
    result = dict(comp)
    
    # 과제 목록
    c.execute("SELECT * FROM assignments WHERE competition_id = ?", (competition_id,))
    result["assignments"] = [dict(row) for row in c.fetchall()]
    
    # 참가자 목록
    c.execute("SELECT * FROM participants WHERE competition_id = ?", (competition_id,))
    result["participants"] = [dict(row) for row in c.fetchall()]
    
    # 제출물 통계
    c.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN status = 'manual_review' THEN 1 ELSE 0 END) as manual_review
        FROM submissions 
        WHERE competition_id = ?
    """, (competition_id,))
    result["submissions_stats"] = dict(c.fetchone())
    
    conn.close()
    return result


# ----- 참가자 관리 -----

@app.post("/competitions/{competition_id}/participants/upload")
async def upload_participants(competition_id: int, file: UploadFile = File(...)):
    """참가자 CSV 업로드 (F2.1)"""
    conn = get_db()
    c = conn.cursor()
    
    # 대회 존재 확인
    c.execute("SELECT id FROM competitions WHERE id = ?", (competition_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Competition not found")
    
    # CSV 파싱
    content = await file.read()
    csv_text = content.decode('utf-8')
    
    lines = csv_text.strip().split('\n')
    if len(lines) < 2:
        conn.close()
        raise HTTPException(status_code=400, detail="CSV file is empty")
    
    # 헤더 파싱
    header = lines[0].strip().split(',')
    required_cols = ['name', 'email']
    
    for col in required_cols:
        if col not in header:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Missing required column: {col}")
    
    # 참가자 등록
    added = 0
    for line in lines[1:]:
        if not line.strip():
            continue
        
        values = line.strip().split(',')
        if len(values) < len(header):
            continue
        
        row_dict = dict(zip(header, values))
        
        c.execute("""
            INSERT INTO participants (competition_id, name, email, department, position)
            VALUES (?, ?, ?, ?, ?)
        """, (
            competition_id,
            row_dict['name'],
            row_dict['email'],
            row_dict.get('department', ''),
            row_dict.get('position', '')
        ))
        added += 1
    
    conn.commit()
    conn.close()
    
    return {"message": f"{added} participants added successfully"}


@app.get("/competitions/{competition_id}/participants")
async def get_participants(competition_id: int):
    """참가자 목록"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM participants WHERE competition_id = ?", (competition_id,))
    participants = [dict(row) for row in c.fetchall()]
    conn.close()
    return participants


# ----- 과제 관리 -----

@app.post("/competitions/{competition_id}/assignments")
async def create_assignment(competition_id: int, assignment: Assignment):
    """과제 생성 (F1.2)"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO assignments (competition_id, name, description, requirements, golden_output)
        VALUES (?, ?, ?, ?, ?)
    """, (
        competition_id,
        assignment.name,
        assignment.description,
        assignment.requirements,
        assignment.golden_output
    ))
    
    assignment_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": assignment_id, "message": f"Assignment '{assignment.name}' created"}


@app.post("/competitions/{competition_id}/assignments/{assignment_id}/input_file")
async def upload_assignment_input_file(
    competition_id: int,
    assignment_id: int,
    file: UploadFile = File(...)
):
    """과제 대상 파일 업로드 (F1.3)"""
    conn = get_db()
    c = conn.cursor()
    
    # 과제 존재 확인
    c.execute("SELECT id FROM assignments WHERE id = ? AND competition_id = ?", 
              (assignment_id, competition_id))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # 파일 타입 감지
    file_type = FileParser.detect_file_type(file.filename)
    if not file_type:
        conn.close()
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # 파일 파싱
    content = await file.read()
    success, parsed_text = FileParser.parse_file(content, file_type)
    
    if not success:
        conn.close()
        raise HTTPException(status_code=400, detail=f"File parsing failed: {parsed_text}")
    
    # DB 업데이트
    c.execute("""
        UPDATE assignments 
        SET input_file_path = ?, input_file_type = ?, input_file_content = ?
        WHERE id = ?
    """, (file.filename, file_type, parsed_text, assignment_id))
    
    conn.commit()
    conn.close()
    
    return {"message": f"Input file '{file.filename}' uploaded and parsed successfully"}


@app.get("/competitions/{competition_id}/assignments")
async def get_assignments(competition_id: int):
    """과제 목록"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM assignments WHERE competition_id = ?", (competition_id,))
    assignments = [dict(row) for row in c.fetchall()]
    conn.close()
    return assignments


# ----- 제출물 관리 -----

@app.post("/competitions/{competition_id}/submissions/upload")
async def upload_submissions(competition_id: int, file: UploadFile = File(...)):
    """
    제출물 ZIP 업로드 (F2.2, F2.3)
    파일명 규칙: {AssignmentName}-Prompt_{ParticipantID}.txt
    예: TaskA-Prompt_P001.txt
    """
    conn = get_db()
    c = conn.cursor()
    
    # 대회 확인
    c.execute("SELECT id FROM competitions WHERE id = ?", (competition_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Competition not found")
    
    # 과제 및 참가자 정보 가져오기
    c.execute("SELECT * FROM assignments WHERE competition_id = ?", (competition_id,))
    assignments = {row['name']: dict(row) for row in c.fetchall()}
    
    c.execute("SELECT * FROM participants WHERE competition_id = ?", (competition_id,))
    participants = {row['id']: dict(row) for row in c.fetchall()}
    
    # ZIP 파일 읽기
    content = await file.read()
    zip_file = zipfile.ZipFile(io.BytesIO(content))
    
    submissions_added = 0
    skipped = []
    
    for file_name in zip_file.namelist():
        if not file_name.endswith('.txt'):
            continue
        
        # 파일명 파싱: TaskA-Prompt_P001.txt
        base_name = os.path.splitext(file_name)[0]
        
        try:
            parts = base_name.split('_')
            if len(parts) < 2:
                skipped.append(f"{file_name} (invalid format)")
                continue
            
            # Assignment name과 Participant ID 추출
            assignment_part = parts[0].split('-')[0]  # "TaskA-Prompt" -> "TaskA"
            participant_id = int(parts[1].replace('P', ''))  # "P001" -> 1
            
            # 매칭 확인
            if assignment_part not in assignments:
                skipped.append(f"{file_name} (assignment not found: {assignment_part})")
                continue
            
            if participant_id not in participants:
                skipped.append(f"{file_name} (participant not found: {participant_id})")
                continue
            
            # 프롬프트 읽기
            prompt_text = zip_file.read(file_name).decode('utf-8')
            
            # DB 저장
            c.execute("""
                INSERT OR REPLACE INTO submissions 
                (competition_id, participant_id, assignment_id, prompt_text, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (
                competition_id,
                participant_id,
                assignments[assignment_part]['id'],
                prompt_text
            ))
            
            submissions_added += 1
            
        except Exception as e:
            skipped.append(f"{file_name} (error: {str(e)})")
    
    conn.commit()
    conn.close()
    
    result = {"message": f"{submissions_added} submissions uploaded successfully"}
    if skipped:
        result["skipped"] = skipped
    
    return result


@app.get("/competitions/{competition_id}/submissions")
async def get_submissions(competition_id: int):
    """제출물 목록"""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT s.*, p.name as participant_name, a.name as assignment_name
        FROM submissions s
        JOIN participants p ON s.participant_id = p.id
        JOIN assignments a ON s.assignment_id = a.id
        WHERE s.competition_id = ?
        ORDER BY p.name, a.name
    """, (competition_id,))
    
    submissions = [dict(row) for row in c.fetchall()]
    conn.close()
    return submissions


# ----- 자동 채점 -----

async def grade_single_submission(submission_id: int):
    """
    단일 제출물 채점 (백그라운드 작업)
    F3.3, F3.4, F3.5
    """
    conn = get_db()
    c = conn.cursor()
    
    try:
        # 제출물 정보 가져오기
        c.execute("""
            SELECT s.*, a.input_file_content, a.golden_output, a.requirements, a.name as assignment_name,
                   c.model
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN competitions c ON s.competition_id = c.id
            WHERE s.id = ?
        """, (submission_id,))
        
        row = c.fetchone()
        if not row:
            return
        
        sub = dict(row)
        
        # 상태 업데이트: executing
        c.execute("UPDATE submissions SET status = 'executing' WHERE id = ?", (submission_id,))
        conn.commit()
        
        # 채점 엔진 초기화
        engine = GradingEngine(OPENAI_API_KEY, model=sub['model'])
        
        # 채점 실행
        success, grading_result, outputs, error = engine.grade_submission(
            participant_prompt=sub['prompt_text'],
            input_file_content=sub['input_file_content'],
            golden_output=sub['golden_output'],
            requirements=sub['requirements'],
            assignment_name=sub['assignment_name']
        )
        
        if not success:
            # F3.5: 실패 시 manual_review 플래그
            c.execute("""
                UPDATE submissions 
                SET status = 'manual_review', error_message = ?, retry_count = retry_count + 1
                WHERE id = ?
            """, (error, submission_id))
            conn.commit()
            return
        
        # 성공: 결과 저장
        c.execute("""
            UPDATE submissions 
            SET execution_output_1 = ?, execution_output_2 = ?, execution_output_3 = ?,
                grading_result = ?, status = 'completed', graded_at = ?
            WHERE id = ?
        """, (
            outputs[0], outputs[1], outputs[2],
            json.dumps(grading_result, ensure_ascii=False),
            datetime.now().isoformat(),
            submission_id
        ))
        conn.commit()
        
    except Exception as e:
        # 예외 처리
        c.execute("""
            UPDATE submissions 
            SET status = 'failed', error_message = ?
            WHERE id = ?
        """, (str(e), submission_id))
        conn.commit()
    
    finally:
        conn.close()


@app.post("/competitions/{competition_id}/grade")
async def start_grading(competition_id: int, background_tasks: BackgroundTasks):
    """
    자동 채점 시작 (F3.1)
    모든 pending 제출물을 백그라운드에서 채점
    """
    conn = get_db()
    c = conn.cursor()
    
    # pending 제출물 조회
    c.execute("""
        SELECT id FROM submissions 
        WHERE competition_id = ? AND status = 'pending'
    """, (competition_id,))
    
    submission_ids = [row['id'] for row in c.fetchall()]
    conn.close()
    
    if not submission_ids:
        return {"message": "No pending submissions to grade"}
    
    # 백그라운드 작업 추가
    for sub_id in submission_ids:
        background_tasks.add_task(grade_single_submission, sub_id)
    
    return {
        "message": f"Grading started for {len(submission_ids)} submissions",
        "submission_ids": submission_ids
    }


@app.get("/competitions/{competition_id}/grading_progress")
async def get_grading_progress(competition_id: int):
    """채점 진행률 (F3.2)"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'executing' THEN 1 ELSE 0 END) as executing,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN status = 'manual_review' THEN 1 ELSE 0 END) as manual_review
        FROM submissions
        WHERE competition_id = ?
    """, (competition_id,))
    
    stats = dict(c.fetchone())
    conn.close()
    
    if stats['total'] > 0:
        stats['progress_percent'] = round(stats['completed'] / stats['total'] * 100, 1)
    else:
        stats['progress_percent'] = 0
    
    return stats


# ----- 결과 대시보드 -----

@app.get("/competitions/{competition_id}/leaderboard")
async def get_leaderboard(competition_id: int):
    """리더보드 (F4.1)"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        SELECT 
            p.id as participant_id,
            p.name,
            p.email,
            p.department,
            p.position,
            COUNT(s.id) as total_submissions,
            SUM(CASE WHEN s.status = 'completed' THEN 1 ELSE 0 END) as completed_submissions,
            AVG(json_extract(s.grading_result, '$.total_score')) as average_score
        FROM participants p
        LEFT JOIN submissions s ON p.id = s.participant_id AND s.competition_id = ?
        WHERE p.competition_id = ?
        GROUP BY p.id
        ORDER BY average_score DESC
    """, (competition_id, competition_id))
    
    leaderboard = []
    for rank, row in enumerate(c.fetchall(), 1):
        entry = dict(row)
        entry['rank'] = rank
        leaderboard.append(entry)
    
    conn.close()
    return leaderboard


@app.get("/submissions/{submission_id}/detail")
async def get_submission_detail(submission_id: int):
    """제출물 상세 정보 (F4.2)"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        SELECT s.*, p.name as participant_name, a.name as assignment_name
        FROM submissions s
        JOIN participants p ON s.participant_id = p.id
        JOIN assignments a ON s.assignment_id = a.id
        WHERE s.id = ?
    """, (submission_id,))
    
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Submission not found")
    
    detail = dict(row)
    
    # grading_result JSON 파싱
    if detail['grading_result']:
        detail['grading_result'] = json.loads(detail['grading_result'])
    
    conn.close()
    return detail


@app.post("/create_demo_data")
async def create_demo_data_endpoint():
    """실제 과제 데이터 생성 엔드포인트"""
    try:
        import subprocess
        result = subprocess.run(
            ["python3", "create_demo_data.py"],
            cwd=os.path.dirname(__file__) or ".",
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Demo data created successfully",
                "output": result.stdout
            }
        else:
            return {
                "status": "error",
                "message": "Failed to create demo data",
                "error": result.stderr
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----- 정적 파일 서빙 -----

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/app")
async def serve_frontend():
    """프론트엔드 서빙"""
    static_index = os.path.join("static", "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)
    else:
        return {"message": "Frontend not available yet"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
