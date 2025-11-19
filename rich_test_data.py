"""
풍부한 더미 데이터 생성 스크립트
- 다양한 참가자 프롬프트 (초보자 ~ 전문가)
- 실제 파일 첨부 시나리오
- 실제 GPT 채점 (OPENAI_API_KEY 있으면)
"""

import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "http://localhost:8001"

# 실제 참가자 이름 (20명)
PARTICIPANTS = [
    "김민준", "이서윤", "박도윤", "최서준", "정하은",
    "강지우", "조유진", "윤서연", "임시우", "한예은",
    "오지훈", "신수아", "권민재", "황지원", "송현우",
    "고서영", "배준호", "홍다은", "노승현", "문채원"
]

# Task A 프롬프트 (경영 요약 보고서 - 난이도별)
TASK_A_PROMPTS = {
    "초보자": [
        # 기본적인 요청만
        "KPI 데이터를 분석해서 보고서를 작성해주세요.",
        "위 데이터로 경영진에게 보고할 내용을 만들어주세요.",
        "매출과 사용자 증가율을 요약해주세요.",
    ],
    "중급자": [
        # 구조화된 지시사항
        """너는 경영 분석 전문가야.
        
다음 KPI 데이터를 분석하여 경영진용 요약 보고서를 작성해줘:
1. 주요 지표 분석 (전월 대비 증감률 계산 포함)
2. 핵심 인사이트 3개 도출
3. 주요 리스크 2개 식별
4. 권장 액션 아이템 2개 제시""",
        
        """당신은 데이터 분석가입니다.
        
아래 KPI 데이터를 기반으로 경영 요약 보고서를 작성하세요:
- Revenue, New Signups, MAU 각각 분석
- 전월 대비 변화율 계산 및 해석
- 비즈니스 인사이트 도출
- 리스크 요소 파악""",
    ],
    "전문가": [
        # 상세한 역할, 단계, 검증 기준
        """# 역할
너는 20년 경력의 경영 컨설턴트이며, 데이터 기반 의사결정을 전문으로 하는 전문가야.

# 과제
제공된 KPI 데이터를 분석하여 CEO와 CFO를 위한 경영 요약 보고서를 작성해줘.

# 분석 단계
1. **정량적 분석**
   - 각 KPI의 절대값 및 전월 대비 증감률 계산
   - MoM, YoY 성장률 추정
   - 핵심 지표 간 상관관계 분석

2. **정성적 분석**
   - 하이라이트 메모를 기반으로 성장 요인 파악
   - 시장 트렌드와의 연관성 분석
   - 경쟁사 대비 포지션 평가

3. **인사이트 도출**
   - 3가지 핵심 인사이트 (데이터 기반 근거 포함)
   - 각 인사이트의 비즈니스 임팩트 정량화

4. **리스크 관리**
   - 2가지 주요 리스크 식별
   - 각 리스크의 발생 가능성 및 영향도 평가

5. **액션 플랜**
   - 2가지 권장 액션 (우선순위, 예상 비용, 타임라인 포함)

# 출력 형식
- 마크다운 형식
- 섹션별 헤더 사용
- 표, 리스트로 가독성 확보
- 각 주장에 대한 데이터 근거 명시

# 제약사항
- 보고서 길이: 500~800단어
- 전문 용어 사용 시 간단한 설명 첨부
- CEO/CFO가 5분 내 읽을 수 있도록 간결하게""",

        """You are an expert business analyst with MBA and 15 years of experience in SaaS metrics analysis.

**Task:** Create an executive summary report for C-level stakeholders.

**Analysis Framework:**

1. **Metrics Deep Dive**
   - Calculate month-over-month growth rates for all KPIs
   - Identify trends and patterns
   - Benchmark against industry standards (if applicable)

2. **Root Cause Analysis**
   - Analyze the "Highlight Memo" to understand drivers
   - Connect quantitative metrics to qualitative insights
   - Identify causal relationships

3. **Strategic Insights (minimum 3)**
   - Each insight must include:
     * Clear statement
     * Data-driven evidence
     * Business impact assessment
     * Recommended action

4. **Risk Assessment (minimum 2)**
   - Identify potential threats
   - Evaluate probability and impact
   - Suggest mitigation strategies

5. **Action Items (minimum 2)**
   - Prioritized recommendations
   - Expected outcomes
   - Resource requirements
   - Timeline estimation

**Output Format:**
- Use clear markdown structure
- Include tables for numerical data
- Bullet points for key takeaways
- Professional and concise language

**Quality Criteria:**
- Accuracy: All calculations must be correct
- Clarity: Avoid jargon; explain complex concepts
- Actionability: Every insight should lead to a decision
- Brevity: Maximum 800 words""",
    ]
}

