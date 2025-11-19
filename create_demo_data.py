#!/usr/bin/env python3
"""
PRD 준수 시연 데이터 생성 스크립트
- 실무자 참가자 (부서/직급 포함)
- Task A, B, C (PRD 기반 과제)
- 4가지 입력 요소 포함
"""

import requests
import os
from io import BytesIO
import zipfile

# API_BASE = "https://auto-grader-backend-production.up.railway.app"
API_BASE = "http://localhost:8000"  # 로컬 테스트

# 실무자 참가자 데이터
PARTICIPANTS = [
    {"id": 1, "name": "김민준", "email": "kim.minjun@company.com", "department": "전략기획팀", "position": "과장"},
    {"id": 2, "name": "이서연", "email": "lee.seoyeon@company.com", "department": "마케팅팀", "position": "대리"},
    {"id": 3, "name": "박지호", "email": "park.jiho@company.com", "department": "데이터분석팀", "position": "차장"},
    {"id": 4, "name": "최유진", "email": "choi.yujin@company.com", "department": "인사팀", "position": "사원"},
    {"id": 5, "name": "정하은", "email": "jung.haeun@company.com", "department": "재무팀", "position": "부장"},
]

# 과제별 요구사항 및 정답
ASSIGNMENTS = {
    "TaskA": {
        "name": "TaskA",
        "description": "경영 보고서 작성: 분기별 매출 데이터를 분석하여 3가지 핵심 인사이트를 도출하세요.",
        "requirements": """
        평가 기준:
        1. 데이터에 기반한 구체적인 인사이트 3개 이상
        2. 각 인사이트에 대한 정량적 근거 제시 (백분율, 금액 등)
        3. 명확하고 간결한 문장 구조
        4. 비즈니스 의사결정에 활용 가능한 수준의 분석
        """,
        "input_data": """
        [2024년 분기별 매출 데이터]
        Q1 매출: 100억원 (전년 동기 대비 +10%)
        Q2 매출: 120억원 (전년 동기 대비 +15%)
        Q3 매출: 150억원 (전년 동기 대비 +25%)
        Q4 매출: 180억원 (전년 동기 대비 +20%)
        
        [제품별 매출 비중 (Q4 기준)]
        - 제품 A: 90억원 (50%)
        - 제품 B: 54억원 (30%)
        - 제품 C: 36억원 (20%)
        """,
        "golden_output": """
        # 2024년 매출 분석 보고서
        
        ## 핵심 인사이트
        
        ### 1. 지속적인 성장세 달성
        2024년 연간 매출은 550억원으로, 전년 대비 17.5% 성장했습니다. 특히 하반기(Q3-Q4)에 매출 가속화가 두드러지며, Q3는 전년 동기 대비 25%로 가장 높은 성장률을 기록했습니다.
        
        ### 2. 분기별 매출 증가 가속화
        분기별 매출 증가율을 보면 Q1→Q2: 20억원(20%), Q2→Q3: 30억원(25%), Q3→Q4: 30억원(20%)로 증가폭이 Q3에 최고점을 기록한 후 안정화되었습니다.
        
        ### 3. 제품 A 의존도 관리 필요
        Q4 기준 제품 A가 전체 매출의 50%를 차지하고 있어, 특정 제품에 대한 의존도가 높습니다. 제품 B(30%)와 제품 C(20%)의 성장을 통한 포트폴리오 다각화가 필요합니다.
        """
    },
    "TaskB": {
        "name": "TaskB",
        "description": "데이터 정제: 고객 데이터를 정제하고 요약표를 생성하세요.",
        "requirements": """
        평가 기준:
        1. 중복 데이터 제거
        2. 결측값(NA, null) 처리
        3. 이상치(outlier) 식별 및 처리
        4. 정제된 데이터 요약표 생성 (고객 수, 평균 구매액 등)
        """,
        "input_data": """
        | 고객ID | 이름 | 나이 | 구매액 |
        |--------|------|------|--------|
        | C001 | 김민수 | 35 | 50000 |
        | C002 | 이영희 | NA | 30000 |
        | C001 | 김민수 | 35 | 50000 |
        | C003 | 박철수 | 28 | 999999 |
        | C004 | 최지은 | 42 | 45000 |
        | C005 | 정다은 | 31 | null |
        """,
        "golden_output": """
        # 데이터 정제 결과
        
        ## 정제 과정
        1. 중복 제거: C001 (김민수) 중복 1건 제거
        2. 결측값 처리: 
           - C002 나이 NA → 전체 평균(34세)로 대체
           - C005 구매액 null → 제외 또는 평균(42,500원)으로 대체
        3. 이상치 처리: C003 구매액 999,999원 → 이상치로 판단하여 제외
        
        ## 정제된 데이터
        | 고객ID | 이름 | 나이 | 구매액 |
        |--------|------|------|--------|
        | C001 | 김민수 | 35 | 50000 |
        | C002 | 이영희 | 34 | 30000 |
        | C004 | 최지은 | 42 | 45000 |
        | C005 | 정다은 | 31 | 42500 |
        
        ## 요약표
        - 총 고객 수: 4명
        - 평균 나이: 35.5세
        - 평균 구매액: 41,875원
        - 구매액 범위: 30,000원 ~ 50,000원
        """
    },
    "TaskC": {
        "name": "TaskC",
        "description": "일정 충돌 식별: 회의 일정에서 충돌을 찾아내세요.",
        "requirements": """
        평가 기준:
        1. 모든 일정 충돌 식별 (시간 겹침)
        2. 충돌하는 회의 쌍 명시
        3. 충돌 해결 방안 제시
        4. 추가 오류 발견 시 가점 (PRD R1.3)
        """,
        "input_data": """
        [2025년 1월 20일 회의 일정]
        1. 경영전략회의: 09:00-10:30 (회의실 A)
        2. 마케팅 브리핑: 10:00-11:00 (회의실 B)
        3. 제품개발 리뷰: 10:30-12:00 (회의실 A)
        4. 재무보고: 14:00-15:00 (회의실 C)
        5. 인사평가회의: 14:30-16:00 (회의실 C)
        6. 임원회의: 15:00-17:00 (회의실 A)
        7. 프로젝트 킥오프: 16:00-17:30 (회의실 B)
        8. 분기 결산회의: 16:30-18:00 (회의실 A)
        9. 고객미팅: 17:00-18:00 (회의실 C)
        """,
        "golden_output": """
        # 일정 충돌 분석 결과
        
        ## 식별된 충돌 (9개)
        
        ### 오전 일정 충돌
        1. **경영전략회의 (09:00-10:30, 회의실A)** vs **마케팅 브리핑 (10:00-11:00, 회의실B)**
           - 30분 겹침 (10:00-10:30)
           - 회의실은 다르지만 참석자 겹침 가능성 있음
        
        2. **경영전략회의 (09:00-10:30, 회의실A)** vs **제품개발 리뷰 (10:30-12:00, 회의실A)**
           - 같은 회의실, 연속 일정 (정리 시간 없음)
        
        ### 오후 일정 충돌
        3. **재무보고 (14:00-15:00, 회의실C)** vs **인사평가회의 (14:30-16:00, 회의실C)**
           - 30분 겹침 (14:30-15:00), 같은 회의실
        
        4. **재무보고 (14:00-15:00, 회의실C)** vs **임원회의 (15:00-17:00, 회의실A)**
           - 연속 일정, 회의실 이동 시간 없음
        
        5. **인사평가회의 (14:30-16:00, 회의실C)** vs **임원회의 (15:00-17:00, 회의실A)**
           - 1시간 겹침 (15:00-16:00)
        
        6. **인사평가회의 (14:30-16:00, 회의실C)** vs **프로젝트 킥오프 (16:00-17:30, 회의실B)**
           - 연속 일정, 이동 시간 없음
        
        7. **임원회의 (15:00-17:00, 회의실A)** vs **분기 결산회의 (16:30-18:00, 회의실A)**
           - 30분 겹침 (16:30-17:00), 같은 회의실
        
        8. **프로젝트 킥오프 (16:00-17:30, 회의실B)** vs **고객미팅 (17:00-18:00, 회의실C)**
           - 30분 겹침 (17:00-17:30)
        
        9. **분기 결산회의 (16:30-18:00, 회의실A)** vs **고객미팅 (17:00-18:00, 회의실C)**
           - 1시간 겹침 (17:00-18:00)
        
        ## 해결 방안
        1. 오전 일정 재배치: 마케팅 브리핑을 11:00-12:00으로 변경
        2. 오후 일정 분산: 임원회의를 오전으로 이동 또는 16:00-18:00으로 변경
        3. 회의실 버퍼 타임 추가: 각 회의 사이 15분 여유 시간 확보
        """
    }
}

