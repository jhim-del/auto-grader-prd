"""
프롬프트 경진대회 자동 평가 플랫폼 v3.0
엑셀 일괄 업로드 방식
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
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import pandas as pd
import io

from grading_engine import GradingEngine
from file_parser import FileParser

# 환경변수
DATA_DIR = os.environ.get("DATA_DIR", ".")
DB_PATH = os.path.join(DATA_DIR, "competition_prd.db")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 채점 진행 상황 추적 (메모리에 저장)
grading_progress = {}

app = FastAPI(title="Auto-Grader v3.0 - 엑셀 일괄 업로드")

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
    name: str

class PractitionerUpdate(BaseModel):
    name: Optional[str] = None

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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # practitioners 테이블
    c.execute("""
        CREATE TABLE IF NOT EXISTS practitioners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            company TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # tasks 테이블
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            input_data TEXT NOT NULL,
            golden_output TEXT NOT NULL,
            evaluation_notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # submissions 테이블
    c.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            practitioner_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            prompt_text TEXT NOT NULL,
            submission_date TEXT DEFAULT CURRENT_TIMESTAMP,
            score REAL,
            grading_result TEXT,
            graded_at TEXT,
            FOREIGN KEY (practitioner_id) REFERENCES practitioners (id),
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
    """)
    
    conn.commit()
    conn.close()

# ============================================================================
# 라우트
# ============================================================================

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/")
async def read_root():
    """메인 페이지"""
    return FileResponse("static/index.html")

# ============================================================================
# 과제(Task) API
# ============================================================================

@app.get("/tasks")
async def get_tasks():
    """과제 목록 조회"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks ORDER BY id")
    tasks = [dict(row) for row in c.fetchall()]
    conn.close()
    return tasks

@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    """과제 상세 조회"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = c.fetchone()
    conn.close()
    
    if not task:
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다")
    
    return dict(task)

@app.post("/tasks")
async def create_task_with_files(
    title: str = Form(...),
    description: str = Form(None),
    evaluation_notes: str = Form(None),
    input_file: UploadFile = File(...),
    output_file: UploadFile = File(...)
):
    """과제 생성 (파일 업로드)"""
    
    # 입력 데이터 파싱
    input_content = await input_file.read()
    input_data = FileParser.parse_file(input_content, input_file.filename)
    
    # 기대 출력 파싱
    output_content = await output_file.read()
    golden_output = FileParser.parse_file(output_content, output_file.filename)
    
    # DB 저장
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO tasks (title, description, input_data, golden_output, evaluation_notes)
        VALUES (?, ?, ?, ?, ?)
    """, (title, description, input_data, golden_output, evaluation_notes))
    
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": task_id, "message": "과제가 생성되었습니다"}

@app.put("/tasks/{task_id}")
async def update_task_with_files(
    task_id: int,
    title: str = Form(None),
    description: str = Form(None),
    evaluation_notes: str = Form(None),
    input_file: UploadFile = File(None),
    output_file: UploadFile = File(None)
):
    """과제 수정 (파일 업로드)"""
    
    conn = get_db()
    c = conn.cursor()
    
    # 기존 과제 확인
    c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = c.fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다")
    
    # 수정할 필드 준비
    updates = {}
    if title is not None:
        updates['title'] = title
    if description is not None:
        updates['description'] = description
    if evaluation_notes is not None:
        updates['evaluation_notes'] = evaluation_notes
    
    # 파일이 업로드된 경우 파싱
    if input_file is not None:
        input_content = await input_file.read()
        updates['input_data'] = FileParser.parse_file(input_content, input_file.filename)
    
    if output_file is not None:
        output_content = await output_file.read()
        updates['golden_output'] = FileParser.parse_file(output_content, output_file.filename)
    
    # 업데이트 쿼리 생성
    if updates:
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [task_id]
        c.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
        conn.commit()
    
    conn.close()
    return {"message": "과제가 수정되었습니다"}

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """과제 삭제"""
    conn = get_db()
    c = conn.cursor()
    
    # 과제 존재 확인
    c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다")
    
    # 관련 제출물 삭제
    c.execute("DELETE FROM submissions WHERE task_id = ?", (task_id,))
    
    # 과제 삭제
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "과제가 삭제되었습니다"}

# ============================================================================
# 참가자 및 제출물 일괄 업로드 API
# ============================================================================