# Task B 프롬프트 (Excel 데이터 정제)
TASK_B_PROMPTS = {
    "초보자": [
        "Excel 파일의 고객 데이터를 정리해주세요.",
        "중복된 데이터를 제거하고 깨끗하게 만들어주세요.",
    ],
    "중급자": [
        """너는 데이터 정제 전문가야.

다음 작업을 수행해줘:
1. 이메일 주소 기준으로 중복 제거
2. Plan 컬럼을 'Free', 'Pro', 'Enterprise'로 정규화
3. Amount 컬럼의 숫자 형식 통일
4. Plan별 요약 통계 생성 (개수, 총액)""",

        """당신은 데이터 애널리스트입니다.

Excel 파일의 고객 데이터를 정제하세요:
- 중복 레코드 식별 및 제거 (이메일 기준)
- 데이터 타입 통일 (날짜, 금액, 텍스트)
- Plan 필드 정규화 (대소문자, 공백 처리)
- Plan별 집계 및 요약표 생성""",
    ],
    "전문가": [
        """# 역할
너는 10년 경력의 데이터 엔지니어이며, ETL 파이프라인 설계 및 데이터 품질 관리 전문가야.

# 과제
Excel 파일의 지저분한 고객 데이터를 정제하고, Plan별 요약 분석을 수행해줘.

# 데이터 정제 절차

1. **중복 제거**
   - Primary Key: email 컬럼
   - 중복 발견 시: 최신 레코드 유지 (created_at 기준)
   - 제거된 레코드 수 보고

2. **데이터 검증**
   - 이메일: 정규식 검증 (invalid 제거)
   - Plan: {'Free', 'Pro', 'Enterprise'} 중 하나로 정규화
   - Amount: 숫자 변환, 통화 기호 제거, NULL 처리
   - 날짜: ISO 8601 형식으로 통일

3. **결측치 처리**
   - Amount NULL → 0으로 대체 (Free plan인 경우)
   - Plan NULL → 'Free'로 기본값 설정
   - 기타 필수 컬럼 NULL → 레코드 제외

4. **Plan별 집계**
   | Plan       | Count | Total Amount | Avg Amount |
   |------------|-------|--------------|------------|
   | Free       | ?     | ₩?           | ₩?         |
   | Pro        | ?     | ₩?           | ₩?         |
   | Enterprise | ?     | ₩?           | ₩?         |
   | **TOTAL**  | ?     | ₩?           | ₩?         |

# 출력 형식
- 정제 프로세스 로그
- 최종 데이터 품질 리포트
- Plan별 요약 통계 (마크다운 표)

# 품질 기준
- 중복 제거율 100%
- 데이터 타입 일관성 100%
- 집계 정확도 100%""",
    ]
}