# 참가자별 프롬프트 (다양한 품질)
PROMPTS = {
    "TaskA": [
        # 참가자 1 (고품질)
        """당신은 경영 전략 분석가입니다. 제공된 분기별 매출 데이터를 분석하여 다음을 수행하세요:

1. 데이터의 핵심 트렌드를 파악합니다
2. 전년 대비 성장률과 분기별 증가율을 계산합니다
3. 제품별 매출 구조를 분석합니다
4. 3가지 핵심 인사이트를 도출하고, 각각에 대해:
   - 구체적인 수치 근거를 제시합니다
   - 비즈니스 의사결정에 활용 가능한 시사점을 제공합니다

출력 형식:
# [연도] 매출 분석 보고서
## 핵심 인사이트
### 1. [인사이트 제목]
[상세 설명과 수치 근거]

### 2. [인사이트 제목]
[상세 설명과 수치 근거]

### 3. [인사이트 제목]
[상세 설명과 수치 근거]""",
        
        # 참가자 2 (중간 품질)
        """분기별 매출 데이터를 분석하여 3가지 인사이트를 도출하세요.
각 인사이트에는 구체적인 숫자를 포함해야 합니다.
마크다운 형식으로 작성하세요.""",
        
        # 참가자 3 (중상 품질)
        """# 과제: 경영 보고서 작성
        
주어진 매출 데이터를 기반으로:
1. 연간 및 분기별 성장 패턴 분석
2. 제품 포트폴리오 구조 평가
3. 3가지 핵심 인사이트 도출 (정량적 근거 포함)

출력 형식: 마크다운 보고서""",
        
        # 참가자 4 (하 품질)
        """매출 데이터를 보고 인사이트를 말해주세요.""",
        
        # 참가자 5 (중상 품질)
        """당신은 데이터 분석 전문가입니다. 
제공된 분기별 매출 데이터와 제품별 비중을 분석하여:
- 성장 트렌드
- 계절성 패턴
- 제품 포트폴리오 리스크
를 고려한 3가지 인사이트를 도출하세요. 각 인사이트는 구체적인 숫자로 뒷받침되어야 합니다."""
    ],
    "TaskB": [
        # 참가자 1
        """당신은 데이터 정제 전문가입니다. 제공된 고객 데이터를 다음 순서로 처리하세요:

1. **중복 제거**: 동일한 고객ID를 가진 레코드 식별 및 제거
2. **결측값 처리**: 
   - 나이 NA: 전체 평균으로 대체
   - 구매액 null: 전체 평균으로 대체 또는 제외
3. **이상치 처리**: 
   - 구매액이 평균±2표준편차를 벗어나면 이상치로 판단
   - 이상치는 제외하거나 별도 표시
4. **요약표 생성**: 
   - 총 고객 수
   - 평균 나이
   - 평균 구매액
   - 구매액 범위

출력 형식:
# 데이터 정제 결과
## 정제 과정
[단계별 처리 내용]
## 정제된 데이터
[마크다운 테이블]
## 요약표
[주요 통계]""",
        
        # 참가자 2
        """고객 데이터를 정제하고 요약표를 만드세요.
중복, NA, 이상치를 처리하세요.""",
        
        # 참가자 3
        """주어진 고객 데이터에서:
1. 중복 레코드 제거
2. 결측값을 적절히 처리
3. 이상치 식별 및 처리
4. 정제된 데이터와 기본 통계 제공""",
        
        # 참가자 4
        """데이터를 깨끗하게 만들어주세요.""",
        
        # 참가자 5
        """데이터 정제 전문가로서:
- 중복: 고객ID 기준으로 제거
- NA/null: 평균값으로 대체
- 이상치: IQR 방식으로 탐지 후 제외
- 최종 결과: 정제된 테이블 + 요약 통계"""
    ],
    "TaskC": [
        # 참가자 1
        """당신은 일정 관리 전문가입니다. 제공된 회의 일정을 분석하여:

1. **시간 충돌 식별**: 
   - 회의 시간이 겹치는 모든 쌍을 찾습니다
   - 같은 회의실을 동시에 사용하는 경우 우선 식별
   - 연속 일정도 이동 시간 부족으로 표시
   
2. **충돌 상세 분석**:
   - 충돌 시작/종료 시간
   - 회의실 정보
   - 겹치는 시간(분)
   
3. **해결 방안 제시**:
   - 일정 재배치 제안
   - 회의실 변경 제안
   - 버퍼 타임 추가 제안

출력 형식:
# 일정 충돌 분석 결과
## 식별된 충돌 (N개)
### [충돌 번호]. [회의1] vs [회의2]
- 충돌 시간: [HH:MM-HH:MM]
- 충돌 유형: [시간 겹침/회의실 중복/이동시간 부족]
## 해결 방안
[구체적인 제안]""",
        
        # 참가자 2
        """회의 일정에서 시간이 겹치는 것을 찾아주세요.""",
        
        # 참가자 3
        """일정 충돌 분석:
1. 모든 회의 시간 비교
2. 겹치는 시간대 식별
3. 같은 회의실 중복 사용 찾기
4. 해결 방안 제시""",
        
        # 참가자 4
        """충돌 찾아주세요.""",
        
        # 참가자 5
        """일정 관리 시스템으로서:
- 시간 겹침: 분 단위로 정확히 계산
- 회의실 충돌: 동시 사용 불가능 식별
- 연속 일정: 15분 버퍼 타임 부족 시 경고
- 충돌 쌍: 모든 조합 체크
- 해결 방안: 최소 변경으로 충돌 제거"""
    ]
}


