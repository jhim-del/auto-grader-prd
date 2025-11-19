"""
프롬프트 경진대회 자동 평가 플랫폼 v3.0
완전한 관리 시스템 - 사용자가 모든 설정 가능
"""

import os
import json
import sqlite3
import asyncio
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from grading_engine import GradingEngine
from file_parser import FileParser

# 환경변수
DATA_DIR = os.environ.get("DATA_DIR", ".")
DB_PATH = os.path.join(DATA_DIR, "competition_prd.db")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 채점 진행 상황 추적 (메모리에 저장)
grading_progress = {}
# 구조: {submission_id: {status, current_step, progress, details, execution_count, ...}}

app = FastAPI(title="Auto-Grader v3.0 - 완전한 관리 시스템")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Pydantic 모델
# ============================================================================

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    input_data: str
    golden_output: str
    evaluation_notes: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    input_data: Optional[str] = None
    golden_output: Optional[str] = None
    evaluation_notes: Optional[str] = None

class PractitionerCreate(BaseModel):
    name: str  # 이름만 필요

class PractitionerUpdate(BaseModel):
    name: Optional[str] = None  # 이름만 수정 가능

class SubmissionCreate(BaseModel):
    task_id: int
    practitioner_id: int
    prompt_text: str

class SubmissionUpdate(BaseModel):
    prompt_text: Optional[str] = None

# ============================================================================
# 데이터베이스 헬퍼
# ============================================================================

def get_db():
    """DB 연결"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """DB 초기화"""
    conn = get_db()
    c = conn.cursor()
    
    # practitioners 테이블 (이름만)
    c.execute("""
    CREATE TABLE IF NOT EXISTS practitioners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # tasks 테이블
    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        input_data TEXT,
        golden_output TEXT,
        evaluation_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # submissions 테이블
    c.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        practitioner_id INTEGER NOT NULL,
        prompt_text TEXT NOT NULL,
        status TEXT DEFAULT 'submitted',
        execution_output_1 TEXT,
        execution_output_2 TEXT,
        execution_output_3 TEXT,
        grading_result TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        graded_at TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id),
        FOREIGN KEY (practitioner_id) REFERENCES practitioners(id)
    )
    """)
    
    conn.commit()
    conn.close()

# ============================================================================
# 시작 이벤트
# ============================================================================

@app.on_event("startup")
async def startup():
    """서버 시작 시 DB 초기화"""
    init_db()
    print(f"✅ Database initialized at {DB_PATH}")

# ============================================================================
# API: 과제 관리
# ============================================================================

@app.get("/tasks")
async def get_tasks():
    """모든 과제 조회"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks ORDER BY created_at DESC")
    tasks = [dict(row) for row in c.fetchall()]
    conn.close()
    return tasks

@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    """특정 과제 조회"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = c.fetchone()
    conn.close()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return dict(task)

@app.post("/tasks")
async def create_task(task: TaskCreate):
    """과제 생성"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO tasks (title, description, input_data, golden_output, evaluation_notes)
        VALUES (?, ?, ?, ?, ?)
    """, (task.title, task.description, task.input_data, task.golden_output, task.evaluation_notes))
    
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": task_id, "message": "Task created successfully"}

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: TaskUpdate):
    """과제 수정"""
    conn = get_db()
    c = conn.cursor()
    
    # 존재 확인
    c.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 수정할 필드만 업데이트
    updates = []
    values = []
    
    if task.title is not None:
        updates.append("title = ?")
        values.append(task.title)
    if task.description is not None:
        updates.append("description = ?")
        values.append(task.description)
    if task.input_data is not None:
        updates.append("input_data = ?")
        values.append(task.input_data)
    if task.golden_output is not None:
        updates.append("golden_output = ?")
        values.append(task.golden_output)
    if task.evaluation_notes is not None:
        updates.append("evaluation_notes = ?")
        values.append(task.evaluation_notes)
    
    if updates:
        values.append(task_id)
        c.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
    
    conn.close()
    return {"message": "Task updated successfully"}

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """과제 삭제"""
    conn = get_db()
    c = conn.cursor()
    
    # 연결된 제출물 먼저 삭제
    c.execute("DELETE FROM submissions WHERE task_id = ?", (task_id,))
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    conn.commit()
    conn.close()
    return {"message": "Task deleted successfully"}

# ============================================================================
# API: 참가자 관리
# ============================================================================

@app.get("/practitioners")
async def get_practitioners():
    """모든 참가자 조회"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM practitioners ORDER BY created_at DESC")
    practitioners = [dict(row) for row in c.fetchall()]
    conn.close()
    return practitioners