# Task C 프롬프트 (PDF 정보 추출)
TASK_C_PROMPTS = {
    "초보자": [
        "PDF에서 중요한 정보 10개를 찾아주세요.",
        "권한 충돌이 있는지 확인해주세요.",
    ],
    "중급자": [
        """너는 문서 분석 전문가야.

PDF 문서를 분석하여:
1. 10개 핵심 정보 항목 추출
2. 권한 충돌 9개 식별
3. 각 충돌에 대한 보안 위험도 평가""",

        """당신은 정보보안 감사관입니다.

IT 권한 관리 문서를 분석하세요:
- 문서에서 10개 메타 정보 추출
- 권한 충돌 9개 식별 및 설명
- 보안 권고사항 제시""",
    ],
    "전문가": [
        """# 역할
너는 CISSP 자격증을 보유한 정보보안 전문가이며, 15년간 접근 제어 및 권한 관리를 담당한 베테랑이야.

# 과제
IT 시스템 접근 권한 관리 절차서(PDF)를 분석하여, 문서 정보 추출 및 권한 충돌 감사를 수행해줘.

# 분석 프레임워크

## Part 1: 문서 메타정보 추출 (10개 항목)
1. 문서 제목 및 버전
2. 발행일 및 유효기간
3. 담당 부서 및 승인자
4. 권한 레벨 체계
5. 승인 프로세스 플로우
6. 권한 유효기간 정책
7. 재승인 절차
8. 긴급 권한 발급 규정
9. 로그 및 감사 정책
10. 위반 시 조치 사항

## Part 2: 권한 충돌 감사 (9개 충돌 식별)

**Segregation of Duties (SoD) 원칙 기반 분석:**

1. **개발자 + 운영 DB 접근**
   - 리스크: 프로덕션 데이터 무단 수정
   - 심각도: High
   
2. **외주 인력 + 민감 정보 접근**
   - 리스크: 데이터 유출
   - 심각도: Critical

3. **권한 상승 (Privilege Escalation)**
   - 승인 없는 권한 증가 사례
   - 심각도: High

4. **만료된 권한 (Stale Permissions)**
   - 6개월 초과 권한 보유자
   - 심각도: Medium

5. **Orphaned Accounts**
   - 퇴사자 미삭제 계정
   - 심각도: Critical

6. **과도한 권한 (Excessive Permissions)**
   - 직무에 비해 불필요한 높은 권한
   - 심각도: Medium

7. **감사 로그 부재**
   - 로그 기록이 없는 계정
   - 심각도: High

8. **부서 이동 미반영**
   - 조직 변경 후 권한 미조정
   - 심각도: Medium

9. **공유 계정 (Shared Credentials)**
   - 개인 식별 불가능한 계정
   - 심각도: High

# 출력 형식

## 추출된 정보 (10개 항목)
1. **문서 제목**: ...
2. **발행일**: ...
...

## 권한 충돌 (9개)
### 1. 충돌 유형: ...
- **발견 위치**: ...
- **리스크**: ...
- **심각도**: Critical/High/Medium
- **권고사항**: ...

# 품질 기준
- 정보 추출 정확도: 100%
- 충돌 식별 완전성: 9/9
- 보안 심각도 평가의 타당성""",
    ]
}


def create_participant(name):
    """참가자 등록"""
    response = requests.post(
        f"{BASE_URL}/practitioners",
        json={"name": name}
    )
    return response.json()


def create_task_with_files(task_id, title, description, input_data, golden_output, eval_notes):
    """과제 생성 (파일 포함)"""
    response = requests.post(
        f"{BASE_URL}/tasks",
        json={
            "title": title,
            "description": description,
            "input_data": input_data,
            "golden_output": golden_output,
            "evaluation_notes": eval_notes
        }
    )
    return response.json()


def submit_prompt(practitioner_id, task_id, prompt_text):
    """프롬프트 제출"""
    response = requests.post(
        f"{BASE_URL}/submissions",
        json={
            "practitioner_id": practitioner_id,
            "task_id": task_id,
            "prompt_text": prompt_text
        }
    )
    return response.json()


def grade_all_submissions(task_id):
    """과제의 모든 제출물 채점"""
    response = requests.post(f"{BASE_URL}/tasks/{task_id}/grade_all")
    return response.json()