def create_demo_competition():
    """시연용 대회 생성"""
    print("=" * 60)
    print("🚀 PRD 준수 시연 데이터 생성 시작")
    print("=" * 60)
    
    # 1. 대회 생성
    print("\n📋 1. 대회 생성 중...")
    resp = requests.post(
        f"{API_BASE}/competitions",
        json={
            "name": "2025 프롬프트 엔지니어링 경진대회",
            "description": "실무자 대상 프롬프트 작성 능력 평가 (PRD v2.0 준수)",
            "model": "gpt-4o-mini"
        }
    )
    
    if resp.status_code != 200:
        print(f"❌ 대회 생성 실패: {resp.text}")
        return None
    
    comp_id = resp.json()["id"]
    print(f"✅ Competition ID: {comp_id}")
    
    # 2. 참가자 등록
    print("\n👥 2. 참가자 등록 중...")
    csv_content = "name,email,department,position\n"
    for p in PARTICIPANTS:
        csv_content += f"{p['name']},{p['email']},{p['department']},{p['position']}\n"
    
    files = {"file": ("participants.csv", csv_content.encode('utf-8'), "text/csv")}
    resp = requests.post(
        f"{API_BASE}/competitions/{comp_id}/participants/upload",
        files=files
    )
    
    if resp.status_code != 200:
        print(f"❌ 참가자 등록 실패: {resp.text}")
        return None
    
    print(f"✅ {resp.json()['message']}")
    
    # 3. 과제 생성
    print("\n📝 3. 과제 생성 중...")
    for task_name, task_data in ASSIGNMENTS.items():
        # 과제 기본 정보 생성
        resp = requests.post(
            f"{API_BASE}/competitions/{comp_id}/assignments",
            json={
                "name": task_data["name"],
                "description": task_data["description"],
                "prompt": "당신은 프롬프트 평가 전문가입니다. 제출된 결과물을 정확성, 명확성, 일관성 기준으로 평가하세요.",
                "requirements": task_data["requirements"],
                "golden_output": task_data["golden_output"]
            }
        )
        
        if resp.status_code != 200:
            print(f"❌ 과제 {task_name} 생성 실패: {resp.text}")
            continue
        
        assignment_id = resp.json()["id"]
        print(f"  ✅ {task_name}: {task_data['description'][:50]}...")
        
        # 대상 파일 업로드 (TXT 형식)
        if "input_data" in task_data:
            input_file_content = task_data["input_data"].encode('utf-8')
            files = {
                "file": (f"{task_name}_input.txt", input_file_content, "text/plain")
            }
            
            resp = requests.post(
                f"{API_BASE}/competitions/{comp_id}/assignments/{assignment_id}/input_file",
                files=files
            )
            
            if resp.status_code == 200:
                print(f"     ✅ 대상 파일 업로드 완료")
    
    # 4. 제출물 생성 및 업로드
    print("\n📦 4. 제출물 생성 중...")
    
    # ZIP 파일 생성
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, participant in enumerate(PARTICIPANTS):
            for task_name, prompts_list in PROMPTS.items():
                # 참가자별로 순환하며 프롬프트 할당
                prompt_text = prompts_list[i % len(prompts_list)]
                
                # 파일명: TaskA-Prompt_P001.txt
                filename = f"{task_name}-Prompt_P{participant['id']:03d}.txt"
                zip_file.writestr(filename, prompt_text.encode('utf-8'))
                print(f"  ✅ {filename} ({participant['name']})")
    
    # ZIP 업로드
    print(f"\n📤 ZIP 파일 업로드 중... (15개 파일)")
    zip_buffer.seek(0)
    
    files = {"file": ("submissions.zip", zip_buffer.getvalue(), "application/zip")}
    resp = requests.post(
        f"{API_BASE}/competitions/{comp_id}/submissions/upload",
        files=files
    )
    
    if resp.status_code != 200:
        print(f"❌ 제출물 업로드 실패: {resp.text}")
        return None
    
    result = resp.json()
    print(f"✅ {result['message']}")
    if "skipped" in result:
        print(f"⚠️  Skipped: {result['skipped']}")
    
    # 완료
    print("\n" + "=" * 60)
    print("✅ 시연 데이터 생성 완료!")
    print(f"📊 Competition ID: {comp_id}")
    print(f"👥 참가자: 5명 (실무자)")
    print(f"📝 과제: 3개 (Task A, B, C)")
    print(f"📦 제출물: 15개 (4가지 입력 요소 포함)")
    print(f"\n🌐 웹 UI: {API_BASE}/app")
    print("\n🎯 다음 단계:")
    print("  1. 웹 UI에서 참가자/과제/제출물 확인")
    print("  2. '채점 시작' 버튼으로 자동 채점 (PRD 준수)")
    print("  3. 리더보드에서 결과 확인")
    print("=" * 60)
    
    return comp_id


if __name__ == "__main__":
    create_demo_competition()
