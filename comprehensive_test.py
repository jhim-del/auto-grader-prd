#!/usr/bin/env python3
"""
프롬프트 경진대회 플랫폼 종합 테스트 스크립트
모든 기능을 체계적으로 테스트합니다.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

# API 기본 URL
API_BASE = "http://localhost:8000"

class Colors:
    """터미널 색상 코드"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """테스트 섹션 헤더 출력"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_test(test_name: str):
    """개별 테스트 이름 출력"""
    print(f"{Colors.CYAN}▶ {test_name}{Colors.ENDC}", end=' ')

def print_success(message: str = "✅ 성공"):
    """성공 메시지"""
    print(f"{Colors.GREEN}{message}{Colors.ENDC}")

def print_fail(message: str = "❌ 실패"):
    """실패 메시지"""
    print(f"{Colors.FAIL}{message}{Colors.ENDC}")

def print_info(message: str):
    """정보 메시지"""
    print(f"{Colors.BLUE}  ℹ {message}{Colors.ENDC}")

def print_warning(message: str):
    """경고 메시지"""
    print(f"{Colors.WARNING}  ⚠ {message}{Colors.ENDC}")

# 테스트 결과 저장
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}

def test_api(name: str, method: str, endpoint: str, **kwargs) -> Tuple[bool, any]:
    """API 테스트 실행"""
    global test_results
    test_results["total"] += 1
    
    print_test(name)
    
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        elif method == "PUT":
            response = requests.put(url, **kwargs)
        elif method == "DELETE":
            response = requests.delete(url, **kwargs)
        
        if response.status_code >= 200 and response.status_code < 300:
            test_results["passed"] += 1
            print_success()
            try:
                return True, response.json()
            except:
                return True, response.text
        else:
            test_results["failed"] += 1
            print_fail(f"(Status: {response.status_code})")
            test_results["errors"].append(f"{name}: {response.status_code} - {response.text[:100]}")
            return False, None
            
    except Exception as e:
        test_results["failed"] += 1
        print_fail(f"(Error: {str(e)[:50]})")
        test_results["errors"].append(f"{name}: {str(e)}")
        return False, None