@app.get("/practitioners/{practitioner_id}")
async def get_practitioner(practitioner_id: int):
    """특정 참가자 조회"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM practitioners WHERE id = ?", (practitioner_id,))
    practitioner = c.fetchone()
    conn.close()
    
    if not practitioner:
        raise HTTPException(status_code=404, detail="Practitioner not found")
    
    return dict(practitioner)

@app.post("/practitioners")
async def create_practitioner(practitioner: PractitionerCreate):
    """참가자 생성"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO practitioners (name)
        VALUES (?)
    """, (practitioner.name,))
    
    practitioner_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": practitioner_id, "message": "Practitioner created successfully"}

@app.put("/practitioners/{practitioner_id}")
async def update_practitioner(practitioner_id: int, practitioner: PractitionerUpdate):
    """참가자 수정"""
    conn = get_db()
    c = conn.cursor()
    
    # 존재 확인
    c.execute("SELECT id FROM practitioners WHERE id = ?", (practitioner_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Practitioner not found")
    
    # 이름만 업데이트
    if practitioner.name is not None:
        c.execute("UPDATE practitioners SET name = ? WHERE id = ?", (practitioner.name, practitioner_id))
        conn.commit()
    
    conn.close()
    return {"message": "Practitioner updated successfully"}

@app.delete("/practitioners/{practitioner_id}")
async def delete_practitioner(practitioner_id: int):
    """참가자 삭제"""
    conn = get_db()
    c = conn.cursor()
    
    # 연결된 제출물 먼저 삭제
    c.execute("DELETE FROM submissions WHERE practitioner_id = ?", (practitioner_id,))
    c.execute("DELETE FROM practitioners WHERE id = ?", (practitioner_id,))
    
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Practitioner not found")
    
    conn.commit()
    conn.close()
    return {"message": "Practitioner deleted successfully"}

# ============================================================================
# API: 제출물 관리
# ============================================================================

@app.get("/submissions")
async def get_submissions(task_id: Optional[int] = None, practitioner_id: Optional[int] = None):
    """모든 제출물 조회 (필터 옵션)"""
    conn = get_db()
    c = conn.cursor()
    
    query = """
        SELECT s.*, p.name as practitioner_name, t.title as task_title
        FROM submissions s
        JOIN practitioners p ON s.practitioner_id = p.id
        JOIN tasks t ON s.task_id = t.id
        WHERE 1=1
    """
    params = []
    
    if task_id:
        query += " AND s.task_id = ?"
        params.append(task_id)
    if practitioner_id:
        query += " AND s.practitioner_id = ?"
        params.append(practitioner_id)
    
    query += " ORDER BY s.created_at DESC"
    
    c.execute(query, params)
    submissions = [dict(row) for row in c.fetchall()]
    conn.close()
    
    # grading_result JSON 파싱
    for sub in submissions:
        if sub['grading_result']:
            try:
                sub['grading_result'] = json.loads(sub['grading_result'])
            except:
                pass
    
    return submissions

@app.get("/submissions/{submission_id}")
async def get_submission(submission_id: int):
    """특정 제출물 상세 조회"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        SELECT s.*, p.name as practitioner_name,
               t.title as task_title, t.input_data, t.golden_output, t.evaluation_notes
        FROM submissions s
        JOIN practitioners p ON s.practitioner_id = p.id
        JOIN tasks t ON s.task_id = t.id
        WHERE s.id = ?
    """, (submission_id,))
    
    submission = c.fetchone()
    conn.close()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    result = dict(submission)
    
    # grading_result JSON 파싱
    if result['grading_result']:
        try:
            result['grading_result'] = json.loads(result['grading_result'])
        except:
            pass
    
    return result

@app.post("/submissions")
async def create_submission(submission: SubmissionCreate):
    """제출물 생성"""
    conn = get_db()
    c = conn.cursor()
    
    # task와 practitioner 존재 확인
    c.execute("SELECT id FROM tasks WHERE id = ?", (submission.task_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    c.execute("SELECT id FROM practitioners WHERE id = ?", (submission.practitioner_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Practitioner not found")
    
    c.execute("""
        INSERT INTO submissions (task_id, practitioner_id, prompt_text, status)
        VALUES (?, ?, ?, 'submitted')
    """, (submission.task_id, submission.practitioner_id, submission.prompt_text))
    
    submission_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": submission_id, "message": "Submission created successfully"}

@app.put("/submissions/{submission_id}")
async def update_submission(submission_id: int, submission: SubmissionUpdate):
    """제출물 수정 (프롬프트만)"""
    conn = get_db()
    c = conn.cursor()
    
    # 존재 확인
    c.execute("SELECT id FROM submissions WHERE id = ?", (submission_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Submission not found")
    
    if submission.prompt_text is not None:
        c.execute("UPDATE submissions SET prompt_text = ?, status = 'submitted' WHERE id = ?", 
                  (submission.prompt_text, submission_id))
        conn.commit()
    
    conn.close()
    return {"message": "Submission updated successfully"}

@app.delete("/submissions/{submission_id}")
async def delete_submission(submission_id: int):
    """제출물 삭제"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("DELETE FROM submissions WHERE id = ?", (submission_id,))
    
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Submission not found")
    
    conn.commit()
    conn.close()
    return {"message": "Submission deleted successfully"}

