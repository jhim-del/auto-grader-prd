#!/usr/bin/env python3
"""
실제 데이터 기반 완전한 테스트
- 과제 3개 (Task A, B, C)
- 참가자 20명
- 제출물 60개 (20명 × 3개 과제)
- 파일 업로드 (PDF, Excel)
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

# 20명 참가자 (실무자 이름)
PRACTITIONERS = [
    "김민준", "이서윤", "박도윤", "최서준", "정하은",
    "강지우", "조유진", "윤서연", "임시우", "한예은",
    "오지훈", "신수아", "권민재", "황지원", "송현우",
    "고서영", "배준호", "홍다은", "노승현", "문채원"
]

print("=" * 70)
print("실제 데이터 기반 완전한 테스트 시작")
print("=" * 70)

# 1. 참가자 20명 등록
print("\n[1/6] 참가자 20명 등록 중...")
practitioner_ids = {}
for name in PRACTITIONERS:
    response = requests.post(f"{BASE_URL}/practitioners", json={"name": name})
    if response.status_code == 200:
        practitioner_ids[name] = response.json()["id"]
        print(f"  ✓ {name} 등록 완료 (ID: {practitioner_ids[name]})")
    else:
        print(f"  ✗ {name} 등록 실패: {response.text}")

print(f"\n✅ 총 {len(practitioner_ids)}명 등록 완료")

# 2. Task A: 경영 요약 보고서 생성
print("\n[2/6] Task A: 경영 요약 보고서 생성...")
task_a_input = """KPI 데이터:
- Revenue: $2.5M (전월 대비 +15%)
- New Signups: 1,234명 (전월 대비 +8%)
- MAU: 45,678명 (전월 대비 +12%)

하이라이트 메모:
- 신규 프로모션 캠페인 성공
- 모바일 앱 업데이트 후 사용자 증가
- 경쟁사 대비 성장률 우위"""

task_a_output = """# 경영 요약 보고서

## 주요 지표 분석
1. **매출 (Revenue)**
   - 현재: $2.5M
   - 전월 대비: +$326K (+15%)
   - 평가: 목표 대비 110% 달성

2. **신규 가입자 (New Signups)**
   - 현재: 1,234명
   - 전월 대비: +92명 (+8%)
   - 평가: 프로모션 효과 확인

3. **월간 활성 사용자 (MAU)**
   - 현재: 45,678명
   - 전월 대비: +4,893명 (+12%)
   - 평가: 모바일 앱 업데이트 기여

## 핵심 인사이트
1. 신규 프로모션 캠페인의 높은 ROI 확인
2. 모바일 경험 개선이 사용자 참여도 증대
3. 시장 점유율 확대 추세

## 주요 리스크
1. 프로모션 종료 후 이탈률 증가 가능성
2. 서버 용량 부족 우려 (MAU 급증)

## 권장 액션
1. 프로모션 연장 검토 (Q2 예산 배정)
2. 인프라 확장 계획 수립 (긴급)"""

response = requests.post(f"{BASE_URL}/tasks", json={
    "title": "Task A: 경영 요약 보고서 생성",
    "description": "KPI 데이터를 기반으로 경영진용 요약 보고서를 생성하세요.",
    "input_data": task_a_input,
    "golden_output": task_a_output,
    "evaluation_notes": "전월 대비 계산, 인사이트 3개, 리스크 2개, 액션 2개 포함 여부 확인"
})

if response.status_code == 200:
    task_a_id = response.json()["id"]
    print(f"  ✓ Task A 생성 완료 (ID: {task_a_id})")
else:
    print(f"  ✗ Task A 생성 실패: {response.text}")
    exit(1)

# 3. Task B: 고객 목록 정제 및 요약
print("\n[3/6] Task B: 고객 목록 정제 및 요약...")
task_b_input = """Excel 파일: task_b_input.xlsx
- 100건의 고객 데이터 (지저분한 형식)
- 중복, 오타, 빈 값 포함
- Plan: Free, Pro, Enterprise
- 정제 후 Plan별 요약표 생성 필요"""

task_b_output = """정제 결과: 93건 (중복 7건 제거)

Plan별 요약:
| Plan       | Count | Total Amount |
|------------|-------|--------------|
| Free       | 35    | ₩0           |
| Pro        | 42    | ₩4,158,000   |
| Enterprise | 16    | ₩4,784,000   |
| TOTAL      | 93    | ₩8,942,000   |

주요 정제 작업:
- 이메일 중복 제거
- 금액 형식 통일
- 날짜 형식 표준화
- Plan 대소문자 정규화"""

response = requests.post(f"{BASE_URL}/tasks", json={
    "title": "Task B: 고객 목록 정제 및 요약",
    "description": "Excel 파일의 지저분한 고객 데이터를 정제하고 Plan별 요약표를 생성하세요.",
    "input_data": task_b_input,
    "golden_output": task_b_output,
    "evaluation_notes": "중복 제거, Plan별 집계, 금액 합계 정확성 확인"
})

if response.status_code == 200:
    task_b_id = response.json()["id"]
    print(f"  ✓ Task B 생성 완료 (ID: {task_b_id})")
else:
    print(f"  ✗ Task B 생성 실패: {response.text}")
    exit(1)

# 4. Task C: 문서 정보 추출 및 충돌 식별
print("\n[4/6] Task C: 문서 정보 추출 및 충돌 식별...")
task_c_input = """PDF 파일: IT 시스템 접근 권한 관리 절차서
- 10개 정보 항목 추출 필요
- 권한 충돌 9개 식별"""

task_c_output = """## 추출된 정보 (10개 항목)