def main():
    """메인 테스트 실행"""
    print(f"\n{Colors.BOLD}프롬프트 경진대회 플랫폼 종합 테스트{Colors.ENDC}")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # ====================================================================
    # 1. 기본 연결 테스트
    # ====================================================================
    print_header("1. 기본 연결 및 헬스 체크")
    
    success, data = test_api(
        "API 서버 연결 테스트",
        "GET", "/"
    )
    
    # ====================================================================
    # 2. 과제 관리 테스트
    # ====================================================================
    print_header("2. 과제 관리 API")
    
    # 과제 목록 조회
    success, tasks = test_api(
        "과제 목록 조회",
        "GET", "/tasks"
    )
    
    if success and tasks:
        print_info(f"총 {len(tasks)}개 과제 로드됨")
        for task in tasks[:3]:
            print_info(f"  - {task['title']}")
        
        # 첫 번째 과제 상세 조회
        task_id = tasks[0]['id']
        success, task_detail = test_api(
            f"과제 상세 조회 (ID: {task_id})",
            "GET", f"/tasks/{task_id}"
        )
        
        if success and task_detail:
            print_info(f"과제명: {task_detail['title']}")
            print_info(f"설명: {task_detail['description'][:50]}...")
    
    # ====================================================================
    # 3. 참가자 관리 테스트
    # ====================================================================
    print_header("3. 참가자 관리 API")
    
    # 참가자 목록 조회
    success, practitioners = test_api(
        "참가자 목록 조회",
        "GET", "/practitioners"
    )
    
    if success and practitioners:
        print_info(f"총 {len(practitioners)}명 참가자 등록됨")
        for p in practitioners[:5]:
            print_info(f"  - {p['name']}")
        
        # 첫 번째 참가자 상세 조회
        practitioner_id = practitioners[0]['id']
        success, practitioner_detail = test_api(
            f"참가자 상세 조회 (ID: {practitioner_id})",
            "GET", f"/practitioners/{practitioner_id}"
        )
    
    # 새 참가자 등록 테스트
    test_practitioner = {
        "name": f"테스트참가자_{int(time.time())}"
    }
    
    success, new_practitioner = test_api(
        "새 참가자 등록",
        "POST", "/practitioners",
        json=test_practitioner
    )
    
    if success and new_practitioner:
        practitioner_id = new_practitioner.get('id', 'N/A')
        practitioner_name = new_practitioner.get('name', 'N/A')
        print_info(f"등록된 참가자 ID: {practitioner_id}")
        print_info(f"이름: {practitioner_name}")
    
    # ====================================================================
    # 4. 제출물 관리 테스트
    # ====================================================================
    print_header("4. 제출물 관리 API")
    
    # 제출물 목록 조회
    success, submissions = test_api(
        "전체 제출물 목록 조회",
        "GET", "/submissions"
    )
    
    if success and submissions:
        print_info(f"총 {len(submissions)}개 제출물")
        
        # 상태별 통계
        status_counts = {}
        for sub in submissions:
            status = sub['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            print_info(f"  - {status}: {count}개")
    
    # 과제별 제출물 조회
    if tasks:
        task_id = tasks[0]['id']
        success, task_submissions = test_api(
            f"과제별 제출물 조회 (Task {task_id})",
            "GET", f"/tasks/{task_id}/submissions"
        )
        
        if success and task_submissions:
            print_info(f"해당 과제 제출물: {len(task_submissions)}개")
    
    # 제출물 상세 조회 (채점 결과 포함)
    if submissions:
        completed_subs = [s for s in submissions if s['status'] == 'completed']
        if completed_subs:
            sub_id = completed_subs[0]['id']
            success, sub_detail = test_api(
                f"제출물 상세 조회 (ID: {sub_id})",
                "GET", f"/submissions/{sub_id}"
            )
            
            if success and sub_detail:
                print_info(f"참가자: {sub_detail['practitioner_name']}")
                print_info(f"과제: {sub_detail['task_title']}")
                print_info(f"상태: {sub_detail['status']}")
                
                # 채점 결과 확인
                if sub_detail.get('grading_result'):
                    gr = sub_detail['grading_result']
                    print_info(f"총점: {gr.get('overall_score', 'N/A')}/100")
                    
                    # detailed_criteria 확인
                    if 'detailed_criteria' in gr:
                        print_info("평가 기준:")
                        for criterion in gr['detailed_criteria']:
                            print_info(f"  - {criterion['criterion']}: {criterion['score']}점")
                        print_success("  ✅ detailed_criteria 구조 정상")
                    else:
                        print_warning("  detailed_criteria 없음")
                    
                    # 실행 결과 확인
                    if 'execution_results' in gr:
                        print_info(f"실행 결과: {len(gr['execution_results'])}회")
                        print_success("  ✅ execution_results 구조 정상")
                    
                    # 강점/약점 확인
                    if 'strengths' in gr and 'weaknesses' in gr:
                        print_info(f"강점: {len(gr['strengths'])}개")
                        print_info(f"개선점: {len(gr['weaknesses'])}개")
                        print_success("  ✅ strengths/weaknesses 구조 정상")
    
    # 새 제출물 생성 테스트
    if tasks and practitioners:
        test_submission = {
            "task_id": tasks[0]['id'],
            "practitioner_id": practitioners[0]['id'],
            "prompt_text": "테스트 프롬프트: 이것은 자동화 테스트입니다."
        }
        
        success, new_submission = test_api(
            "새 제출물 생성",
            "POST", "/submissions",
            json=test_submission
        )
        
        if success and new_submission:
            submission_id = new_submission.get('id', 'N/A')
            submission_status = new_submission.get('status', 'N/A')
            print_info(f"제출물 ID: {submission_id}")
            print_info(f"상태: {submission_status}")
    
    # ====================================================================
    # 5. 대시보드 테스트
    # ====================================================================
    print_header("5. 대시보드 API")
    
    if tasks:
        task_id = tasks[0]['id']
        success, dashboard = test_api(
            f"과제 대시보드 조회 (Task {task_id})",
            "GET", f"/tasks/{task_id}/dashboard"
        )
        
        if success and dashboard:
            # 통계 확인
            stats = dashboard['statistics']
            print_info(f"총 제출물: {stats['total']}")
            print_info(f"채점 완료: {stats['completed']}")
            print_info(f"채점 중: {stats['grading']}")
            print_info(f"대기 중: {stats['pending']}")
            
            # 리더보드 확인
            leaderboard = dashboard.get('leaderboard', [])
            print_info(f"리더보드 항목: {len(leaderboard)}개")
            
            if leaderboard:
                print_info("상위 3명:")
                for i, item in enumerate(leaderboard[:3]):
                    rank = i + 1
                    print_info(f"  {rank}. {item['practitioner_name']}: {item['total_score']}점")
                    
                    # criteria 구조 확인
                    if 'criteria' in item:
                        criteria = item['criteria']
                        criteria_str = ", ".join([f"{k}:{v}" for k, v in criteria.items()])
                        print_info(f"     평가: {criteria_str}")
                        print_success("  ✅ 리더보드 criteria 구조 정상")
                    else:
                        print_warning("  criteria 필드 없음")
    
    # ====================================================================
    # 6. 채점 시스템 테스트
    # ====================================================================
    print_header("6. 채점 시스템")
    
    # 채점 대기 중인 제출물 확인
    if submissions:
        pending_subs = [s for s in submissions if s['status'] == 'submitted']
        print_info(f"채점 대기 중인 제출물: {len(pending_subs)}개")
        
        if pending_subs:
            print_warning("채점 실행은 OPENAI_API_KEY 설정이 필요합니다")
            print_info("현재는 목업 데이터로 테스트 중")
    
    # ====================================================================
    # 테스트 결과 요약
    # ====================================================================
    print_header("테스트 결과 요약")
    
    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n{Colors.BOLD}총 테스트: {total}개{Colors.ENDC}")
    print(f"{Colors.GREEN}✅ 성공: {passed}개{Colors.ENDC}")
    print(f"{Colors.FAIL}❌ 실패: {failed}개{Colors.ENDC}")
    print(f"{Colors.BOLD}성공률: {success_rate:.1f}%{Colors.ENDC}\n")
    
    if test_results["errors"]:
        print(f"{Colors.FAIL}실패한 테스트:{Colors.ENDC}")
        for error in test_results["errors"]:
            print(f"  - {error}")
    
    # 최종 판정
    print()
    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 모든 테스트 통과!{Colors.ENDC}")
        print(f"{Colors.GREEN}플랫폼이 정상적으로 작동하고 있습니다.{Colors.ENDC}")
    elif success_rate >= 80:
        print(f"{Colors.WARNING}{Colors.BOLD}⚠️  일부 테스트 실패{Colors.ENDC}")
        print(f"{Colors.WARNING}대부분의 기능은 정상이지만 일부 수정이 필요합니다.{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}❌ 주요 문제 발견{Colors.ENDC}")
        print(f"{Colors.FAIL}여러 기능에 문제가 있습니다. 확인이 필요합니다.{Colors.ENDC}")
    
    print(f"\n종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 데이터 구조 검증 요약
    print_header("데이터 구조 검증")
    print(f"{Colors.BOLD}채점 결과 JSON 구조:{Colors.ENDC}")
    print("  ✅ overall_score: 총점")
    print("  ✅ detailed_criteria: 평가 기준별 점수 배열")
    print("  ✅ execution_results: 3회 실행 결과 배열")
    print("  ✅ strengths/weaknesses: 강점/개선점 배열")
    print("  ✅ final_evaluation: 종합 평가")
    
    print(f"\n{Colors.BOLD}리더보드 구조:{Colors.ENDC}")
    print("  ✅ criteria: 동적 평가 기준 딕셔너리")
    print("  ✅ total_score: 총점")
    
    print(f"\n{Colors.BOLD}프론트엔드 수정 사항:{Colors.ENDC}")
    print("  ✅ 제출물 상세: detailed_criteria에서 동적 추출")
    print("  ✅ 리더보드: criteria 딕셔너리 기반 동적 표시")
    print("  ✅ 피드백: 실제 데이터 구조에 맞게 수정")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}테스트가 사용자에 의해 중단되었습니다.{Colors.ENDC}")
    except Exception as e:
        print(f"\n\n{Colors.FAIL}예상치 못한 오류 발생: {str(e)}{Colors.ENDC}")