@app.post("/bulk-upload")
async def bulk_upload_submissions(
    task_id: int = Form(...),
    excel_file: UploadFile = File(...)
):
    """
    엑셀 파일로 참가자+제출물 일괄 업로드
    
    엑셀 형식:
    1행: 이름 | 프롬프트
    2행~: 홍길동 | 프롬프트 내용...
    """
    
    # 과제 존재 확인
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = c.fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다")
    
    # 엑셀 파일 읽기
    try:
        content = await excel_file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        # 컬럼명 확인 (1행: 이름, 프롬프트)
        if len(df.columns) < 2:
            raise HTTPException(status_code=400, detail="엑셀 파일에 최소 2개 컬럼(이름, 프롬프트)이 필요합니다")
        
        # 첫 2개 컬럼만 사용
        df = df.iloc[:, :2]
        df.columns = ['이름', '프롬프트']
        
        # 빈 행 제거
        df = df.dropna(subset=['이름', '프롬프트'])
        
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="업로드할 데이터가 없습니다")
        
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"엑셀 파일 읽기 실패: {str(e)}")
    
    # 일괄 등록
    created_count = 0
    skipped_count = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            name = str(row['이름']).strip()
            prompt = str(row['프롬프트']).strip()
            
            if not name or not prompt:
                skipped_count += 1
                continue
            
            # 참가자 존재 확인 또는 생성
            c.execute("SELECT id FROM practitioners WHERE name = ?", (name,))
            practitioner = c.fetchone()
            
            if practitioner:
                practitioner_id = practitioner['id']
            else:
                c.execute("INSERT INTO practitioners (name, email, company) VALUES (?, ?, ?)",
                         (name, "auto@generated.com", "참가자"))
                practitioner_id = c.lastrowid
            
            # 제출물 생성
            c.execute("""
                INSERT INTO submissions (practitioner_id, task_id, prompt_text, submission_date)
                VALUES (?, ?, ?, ?)
            """, (practitioner_id, task_id, prompt, datetime.now().isoformat()))
            
            created_count += 1
            
        except Exception as e:
            errors.append(f"행 {idx+2}: {str(e)}")
            skipped_count += 1
    
    conn.commit()
    conn.close()
    
    return {
        "message": "일괄 업로드 완료",
        "created": created_count,
        "skipped": skipped_count,
        "errors": errors if errors else None
    }

# ============================================================================
# 참가자(Practitioner) API
# ============================================================================

@app.get("/practitioners")
async def get_practitioners():
    """참가자 목록 조회"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM practitioners ORDER BY id")
    practitioners = [dict(row) for row in c.fetchall()]
    conn.close()
    return practitioners

@app.get("/practitioners/{practitioner_id}")
async def get_practitioner(practitioner_id: int):
    """참가자 상세 조회"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM practitioners WHERE id = ?", (practitioner_id,))
    practitioner = c.fetchone()
    conn.close()
    
    if not practitioner:
        raise HTTPException(status_code=404, detail="참가자를 찾을 수 없습니다")
    
    return dict(practitioner)

