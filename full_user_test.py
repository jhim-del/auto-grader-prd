#!/usr/bin/env python3
"""
완전한 사용자 경험 테스트
실제 사용자 시나리오 기반 블랙박스 테스트
"""

import requests
import json
import time
from datetime import datetime

# 테스트 설정
BASE_URL = "http://localhost:8000"
TEST_RESULTS = []

def log_test(name, passed, details=""):
    """테스트 결과 기록"""
    result = "✅ PASS" if passed else "❌ FAIL"
    print(f"{result} | {name}")
    if details:
        print(f"     └─ {details}")
    TEST_RESULTS.append({
        "test": name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

def test_api_health():
    """API 헬스 체크"""
    try:
        response = requests.get(f"{BASE_URL}/tasks", timeout=5)
        log_test("API Health Check", response.status_code == 200, f"Status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        log_test("API Health Check", False, str(e))
        return False

# ============================================================================
# 시나리오 1: 과제 생성 (정상 케이스)
# ============================================================================

def test_create_task_normal():
    """과제 생성 - 정상 케이스"""
    task_data = {
        "title": "테스트 과제 A",
        "description": "KPI 데이터 분석 과제입니다",
        "input_data": "| 지표 | 값 |\n|------|-----|\n| Revenue | 1,000,000 |",
        "golden_output": "분석 결과: 매출 100만원",
        "evaluation_notes": "정확성을 중심으로 평가"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tasks", json=task_data)
        passed = response.status_code == 200
        task_id = response.json().get("id") if passed else None
        log_test("과제 생성 (정상)", passed, f"Task ID: {task_id}")
        return task_id
    except Exception as e:
        log_test("과제 생성 (정상)", False, str(e))
        return None

def test_create_task_long_text():
    """과제 생성 - 긴 텍스트"""
    long_text = "테스트 " * 1000  # 약 7000자
    task_data = {
        "title": "긴 텍스트 테스트",
        "description": "긴 텍스트를 포함한 과제",
        "input_data": long_text,
        "golden_output": long_text,
        "evaluation_notes": "긴 텍스트 처리 테스트"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tasks", json=task_data)
        passed = response.status_code == 200
        log_test("과제 생성 (긴 텍스트)", passed, f"{len(long_text)}자")
        return response.json().get("id") if passed else None
    except Exception as e:
        log_test("과제 생성 (긴 텍스트)", False, str(e))
        return None

def test_create_task_special_chars():
    """과제 생성 - 특수문자"""
    task_data = {
        "title": "특수문자 테스트 !@#$%^&*()",
        "description": "특수문자 포함: <>&\"'",
        "input_data": "JSON: {\"key\": \"value\"}\nSQL: SELECT * FROM table;",
        "golden_output": "코드 블록:\n```python\nprint('Hello')\n```",
        "evaluation_notes": "특수문자 이스케이프 테스트"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tasks", json=task_data)
        passed = response.status_code == 200
        log_test("과제 생성 (특수문자)", passed)
        return response.json().get("id") if passed else None
    except Exception as e:
        log_test("과제 생성 (특수문자)", False, str(e))
        return None

def test_create_task_missing_required():
    """과제 생성 - 필수 필드 누락"""
    task_data = {
        "title": "필수 필드 누락 테스트"
        # input_data와 golden_output 누락
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tasks", json=task_data)
        # 422 Unprocessable Entity가 나와야 정상
        passed = response.status_code == 422
        log_test("과제 생성 (필수 필드 누락)", passed, f"Status: {response.status_code}")
    except Exception as e:
        log_test("과제 생성 (필수 필드 누락)", False, str(e))

# ============================================================================
# 시나리오 2: 참가자 등록
# ============================================================================

def test_create_practitioner_normal():
    """참가자 등록 - 정상 케이스"""
    timestamp = int(time.time() * 1000)
    practitioner_data = {
        "name": "테스트 사용자1",
        "email": f"test{timestamp}@example.com",
        "department": "데이터분석팀",
        "position": "연구원",
        "years_of_experience": 3
    }
    
    try:
        response = requests.post(f"{BASE_URL}/practitioners", json=practitioner_data)
        passed = response.status_code == 200
        practitioner_id = response.json().get("id") if passed else None
        log_test("참가자 등록 (정상)", passed, f"Practitioner ID: {practitioner_id}")
        return practitioner_id
    except Exception as e:
        log_test("참가자 등록 (정상)", False, str(e))
        return None

def test_create_practitioner_duplicate_email():
    """참가자 등록 - 중복 이메일"""
    # 먼저 사용자 생성
    email = f"dup{int(time.time()*1000)}@ex.com"
    requests.post(f"{BASE_URL}/practitioners", json={"name": "First", "email": email})
    time.sleep(0.1)
    
    # 같은 이메일로 다시 시도
    practitioner_data = {
        "name": "테스트 사용자2",
        "email": email,
        "department": "개발팀",
        "position": "개발자"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/practitioners", json=practitioner_data)
        # 400 Bad Request가 나와야 정상
        passed = response.status_code == 400
        log_test("참가자 등록 (중복 이메일)", passed, f"Status: {response.status_code}")
    except Exception as e:
        log_test("참가자 등록 (중복 이메일)", False, str(e))

def test_create_practitioner_invalid_email():
    """참가자 등록 - 잘못된 이메일 형식"""
    practitioner_data = {
        "name": "테스트 사용자3",
        "email": "invalid-email",  # 잘못된 형식
        "department": "마케팅팀"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/practitioners", json=practitioner_data)
        # 422 Unprocessable Entity가 나와야 정상
        passed = response.status_code == 422
        log_test("참가자 등록 (잘못된 이메일)", passed, f"Status: {response.status_code}")
    except Exception as e:
        log_test("참가자 등록 (잘못된 이메일)", False, str(e))

def test_create_practitioner_optional_fields():
    """참가자 등록 - 선택 필드만"""
    timestamp = int(time.time() * 1000)
    practitioner_data = {
        "name": "최소 정보 사용자",
        "email": f"min{timestamp}@example.com"
        # department, position, years_of_experience 생략
    }
    
    try:
        response = requests.post(f"{BASE_URL}/practitioners", json=practitioner_data)
        passed = response.status_code == 200
        log_test("참가자 등록 (최소 필드)", passed)
        return response.json().get("id") if passed else None
    except Exception as e:
        log_test("참가자 등록 (최소 필드)", False, str(e))
        return None

# ============================================================================
# 시나리오 3: 제출물 등록
# ============================================================================

def test_create_submission_normal(task_id, practitioner_id):
    """제출물 등록 - 정상 케이스"""
    if not task_id or not practitioner_id:
        log_test("제출물 등록 (정상)", False, "Task ID 또는 Practitioner ID 없음")
        return None
    
    submission_data = {
        "task_id": task_id,
        "practitioner_id": practitioner_id,
        "prompt_text": "너는 데이터 분석가야. 다음 KPI를 분석해줘:\n\n[입력 데이터]\n\n단계별로 분석하고 인사이트를 제공해."
    }
    
    try:
        response = requests.post(f"{BASE_URL}/submissions", json=submission_data)
        passed = response.status_code == 200
        submission_id = response.json().get("id") if passed else None
        log_test("제출물 등록 (정상)", passed, f"Submission ID: {submission_id}")
        return submission_id
    except Exception as e:
        log_test("제출물 등록 (정상)", False, str(e))
        return None

def test_create_submission_long_prompt(task_id, practitioner_id):
    """제출물 등록 - 긴 프롬프트"""
    if not task_id or not practitioner_id:
        log_test("제출물 등록 (긴 프롬프트)", False, "Task ID 또는 Practitioner ID 없음")
        return None
    
    long_prompt = "# 역할\n너는 전문 데이터 분석가야.\n\n" + ("## 지침\n단계별로 분석해.\n\n" * 100)
    
    submission_data = {
        "task_id": task_id,
        "practitioner_id": practitioner_id,
        "prompt_text": long_prompt
    }
    
    try:
        response = requests.post(f"{BASE_URL}/submissions", json=submission_data)
        passed = response.status_code == 200
        log_test("제출물 등록 (긴 프롬프트)", passed, f"{len(long_prompt)}자")
        return response.json().get("id") if passed else None
    except Exception as e:
        log_test("제출물 등록 (긴 프롬프트)", False, str(e))
        return None

def test_create_submission_invalid_task():
    """제출물 등록 - 존재하지 않는 과제"""
    submission_data = {
        "task_id": 99999,  # 존재하지 않는 ID
        "practitioner_id": 1,
        "prompt_text": "테스트 프롬프트"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/submissions", json=submission_data)
        # 404 Not Found가 나와야 정상
        passed = response.status_code == 404
        log_test("제출물 등록 (존재하지 않는 과제)", passed, f"Status: {response.status_code}")
    except Exception as e:
        log_test("제출물 등록 (존재하지 않는 과제)", False, str(e))

# ============================================================================
# 시나리오 4: 데이터 조회
# ============================================================================

def test_get_tasks():
    """과제 목록 조회"""
    try:
        response = requests.get(f"{BASE_URL}/tasks")
        passed = response.status_code == 200
        count = len(response.json()) if passed else 0
        log_test("과제 목록 조회", passed, f"{count}개")
        return passed
    except Exception as e:
        log_test("과제 목록 조회", False, str(e))
        return False

def test_get_practitioners():
    """참가자 목록 조회"""
    try:
        response = requests.get(f"{BASE_URL}/practitioners")
        passed = response.status_code == 200
        count = len(response.json()) if passed else 0
        log_test("참가자 목록 조회", passed, f"{count}명")
        return passed
    except Exception as e:
        log_test("참가자 목록 조회", False, str(e))
        return False

def test_get_submissions():
    """제출물 목록 조회"""
    try:
        response = requests.get(f"{BASE_URL}/submissions")
        passed = response.status_code == 200
        count = len(response.json()) if passed else 0
        log_test("제출물 목록 조회", passed, f"{count}개")
        return passed
    except Exception as e:
        log_test("제출물 목록 조회", False, str(e))
        return False

def test_get_submission_detail(submission_id):
    """제출물 상세 조회"""
    if not submission_id:
        log_test("제출물 상세 조회", False, "Submission ID 없음")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/submissions/{submission_id}")
        passed = response.status_code == 200
        log_test("제출물 상세 조회", passed, f"ID: {submission_id}")
        return passed
    except Exception as e:
        log_test("제출물 상세 조회", False, str(e))
        return False

# ============================================================================
# 시나리오 5: 데이터 수정
# ============================================================================

def test_update_task(task_id):
    """과제 수정"""
    if not task_id:
        log_test("과제 수정", False, "Task ID 없음")
        return False
    
    update_data = {
        "title": "수정된 과제 제목",
        "description": "수정된 설명"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/tasks/{task_id}", json=update_data)
        passed = response.status_code == 200
        log_test("과제 수정", passed, f"Task ID: {task_id}")
        return passed
    except Exception as e:
        log_test("과제 수정", False, str(e))
        return False

def test_update_practitioner(practitioner_id):
    """참가자 수정"""
    if not practitioner_id:
        log_test("참가자 수정", False, "Practitioner ID 없음")
        return False
    
    update_data = {
        "department": "수정된 부서",
        "position": "수정된 직급"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/practitioners/{practitioner_id}", json=update_data)
        passed = response.status_code == 200
        log_test("참가자 수정", passed, f"Practitioner ID: {practitioner_id}")
        return passed
    except Exception as e:
        log_test("참가자 수정", False, str(e))
        return False

def test_update_submission(submission_id):
    """제출물 수정"""
    if not submission_id:
        log_test("제출물 수정", False, "Submission ID 없음")
        return False
    
    update_data = {
        "prompt_text": "수정된 프롬프트: 더 자세한 지침을 추가함"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/submissions/{submission_id}", json=update_data)
        passed = response.status_code == 200
        log_test("제출물 수정", passed, f"Submission ID: {submission_id}")
        return passed
    except Exception as e:
        log_test("제출물 수정", False, str(e))
        return False

# ============================================================================
# 시나리오 6: 채점 시스템
# ============================================================================

def test_grade_submission_no_api_key(submission_id):
    """채점 실행 - API KEY 없음"""
    if not submission_id:
        log_test("채점 (API KEY 없음)", False, "Submission ID 없음")
        return False
    
    try:
        response = requests.post(f"{BASE_URL}/submissions/{submission_id}/grade")
        # API KEY가 없어도 요청은 받아들여야 함 (백그라운드에서 처리)
        passed = response.status_code == 200
        log_test("채점 (API KEY 없음)", passed, "백그라운드 작업 시작")
        return passed
    except Exception as e:
        log_test("채점 (API KEY 없음)", False, str(e))
        return False

def test_dashboard_empty_task(task_id):
    """대시보드 - 채점 전"""
    if not task_id:
        log_test("대시보드 (채점 전)", False, "Task ID 없음")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/tasks/{task_id}/dashboard")
        passed = response.status_code == 200
        data = response.json() if passed else {}
        log_test("대시보드 (채점 전)", passed, f"통계: {data.get('statistics', {})}")
        return passed
    except Exception as e:
        log_test("대시보드 (채점 전)", False, str(e))
        return False

# ============================================================================
# 시나리오 7: 데이터 삭제
# ============================================================================

def test_delete_submission(submission_id):
    """제출물 삭제"""
    if not submission_id:
        log_test("제출물 삭제", False, "Submission ID 없음")
        return False
    
    try:
        response = requests.delete(f"{BASE_URL}/submissions/{submission_id}")
        passed = response.status_code == 200
        log_test("제출물 삭제", passed, f"Submission ID: {submission_id}")
        return passed
    except Exception as e:
        log_test("제출물 삭제", False, str(e))
        return False

def test_delete_task_with_submissions(task_id):
    """과제 삭제 (제출물 포함)"""
    if not task_id:
        log_test("과제 삭제 (제출물 포함)", False, "Task ID 없음")
        return False
    
    try:
        response = requests.delete(f"{BASE_URL}/tasks/{task_id}")
        passed = response.status_code == 200
        log_test("과제 삭제 (제출물 포함)", passed, "연결된 제출물도 함께 삭제")
        return passed
    except Exception as e:
        log_test("과제 삭제 (제출물 포함)", False, str(e))
        return False

# ============================================================================
# 메인 테스트 실행
# ============================================================================

def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 70)
    print("완전한 사용자 경험 테스트 시작")
    print("=" * 70)
    print()
    
    # API 헬스 체크
    if not test_api_health():
        print("\n⚠️  API 서버가 실행되지 않았습니다. 테스트를 중단합니다.")
        return
    
    print("\n[1] 과제 생성 테스트")
    print("-" * 70)
    task_id_1 = test_create_task_normal()
    task_id_2 = test_create_task_long_text()
    task_id_3 = test_create_task_special_chars()
    test_create_task_missing_required()
    
    print("\n[2] 참가자 등록 테스트")
    print("-" * 70)
    practitioner_id_1 = test_create_practitioner_normal()
    test_create_practitioner_duplicate_email()
    test_create_practitioner_invalid_email()
    practitioner_id_2 = test_create_practitioner_optional_fields()
    
    print("\n[3] 제출물 등록 테스트")
    print("-" * 70)
    submission_id_1 = test_create_submission_normal(task_id_1, practitioner_id_1)
    submission_id_2 = test_create_submission_long_prompt(task_id_2, practitioner_id_2)
    test_create_submission_invalid_task()
    
    print("\n[4] 데이터 조회 테스트")
    print("-" * 70)
    test_get_tasks()
    test_get_practitioners()
    test_get_submissions()
    test_get_submission_detail(submission_id_1)
    
    print("\n[5] 데이터 수정 테스트")
    print("-" * 70)
    test_update_task(task_id_1)
    test_update_practitioner(practitioner_id_1)
    test_update_submission(submission_id_1)
    
    print("\n[6] 채점 시스템 테스트")
    print("-" * 70)
    test_grade_submission_no_api_key(submission_id_1)
    time.sleep(2)  # 백그라운드 작업 처리 대기
    test_dashboard_empty_task(task_id_1)
    
    print("\n[7] 데이터 삭제 테스트")
    print("-" * 70)
    test_delete_submission(submission_id_2)
    test_delete_task_with_submissions(task_id_3)
    
    # 결과 요약
    print("\n" + "=" * 70)
    print("테스트 결과 요약")
    print("=" * 70)
    
    total = len(TEST_RESULTS)
    passed = sum(1 for r in TEST_RESULTS if r["passed"])
    failed = total - passed
    
    print(f"총 테스트: {total}개")
    print(f"성공: {passed}개 (✅)")
    print(f"실패: {failed}개 (❌)")
    print(f"성공률: {passed/total*100:.1f}%")
    
    if failed > 0:
        print("\n실패한 테스트:")
        for result in TEST_RESULTS:
            if not result["passed"]:
                print(f"  ❌ {result['test']}")
                if result["details"]:
                    print(f"     └─ {result['details']}")
    
    # 결과 저장
    with open("test_results_full.json", "w", encoding="utf-8") as f:
        json.dump(TEST_RESULTS, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 테스트 결과 저장: test_results_full.json")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
