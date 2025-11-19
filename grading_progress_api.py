"""
채점 진행 상황 API 추가 코드
main.py의 687번째 줄 앞에 삽입
"""

API_CODE = '''
# ============================================================================
# API: 채점 진행 상황 조회
# ============================================================================

@app.get("/grading/progress/{submission_id}")
async def get_grading_progress(submission_id: int):
    """
    특정 제출물의 채점 진행 상황 조회
    """
    if submission_id not in grading_progress:
        # 진행 중이 아니면 DB에서 상태 확인
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT status FROM submissions WHERE id = ?", (submission_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        status = row[0]
        if status == "completed":
            return {
                "status": "completed",
                "current_step": "채점 완료",
                "progress": 100,
                "details": "채점이 종료되었습니다.",
                "execution_count": 3
            }
        elif status == "failed":
            return {
                "status": "failed",
                "current_step": "채점 실패",
                "progress": 0,
                "details": "채점에 실패했습니다.",
                "execution_count": 0
            }
        else:
            return {
                "status": "not_started",
                "current_step": "대기 중",
                "progress": 0,
                "details": "채점이 시작되지 않았습니다.",
                "execution_count": 0
            }
    
    return grading_progress[submission_id]

@app.get("/grading/progress")
async def get_all_grading_progress():
    """
    현재 진행 중인 모든 채점의 진행 상황 조회
    """
    return {
        "active_gradings": len(grading_progress),
        "details": grading_progress
    }
'''