# ============================================================================
# API: 채점 실행
# ============================================================================

async def grade_submission_background(submission_id: int):
    """백그라운드에서 제출물 채점"""
    if not OPENAI_API_KEY:
        print(f"⚠️  OPENAI_API_KEY not set, skipping grading for submission {submission_id}")
        return
    
    # 진행 상황 초기화
    grading_progress[submission_id] = {"status": "starting", "current_step": "준비 중", "progress": 0, "details": "채점 시작...", "execution_count": 0, "started_at": time.time(), "updated_at": time.time()}
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # 제출물 정보 가져오기
        c.execute("""
            SELECT s.*, t.golden_output, t.input_data
            FROM submissions s
            JOIN tasks t ON s.task_id = t.id
            WHERE s.id = ?
        """, (submission_id,))
        
        submission = c.fetchone()
        if not submission:
            return
        
        submission = dict(submission)
        
        # 상태 업데이트: 채점 중
        c.execute("UPDATE submissions SET status = 'grading' WHERE id = ?", (submission_id,))
        conn.commit()
        
        # 채점 엔진 초기화
        grading_progress[submission_id].update({"status": "step1", "current_step": "1단계: 프롬프트 3회 실행", "progress": 30, "details": "GPT API 호출 중...", "updated_at": time.time()})
        engine = GradingEngine(api_key=OPENAI_API_KEY)
        
        # 1단계: 프롬프트 3회 실행
        success, outputs, error_msg = engine.execute_prompt_3_times(
            submission['prompt_text'],
            submission['input_data']
        )
        
        if not success:
            c.execute("""
                UPDATE submissions 
                SET status = 'failed', grading_result = ? 
                WHERE id = ?
            """, (json.dumps({"error": error_msg}), submission_id))
            conn.commit()
            return
        
        # 실행 결과 저장
        c.execute("""
            UPDATE submissions 
            SET execution_output_1 = ?, execution_output_2 = ?, execution_output_3 = ?
            WHERE id = ?
        """, (outputs[0], outputs[1], outputs[2], submission_id))
        conn.commit()
        
        # 2단계: 마스터 평가
        grading_progress[submission_id].update({"status": "step2", "current_step": "2단계: 평가", "progress": 70, "details": "마스터 평가 중...", "execution_count": 3, "updated_at": time.time()})
        success, grading_result, error_msg = engine.evaluate_outputs(
            submission['prompt_text'],
            outputs,
            submission['golden_output']
        )
        
        if not success:
            c.execute("""
                UPDATE submissions 
                SET status = 'failed', grading_result = ? 
                WHERE id = ?
            """, (json.dumps({"error": error_msg}), submission_id))
            conn.commit()
            return
        
        # 채점 결과 저장
        c.execute("""
            UPDATE submissions 
            SET status = 'completed', 
                grading_result = ?,
                graded_at = ?
            WHERE id = ?
        """, (json.dumps(grading_result), datetime.now().isoformat(), submission_id))
        conn.commit()
        
        grading_progress[submission_id].update({"status": "completed", "current_step": "완료", "progress": 100, "details": "채점 완료", "updated_at": time.time()})
        print(f"✅ Grading completed for submission {submission_id}")
        
    except Exception as e:
        print(f"❌ Grading failed for submission {submission_id}: {e}")
        c.execute("""
            UPDATE submissions 
            SET status = 'failed', grading_result = ? 
            WHERE id = ?
        """, (json.dumps({"error": str(e)}), submission_id))
        conn.commit()
    finally:
        conn.close()

