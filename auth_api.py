"""
관리자 인증 및 참가자 제출 API 추가 코드
"""

PYDANTIC_MODELS = '''
class AdminLoginRequest(BaseModel):
    password: str

class ParticipantCheckRequest(BaseModel):
    name: str
'''

AUTH_API_CODE = '''
# ============================================================================
# API: 관리자 인증
# ============================================================================

def verify_admin_session(token: str) -> bool:
    """관리자 세션 검증"""
    if not token or token not in admin_sessions:
        return False
    
    # 세션 만료 확인
    if time.time() - admin_sessions[token] > SESSION_TIMEOUT:
        del admin_sessions[token]
        return False
    
    return True

@app.post("/admin/login")
async def admin_login(request: AdminLoginRequest):
    """관리자 로그인"""
    if request.password == ADMIN_PASSWORD:
        # 세션 토큰 생성
        token = secrets.token_urlsafe(32)
        admin_sessions[token] = time.time()
        
        return {
            "success": True,
            "token": token,
            "message": "로그인 성공"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid password")

@app.post("/admin/logout")
async def admin_logout(token: str):
    """관리자 로그아웃"""
    if token in admin_sessions:
        del admin_sessions[token]
    return {"success": True}

@app.get("/admin/verify")
async def verify_admin(token: str):
    """관리자 세션 검증"""
    if verify_admin_session(token):
        return {"valid": True}
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

# ============================================================================
# API: 참가자 제출 관련
# ============================================================================

@app.post("/participants/check")
async def check_or_create_participant(request: ParticipantCheckRequest):
    """참가자 확인 또는 생성 + 제출 이력 확인"""
    conn = get_db()
    c = conn.cursor()
    
    try:
        # 기존 참가자 확인
        c.execute("SELECT id FROM practitioners WHERE name = ?", (request.name,))
        row = c.fetchone()
        
        if row:
            practitioner_id = row[0]
            
            # 제출 이력 확인
            c.execute("""
                SELECT task_id FROM submissions 
                WHERE practitioner_id = ?
            """, (practitioner_id,))
            
            submitted_tasks = [r[0] for r in c.fetchall()]
            
            conn.close()
            return {
                "id": practitioner_id,
                "name": request.name,
                "already_submitted": len(submitted_tasks) > 0,
                "submitted_tasks": submitted_tasks
            }
        else:
            # 새 참가자 생성
            c.execute("""
                INSERT INTO practitioners (name, created_at)
                VALUES (?, ?)
            """, (request.name, datetime.now().isoformat()))
            
            conn.commit()
            practitioner_id = c.lastrowid
            conn.close()
            
            return {
                "id": practitioner_id,
                "name": request.name,
                "already_submitted": False,
                "submitted_tasks": []
            }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
'''

ROUTE_UPDATES = '''
# 메인 페이지 라우팅
@app.get("/")
async def root():
    """참가자용 메인 페이지"""
    return FileResponse("static/participant.html")

@app.get("/admin/login")
async def admin_login_page():
    """관리자 로그인 페이지"""
    return FileResponse("static/admin-login.html")

@app.get("/admin")
async def admin_page(token: str = ""):
    """관리자 페이지 (인증 필요)"""
    if not token or not verify_admin_session(token):
        return RedirectResponse(url="/admin/login")
    return FileResponse("static/index.html")
'''

print("=" * 70)
print("인증 API 코드 생성 완료")
print("=" * 70)
print("\n다음 코드를 main.py에 추가해야 합니다:")
print("\n1. Pydantic 모델 섹션에:")
print(PYDANTIC_MODELS)
print("\n2. API 섹션에:")
print(AUTH_API_CODE[:500] + "...")
print("\n3. 기존 @app.get('/app') 대체:")
print(ROUTE_UPDATES)