1. **문서 제목**: IT 시스템 접근 권한 관리 절차서
2. **발행일**: 2024-01-15
3. **담당 부서**: 정보보안팀
4. **권한 레벨**: Level 1~5 (5단계)
5. **승인 프로세스**: 부서장 → 보안담당 → 시스템관리자
6. **권한 유효기간**: 6개월 (자동 만료)
7. **재승인 기간**: 만료 30일 전
8. **긴급 권한**: 최대 24시간 (CTO 승인 필요)
9. **로그 보관**: 3년
10. **위반 시 조치**: 즉시 권한 회수 + 경고

## 권한 충돌 (9개)

1. 개발자 + 운영DB 읽기 권한 (분리 필요)
2. 외주 인력 + 고객 개인정보 접근 (금지)
3. 인턴 + 서버 관리자 권한 (과도한 권한)
4. 퇴사자 계정 미삭제 (3명)
5. Level 3 권한자가 Level 5 작업 수행 중
6. 승인 없이 권한 상승 (2건)
7. 6개월 초과 권한 (15명)
8. 감사 로그 미기록 계정 (5개)
9. 부서 이동 후 권한 미조정 (8명)"""

response = requests.post(f"{BASE_URL}/tasks", json={
    "title": "Task C: 문서 정보 추출 및 충돌 식별",
    "description": "PDF 문서에서 10개 정보 항목을 추출하고 9개 권한 충돌을 식별하세요.",
    "input_data": task_c_input,
    "golden_output": task_c_output,
    "evaluation_notes": "정보 항목 10개, 충돌 9개 정확히 식별 여부 확인"
})

if response.status_code == 200:
    task_c_id = response.json()["id"]
    print(f"  ✓ Task C 생성 완료 (ID: {task_c_id})")
else:
    print(f"  ✗ Task C 생성 실패: {response.text}")
    exit(1)

# 5. 제출물 60개 생성 (20명 × 3개 과제)
print("\n[5/6] 제출물 60개 생성 중...")

task_ids = [task_a_id, task_b_id, task_c_id]
task_names = ["Task A", "Task B", "Task C"]

# 각 참가자별 프롬프트 (다양성 확보)
prompt_templates = {
    "Task A": [
        "KPI 데이터를 분석하여 경영진용 요약 보고서를 작성해주세요.",
        "주어진 지표를 바탕으로 전월 대비 변화를 분석하고 인사이트를 도출하세요.",
        "매출, 가입자, 활성 사용자 데이터를 종합하여 경영 보고서를 생성하세요.",
        "KPI 분석 결과를 기반으로 리스크와 권장 액션을 포함한 보고서를 작성하세요."
    ],
    "Task B": [
        "Excel 파일의 고객 데이터를 정제하고 Plan별 요약표를 만들어주세요.",
        "중복 제거 및 데이터 정규화 후 Plan별 통계를 생성하세요.",
        "고객 목록에서 오류를 수정하고 Plan별 집계를 수행하세요.",
        "데이터 품질을 개선하고 Plan별 금액 합계를 계산하세요."
    ],
    "Task C": [
        "PDF 문서에서 10개 정보 항목을 추출하고 9개 권한 충돌을 식별하세요.",
        "접근 권한 관리 문서를 분석하여 핵심 정보와 보안 이슈를 도출하세요.",
        "문서 내용을 파싱하여 정보 항목과 권한 충돌 사항을 리스트업하세요.",
        "IT 시스템 권한 관리 절차와 현재 충돌 상황을 정리하세요."
    ]
}

submission_count = 0
for i, name in enumerate(PRACTITIONERS):
    prac_id = practitioner_ids[name]
    
    for j, task_id in enumerate(task_ids):
        task_name = task_names[j]
        prompt_idx = i % len(prompt_templates[task_name])
        prompt = prompt_templates[task_name][prompt_idx]
        
        response = requests.post(f"{BASE_URL}/submissions", json={
            "task_id": task_id,
            "practitioner_id": prac_id,
            "prompt_text": prompt
        })
        
        if response.status_code == 200:
            submission_count += 1
            if submission_count % 10 == 0:
                print(f"  진행중... {submission_count}/60")
        else:
            print(f"  ✗ {name} - {task_name} 제출 실패")

print(f"\n✅ 총 {submission_count}개 제출물 생성 완료")

# 6. 검증
print("\n[6/6] 최종 검증 중...")

# 과제 수 확인
response = requests.get(f"{BASE_URL}/tasks")
tasks = response.json()
print(f"  ✓ 과제: {len(tasks)}개")

# 참가자 수 확인
response = requests.get(f"{BASE_URL}/practitioners")
practitioners = response.json()
print(f"  ✓ 참가자: {len(practitioners)}명")

# 제출물 수 확인
response = requests.get(f"{BASE_URL}/submissions")
submissions = response.json()
print(f"  ✓ 제출물: {len(submissions)}개")

print("\n" + "=" * 70)
print("실제 데이터 기반 테스트 완료")
print("=" * 70)
print(f"✅ 과제: {len(tasks)}개")
print(f"✅ 참가자: {len(practitioners)}명")
print(f"✅ 제출물: {len(submissions)}개")
print(f"✅ 배치: {len(practitioners)} × {len(tasks)} = {len(submissions)}")
print("=" * 70)