@app.post("/submissions/{submission_id}/grade")
async def grade_submission(submission_id: int, background_tasks: BackgroundTasks):
    """제출물 채점 시작"""
    conn = get_db()
    c = conn.cursor()
    
    # 존재 확인
    c.execute("SELECT id, status FROM submissions WHERE id = ?", (submission_id,))
    submission = c.fetchone()
    conn.close()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    if submission['status'] == 'grading':
        raise HTTPException(status_code=400, detail="Already grading")
    
    # 백그라운드 작업 추가
    background_tasks.add_task(grade_submission_background, submission_id)
    
    return {"message": "Grading started", "submission_id": submission_id}

@app.post("/tasks/{task_id}/grade_all")
async def grade_all_submissions(task_id: int, background_tasks: BackgroundTasks):
    """특정 과제의 모든 제출물 채점"""
    conn = get_db()
    c = conn.cursor()
    
    # task 존재 확인
    c.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 제출물 목록
    c.execute("SELECT id FROM submissions WHERE task_id = ? AND status IN ('submitted', 'failed')", (task_id,))
    submission_ids = [row['id'] for row in c.fetchall()]
    conn.close()
    
    if not submission_ids:
        return {"message": "No submissions to grade", "count": 0}
    
    # 백그라운드 작업 추가
    for sub_id in submission_ids:
        background_tasks.add_task(grade_submission_background, sub_id)
    
    return {"message": f"Grading started for {len(submission_ids)} submissions", 
            "submission_ids": submission_ids}

# ============================================================================
# API: 채점 현황 대시보드
# ============================================================================