@app.post("/practitioners")
async def create_practitioner(practitioner: PractitionerCreate):
    """참가자 생성"""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO practitioners (name, email, company)
        VALUES (?, ?, ?)
    """, (practitioner.name, "auto@generated.com", "참가자"))
    
    practitioner_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": practitioner_id, "message": "참가자가 생성되었습니다"}

@app.put("/practitioners/{practitioner_id}")
async def update_practitioner(practitioner_id: int, practitioner: PractitionerUpdate):
    """참가자 수정"""
    conn = get_db()
    c = conn.cursor()
    
    # 참가자 존재 확인
    c.execute("SELECT * FROM practitioners WHERE id = ?", (practitioner_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="참가자를 찾을 수 없습니다")
    
    # 수정
    if practitioner.name is not None:
        c.execute("UPDATE practitioners SET name = ? WHERE id = ?",
                 (practitioner.name, practitioner_id))
    
    conn.commit()
    conn.close()
    
    return {"message": "참가자가 수정되었습니다"}

@app.delete("/practitioners/{practitioner_id}")
async def delete_practitioner(practitioner_id: int):
    """참가자 삭제"""
    conn = get_db()
    c = conn.cursor()
    
    # 참가자 존재 확인
    c.execute("SELECT * FROM practitioners WHERE id = ?", (practitioner_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="참가자를 찾을 수 없습니다")
    
    # 관련 제출물 삭제
    c.execute("DELETE FROM submissions WHERE practitioner_id = ?", (practitioner_id,))
    
    # 참가자 삭제
    c.execute("DELETE FROM practitioners WHERE id = ?", (practitioner_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "참가자가 삭제되었습니다"}

# ============================================================================
# 제출물(Submission) API
# ============================================================================

@app.get("/submissions")
async def get_submissions(task_id: Optional[int] = None):
    """제출물 목록 조회"""
    conn = get_db()
    c = conn.cursor()
    
    if task_id:
        c.execute("""
            SELECT s.*, p.name as practitioner_name, t.title as task_title
            FROM submissions s
            JOIN practitioners p ON s.practitioner_id = p.id
            JOIN tasks t ON s.task_id = t.id
            WHERE s.task_id = ?
            ORDER BY s.submission_date DESC
        """, (task_id,))
    else:
        c.execute("""
            SELECT s.*, p.name as practitioner_name, t.title as task_title
            FROM submissions s
            JOIN practitioners p ON s.practitioner_id = p.id
            JOIN tasks t ON s.task_id = t.id
            ORDER BY s.submission_date DESC
        """)
    
    submissions = [dict(row) for row in c.fetchall()]
    conn.close()
    return submissions

@app.get("/submissions/{submission_id}")
async def get_submission(submission_id: int):
    """제출물 상세 조회"""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT s.*, p.name as practitioner_name, t.title as task_title,
               t.input_data, t.golden_output, t.evaluation_notes
        FROM submissions s
        JOIN practitioners p ON s.practitioner_id = p.id
        JOIN tasks t ON s.task_id = t.id
        WHERE s.id = ?
    """, (submission_id,))
    
    submission = c.fetchone()
    conn.close()
    
    if not submission:
        raise HTTPException(status_code=404, detail="제출물을 찾을 수 없습니다")
    
    result = dict(submission)
    
    # grading_result JSON 파싱
    if result.get('grading_result'):
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
    
    # 과제 확인
    c.execute("SELECT * FROM tasks WHERE id = ?", (submission.task_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="과제를 찾을 수 없습니다")
    
    # 참가자 확인
    c.execute("SELECT * FROM practitioners WHERE id = ?", (submission.practitioner_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="참가자를 찾을 수 없습니다")
    
    # 제출물 생성
    c.execute("""
        INSERT INTO submissions (practitioner_id, task_id, prompt_text, submission_date)
        VALUES (?, ?, ?, ?)
    """, (submission.practitioner_id, submission.task_id, submission.prompt_text, 
          datetime.now().isoformat()))
    
    submission_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": submission_id, "message": "제출물이 생성되었습니다"}

@app.put("/submissions/{submission_id}")
async def update_submission(submission_id: int, submission: SubmissionUpdate):
    """제출물 수정"""
    conn = get_db()
    c = conn.cursor()
    
    # 제출물 존재 확인
    c.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="제출물을 찾을 수 없습니다")
    
    # 수정
    if submission.prompt_text is not None:
        c.execute("UPDATE submissions SET prompt_text = ? WHERE id = ?",
                 (submission.prompt_text, submission_id))
    
    conn.commit()
    conn.close()
    
    return {"message": "제출물이 수정되었습니다"}

@app.delete("/submissions/{submission_id}")
async def delete_submission(submission_id: int):
    """제출물 삭제"""
    conn = get_db()
    c = conn.cursor()
    
    # 제출물 존재 확인
    c.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="제출물을 찾을 수 없습니다")
    
    # 제출물 삭제
    c.execute("DELETE FROM submissions WHERE id = ?", (submission_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "제출물이 삭제되었습니다"}

# ============================================================================
# 채점 API
# ============================================================================

@app.post("/grade/{submission_id}")
async def grade_submission(submission_id: int, background_tasks: BackgroundTasks):
    """제출물 채점 시작 (백그라운드)"""
    
    # 제출물 조회
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT s.*, t.input_data, t.golden_output, t.evaluation_notes
        FROM submissions s
        JOIN tasks t ON s.task_id = t.id
        WHERE s.id = ?
    """, (submission_id,))
    
    submission = c.fetchone()
    conn.close()
    
    if not submission:
        raise HTTPException(status_code=404, detail="제출물을 찾을 수 없습니다")
    
    # 이미 채점 중인지 확인
    if submission_id in grading_progress:
        status = grading_progress[submission_id].get('status')
        if status in ['starting', 'step1', 'step2']:
            raise HTTPException(status_code=400, detail="이미 채점 중입니다")
    
    # 진행 상황 초기화
    grading_progress[submission_id] = {
        'status': 'starting',
        'current_step': '채점 준비 중...',
        'progress': 0,
        'details': None,
        'execution_count': 0
    }
    
    # 백그라운드 채점 시작
    background_tasks.add_task(
        grade_submission_task,
        submission_id,
        dict(submission)
    )
    
    return {"message": "채점이 시작되었습니다", "submission_id": submission_id}

async def grade_submission_task(submission_id: int, submission: dict):
    """백그라운드 채점 작업"""
    
    try:
        # 1단계: 프롬프트 실행 (3회)
        grading_progress[submission_id].update({
            'status': 'step1',
            'current_step': '프롬프트 실행 중 (1/3)...',
            'progress': 10
        })
        
        engine = GradingEngine(api_key=OPENAI_API_KEY)
        
        execution_results = []
        for i in range(3):
            grading_progress[submission_id].update({
                'current_step': f'프롬프트 실행 중 ({i+1}/3)...',
                'progress': 10 + (i * 20),
                'execution_count': i + 1
            })
            
            success, result, error = engine.execute_prompt(
                submission['prompt_text'],
                submission['input_data']
            )
            
            execution_results.append({
                'execution_number': i + 1,
                'success': success,
                'output': result if success else None,
                'error': error
            })
        
        # 2단계: 마스터 평가 프롬프트
        grading_progress[submission_id].update({
            'status': 'step2',
            'current_step': '종합 평가 중...',
            'progress': 70
        })
        
        success, result, error = engine.evaluate_outputs(
            submission['prompt_text'],
            submission['input_data'],
            submission['golden_output'],
            execution_results,
            submission.get('evaluation_notes')
        )
        
        if not success:
            raise Exception(f"평가 실패: {error}")
        
        # 채점 결과 저장
        grading_result = {
            'execution_results': execution_results,
            **result
        }
        
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            UPDATE submissions 
            SET score = ?, grading_result = ?, graded_at = ?
            WHERE id = ?
        """, (
            result.get('overall_score', 0),
            json.dumps(grading_result, ensure_ascii=False),
            datetime.now().isoformat(),
            submission_id
        ))
        conn.commit()
        conn.close()
        
        # 완료 상태
        grading_progress[submission_id].update({
            'status': 'completed',
            'current_step': '채점 완료!',
            'progress': 100,
            'details': result
        })
        
    except Exception as e:
        # 오류 상태
        grading_progress[submission_id].update({
            'status': 'error',
            'current_step': f'채점 오류: {str(e)}',
            'progress': 0,
            'error': str(e)
        })