def main():
    print("=" * 70)
    print("풍부한 더미 데이터 생성 시작")
    print("=" * 70)
    
    # 1. 참가자 등록 (20명)
    print("\n[1/4] 참가자 20명 등록 중...")
    participants = []
    for name in PARTICIPANTS:
        p = create_participant(name)
        participants.append(p)
        print(f"  ✓ {name} 등록 완료 (ID: {p['id']})")
    
    # 2. 과제 생성 (실제 데이터)
    print("\n[2/4] 과제 3개 생성 중...")
    
    # Task A
    task_a = create_task_with_files(
        task_id=None,
        title="Task A: 경영 요약 보고서 생성",
        description="KPI 데이터를 기반으로 경영진용 요약 보고서를 생성하세요.",
        input_data="""KPI 데이터:
- Revenue: $2.5M (전월 대비 +15%)
- New Signups: 1,234명 (전월 대비 +8%)
- MAU: 45,678명 (전월 대비 +12%)

하이라이트 메모:
- 신규 프로모션 캠페인 성공
- 모바일 앱 업데이트 후 사용자 증가
- 경쟁사 대비 성장률 우위""",
        golden_output="""# 경영 요약 보고서

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
2. 인프라 확장 계획 수립 (긴급)""",
        eval_notes="전월 대비 계산, 인사이트 3개, 리스크 2개, 액션 2개 포함 여부 확인"
    )
    print(f"  ✓ Task A 생성 완료 (ID: {task_a['id']})")
    
    # Task B
    task_b = create_task_with_files(
        task_id=None,
        title="Task B: 고객 목록 정제 및 요약",
        description="Excel 파일의 지저분한 고객 데이터를 정제하고 Plan별 요약표를 생성하세요.",
        input_data="""Excel 파일: task_b_input.xlsx
- 100건의 고객 데이터 (지저분한 형식)
- 중복, 오타, 빈 값 포함
- Plan: Free, Pro, Enterprise
- 정제 후 Plan별 요약표 생성 필요""",
        golden_output="""정제 결과: 93건 (중복 7건 제거)

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
- Plan 대소문자 정규화""",
        eval_notes="중복 제거, Plan별 집계, 금액 합계 정확성 확인"
    )
    print(f"  ✓ Task B 생성 완료 (ID: {task_b['id']})")
    
    # Task C
    task_c = create_task_with_files(
        task_id=None,
        title="Task C: 문서 정보 추출 및 충돌 식별",
        description="PDF 문서에서 10개 정보 항목을 추출하고 9개 권한 충돌을 식별하세요.",
        input_data="""PDF 파일: IT 시스템 접근 권한 관리 절차서
- 10개 정보 항목 추출 필요
- 권한 충돌 9개 식별""",
        golden_output="""## 추출된 정보 (10개 항목)

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
9. 부서 이동 후 권한 미조정 (8명)""",
        eval_notes="정보 항목 10개, 충돌 9개 정확히 식별 여부 확인"
    )
    print(f"  ✓ Task C 생성 완료 (ID: {task_c['id']})")
    
    # 3. 제출물 생성 (다양한 난이도)
    print("\n[3/4] 제출물 60개 생성 중 (다양한 프롬프트)...")
    
    tasks = [
        (task_a['id'], "A", TASK_A_PROMPTS),
        (task_b['id'], "B", TASK_B_PROMPTS),
        (task_c['id'], "C", TASK_C_PROMPTS)
    ]
    
    submission_count = 0
    for task_id, task_name, prompts_dict in tasks:
        # 각 과제마다 20명이 제출
        for i, participant in enumerate(participants):
            # 난이도 분배 (초보자:중급자:전문가 = 8:7:5)
            if i < 8:
                level = "초보자"
                prompt_list = prompts_dict[level]
                prompt = prompt_list[i % len(prompt_list)]
            elif i < 15:
                level = "중급자"
                prompt_list = prompts_dict[level]
                prompt = prompt_list[(i - 8) % len(prompt_list)]
            else:
                level = "전문가"
                prompt_list = prompts_dict[level]
                prompt = prompt_list[(i - 15) % len(prompt_list)]
            
            # 제출
            submit_prompt(participant['id'], task_id, prompt)
            submission_count += 1
            
            if submission_count % 10 == 0:
                print(f"  진행중... {submission_count}/60")
    
    print(f"\n✅ 총 {submission_count}개 제출물 생성 완료")
    
    # 4. 채점 실행
    print("\n[4/4] 채점 실행 중...")
    has_openai_key = os.environ.get("OPENAI_API_KEY") is not None
    
    if has_openai_key:
        print("  ✓ OPENAI_API_KEY 감지 - 실제 GPT 채점 진행")
        for task_id, task_name, _ in tasks:
            result = grade_all_submissions(task_id)
            print(f"  ✓ Task {task_name} 채점 시작: {result['message']}")
            time.sleep(3)  # API rate limit
    else:
        print("  ⚠️  OPENAI_API_KEY 없음 - 목업 채점 스크립트 사용 필요")
        print("  → python mock_grading.py 실행하여 채점 완료")
    
    print("\n" + "=" * 70)
    print("✅ 풍부한 더미 데이터 생성 완료")
    print("=" * 70)
    print(f"참가자: {len(participants)}명")
    print(f"과제: 3개 (Task A, B, C)")
    print(f"제출물: {submission_count}개 (초보자/중급자/전문가 혼합)")
    print(f"채점 방식: {'실제 GPT 채점' if has_openai_key else '목업 데이터 (mock_grading.py 실행 필요)'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