@app.get("/tasks/{task_id}/dashboard")
async def get_task_dashboard(task_id: int):
    """과제별 채점 현황 대시보드"""
    conn = get_db()
    c = conn.cursor()
    
    # Task 정보
    c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = c.fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = dict(task)
    
    # 제출물 통계
    c.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'grading' THEN 1 ELSE 0 END) as grading,
            SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
        FROM submissions
        WHERE task_id = ?
    """, (task_id,))
    
    stats = dict(c.fetchone())
    
    # 제출물 상세 (채점 결과 포함)
    c.execute("""
        SELECT s.id, s.status, s.created_at, s.graded_at,
               s.grading_result, s.execution_output_1, s.execution_output_2, s.execution_output_3,
               p.name as practitioner_name
        FROM submissions s
        JOIN practitioners p ON s.practitioner_id = p.id
        WHERE s.task_id = ?
        ORDER BY s.created_at DESC
    """, (task_id,))
    
    submissions = []
    for row in c.fetchall():
        sub = dict(row)
        if sub['grading_result']:
            try:
                sub['grading_result'] = json.loads(sub['grading_result'])
            except:
                pass
        submissions.append(sub)
    
    conn.close()
    
    # 리더보드 (점수 순)
    leaderboard = []
    for sub in submissions:
        if sub['status'] == 'completed' and sub['grading_result']:
            # detailed_criteria에서 점수 추출 (동적으로)
            criteria = sub['grading_result'].get('detailed_criteria', [])
            criteria_dict = {}
            for c in criteria:
                criteria_dict[c['criterion']] = c['score']
            
            leaderboard.append({
                "submission_id": sub['id'],
                "practitioner_name": sub['practitioner_name'],
                "total_score": sub['grading_result'].get('overall_score', 0),
                "criteria": criteria_dict,  # 모든 평가 기준을 전달
                "graded_at": sub['graded_at']
            })
    
    # 총점 기준으로 정렬
    leaderboard.sort(key=lambda x: x['total_score'], reverse=True)
    
    return {
        "task": task,
        "statistics": stats,
        "submissions": submissions,
        "leaderboard": leaderboard
    }

# ============================================================================
# API: 채점 진행 상황 조회
# ============================================================================

@app.get("/grading/progress/{submission_id}")
async def get_grading_progress(submission_id: int):
    """특정 제출물의 채점 진행 상황 조회"""
    if submission_id not in grading_progress:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT status FROM submissions WHERE id = ?", (submission_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        status = row[0]
        if status == "completed":
            return {"status": "completed", "current_step": "채점 완료", "progress": 100, 
                    "details": "채점이 종료되었습니다.", "execution_count": 3}
        elif status == "failed":
            return {"status": "failed", "current_step": "채점 실패", "progress": 0, 
                    "details": "채점에 실패했습니다.", "execution_count": 0}
        else:
            return {"status": "not_started", "current_step": "대기 중", "progress": 0, 
                    "details": "채점이 시작되지 않았습니다.", "execution_count": 0}
    
    return grading_progress[submission_id]

@app.get("/grading/progress")
async def get_all_grading_progress():
    """현재 진행 중인 모든 채점의 진행 상황 조회"""
    return {"active_gradings": len(grading_progress), "details": grading_progress}

# ============================================================================
# API: 파일 업로드
# ============================================================================

@app.post("/upload/parse")
async def upload_and_parse_file(file: UploadFile = File(...)):
    """
    파일 업로드 및 파싱
    PDF, TXT, Excel 파일 지원
    """
    try:
        # 파일 확장자 확인
        filename = file.filename or ""
        if not filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # 지원하는 파일 형식 확인
        supported_extensions = ('.txt', '.pdf', '.xlsx', '.xls', '.csv')
        if not filename.lower().endswith(supported_extensions):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported: {', '.join(supported_extensions)}"
            )
        
        # 파일 읽기
        content = await file.read()
        
        # 파일 타입 감지
        file_type = FileParser.detect_file_type(filename)
        if not file_type:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # 파일 파싱
        success, parsed_text = FileParser.parse_file(content, file_type)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"File parsing failed: {parsed_text}")
        
        return {
            "filename": filename,
            "size": len(content),
            "text": parsed_text,  # 프론트엔드에서 'text' 필드 사용
            "content": parsed_text,  # 호환성
            "preview": parsed_text[:500] + ("..." if len(parsed_text) > 500 else "")
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File parsing failed: {str(e)}")

# ============================================================================
# 정적 파일 서빙
# ============================================================================

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

# ============================================================================
# 서버 실행
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