@app.get("/grading/progress")
async def get_all_grading_progress():
    """모든 채점 진행 상황 조회"""
    return grading_progress

@app.get("/grading/progress/{submission_id}")
async def get_grading_progress(submission_id: int):
    """특정 제출물 채점 진행 상황 조회"""
    if submission_id not in grading_progress:
        return {"status": "not_started", "message": "채점이 시작되지 않았습니다"}
    
    return grading_progress[submission_id]

# ============================================================================
# 대시보드 및 통계 API
# ============================================================================

@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """대시보드 통계"""
    conn = get_db()
    c = conn.cursor()
    
    # 전체 통계
    c.execute("SELECT COUNT(*) as count FROM practitioners")
    total_practitioners = c.fetchone()['count']
    
    c.execute("SELECT COUNT(*) as count FROM tasks")
    total_tasks = c.fetchone()['count']
    
    c.execute("SELECT COUNT(*) as count FROM submissions")
    total_submissions = c.fetchone()['count']
    
    c.execute("SELECT COUNT(*) as count FROM submissions WHERE grading_result IS NOT NULL")
    graded_count = c.fetchone()['count']
    
    c.execute("SELECT AVG(score) as avg_score FROM submissions WHERE score IS NOT NULL")
    avg_score = c.fetchone()['avg_score'] or 0
    
    # 과제별 통계
    c.execute("""
        SELECT 
            t.id,
            t.title,
            COUNT(s.id) as submission_count,
            COUNT(CASE WHEN s.grading_result IS NOT NULL THEN 1 END) as graded_count,
            AVG(s.score) as avg_score
        FROM tasks t
        LEFT JOIN submissions s ON t.id = s.task_id
        GROUP BY t.id
    """)
    
    task_stats = [dict(row) for row in c.fetchall()]
    
    conn.close()
    
    return {
        'total_practitioners': total_practitioners,
        'total_tasks': total_tasks,
        'total_submissions': total_submissions,
        'graded_count': graded_count,
        'avg_score': round(avg_score, 2),
        'task_stats': task_stats
    }

@app.get("/leaderboard")
async def get_leaderboard(task_id: Optional[int] = None):
    """리더보드"""
    conn = get_db()
    c = conn.cursor()
    
    if task_id:
        c.execute("""
            SELECT 
                p.name as practitioner_name,
                t.title as task_title,
                s.score,
                s.graded_at,
                s.id as submission_id
            FROM submissions s
            JOIN practitioners p ON s.practitioner_id = p.id
            JOIN tasks t ON s.task_id = t.id
            WHERE s.score IS NOT NULL AND s.task_id = ?
            ORDER BY s.score DESC, s.graded_at ASC
        """, (task_id,))
    else:
        c.execute("""
            SELECT 
                p.name as practitioner_name,
                t.title as task_title,
                s.score,
                s.graded_at,
                s.id as submission_id
            FROM submissions s
            JOIN practitioners p ON s.practitioner_id = p.id
            JOIN tasks t ON s.task_id = t.id
            WHERE s.score IS NOT NULL
            ORDER BY s.score DESC, s.graded_at ASC
        """)
    
    leaderboard = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return leaderboard

# ============================================================================
# Static 파일 서빙
# ============================================================================

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
