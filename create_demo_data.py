#!/usr/bin/env python3
"""
실제 과제 데이터 생성 스크립트
DB Inc. 프롬프팅 워크숍 실제 과제 A, B, C 기반
"""

import os
import sqlite3
from datetime import datetime

# 데이터베이스 경로
DATA_DIR = os.environ.get("DATA_DIR", ".")
DB_PATH = os.path.join(DATA_DIR, "competition_prd.db")

# ============================================================================
# 실무자 데이터 (5명)
# ============================================================================
PRACTITIONERS = [
    {"name": "김도현"},
    {"name": "이서연"},
    {"name": "박준혁"},
    {"name": "최은지"},
    {"name": "정민수"}
]

# ============================================================================
# Task A: 경영 요약 보고서 생성
# ============================================================================
TASK_A_KPI_DATA = """| 지표        | 2025-10         | 2025-11         | 2025-12         |
|-------------|-----------------|-----------------|-----------------|
| Revenue     | 1,280,000,000   | 1,420,000,000   | 1,560,000,000   |
| New_Signups | 1,050           | 1,320           | 1,400           |
| MAU         | 18,200          | 19,400          | 20,100          |"""

TASK_A_HIGHLIGHT_MEMO = """- 12월 초 디지털 보안 통합 솔루션 업그레이드 완료
- 12/15~20 연말 프로모션 진행, 유료 전환율 10.2% 달성
- 데이터센터 장애 0건, SLA 99.98% 유지"""

TASK_A_INPUT = f"""다음 KPI 데이터와 하이라이트 메모를 기반으로 2025년 12월 경영 요약 보고서를 작성하세요.

### KPI 데이터
{TASK_A_KPI_DATA}

### 하이라이트 메모
{TASK_A_HIGHLIGHT_MEMO}

### 요구사항
1. 각 지표에 대해 전월 대비 증감률과 금액/수치 변화를 자동 계산하여 표시
2. 데이터 기반 인사이트 3개 작성
3. 리스크 요인 2개 작성
4. 액션 아이템 2개 작성
"""

TASK_A_GOLDEN_OUTPUT = """# 2025년 12월 경영 요약 보고서

## 1. 핵심 지표

### Revenue (매출)
- **2025-12**: 1,560,000,000원
- **전월 대비**: +140,000,000원 (+9.86%)
- **전전월 대비**: +280,000,000원 (+21.88%)

### New Signups (신규 가입)
- **2025-12**: 1,400건
- **전월 대비**: +80건 (+6.06%)
- **전전월 대비**: +350건 (+33.33%)

### MAU (월간 활성 사용자)
- **2025-12**: 20,100명
- **전월 대비**: +700명 (+3.61%)
- **전전월 대비**: +1,900명 (+10.44%)

## 2. 주요 하이라이트
- 12월 초 디지털 보안 통합 솔루션 업그레이드 완료
- 12/15~20 연말 프로모션 진행, 유료 전환율 10.2% 달성
- 데이터센터 장애 0건, SLA 99.98% 유지

## 3. 인사이트
1. **지속적 성장세**: 매출이 3개월 연속 상승하며, 특히 12월에는 전전월 대비 21.88% 증가로 강력한 성장세를 보임
2. **신규 유입 증가**: 신규 가입자가 전전월 대비 33.33% 급증하며, 마케팅 및 프로모션 효과가 뚜렷함
3. **높은 서비스 안정성**: SLA 99.98% 달성으로 고객 신뢰도 향상 및 이탈률 감소 기대

## 4. 리스크
1. **MAU 증가율 둔화**: MAU 증가율이 전월 대비 3.61%로 신규 가입 증가율(6.06%)보다 낮아, 활성 사용자 전환율 점검 필요
2. **프로모션 종료 후 이탈 우려**: 연말 프로모션 종료 후 유료 전환율 및 매출 유지 가능성 모니터링 필요

## 5. 액션 아이템
1. **신규 사용자 온보딩 강화**: 가입 후 30일 이내 활성 사용자 전환율을 높이기 위한 온보딩 프로그램 개선
2. **프로모션 후속 전략 수립**: 1월 신규 캠페인 또는 리텐션 프로그램을 통해 12월 유입 고객의 장기 유지율 확보
"""

TASK_A = {
    "title": "Task A: 경영 요약 보고서 생성",
    "description": "KPI 데이터와 하이라이트 메모를 기반으로 경영 요약 보고서를 자동 생성하는 프롬프트를 작성하세요.",
    "input_data": TASK_A_INPUT,
    "golden_output": TASK_A_GOLDEN_OUTPUT,
    "evaluation_notes": "전월 대비 자동 계산, 인사이트 3개, 리스크 2개, 액션 2개가 모두 포함되어야 함"
}

# ============================================================================
# Task B: 고객 목록 정제 및 요약
# ============================================================================
TASK_B_INPUT = """첨부된 Excel 파일 'task_b_input.xlsx'에는 고객 목록 데이터가 포함되어 있습니다.

### 문제점
- 날짜 형식이 제각각 (예: '04-12-24', '2025.09.23', '2024/10/02')
- plan 필드 대소문자 혼재 (예: 'Enterprise', 'ENTERPRISE', 'enterprise')
- 금액 필드에 통화 기호 혼재 (예: '99000', '₩99,000')
- 중복 데이터 존재
- 테스트 계정 포함 (예: 'test@', '@test')

### 요구사항
**출력 1: 정제된 고객 목록**
- 날짜 형식을 'YYYY-MM-DD'로 통일
- plan을 모두 대문자로 통일
- amount에서 통화 기호 및 쉼표 제거, 숫자만 남김
- 중복 제거 (email 기준)
- 테스트 계정 제거
- id 컬럼 제거
- 컬럼 순서: name, email, signup_date, last_active, plan, amount

**출력 2: Plan별 요약 대시보드**
- 각 plan별 건수와 amount 합계
- 컬럼: plan, 건수, amount 합계
- 마지막 행에 '합계' 추가
"""

TASK_B_GOLDEN_OUTPUT = """다음 두 개의 시트를 생성합니다:

**시트 1: 정제 데이터** (93건)
- 날짜 형식: YYYY-MM-DD
- plan: 모두 대문자 (PRO, FREE, ENTERPRISE, BASIC, TRIAL)
- amount: 숫자만 (쉼표/통화기호 제거)
- 중복/테스트 계정 제거됨
- 컬럼 순서: name, email, signup_date, last_active, plan, amount

**시트 2: 요약 대시보드**
| plan       | 건수 | amount 합계 |
|------------|------|-------------|
| PRO        | 15   | 448,500     |
| FREE       | 39   | 0           |
| ENTERPRISE | 10   | 990,000     |
| BASIC      | 24   | 237,600     |
| TRIAL      | 5    | 0           |
| 합계       | 93   | 1,676,100   |
"""

TASK_B = {
    "title": "Task B: 고객 목록 정제 및 요약",
    "description": "지저분한 Excel 데이터를 정제하고 Plan별 요약표를 생성하는 프롬프트를 작성하세요.",
    "input_data": TASK_B_INPUT,
    "golden_output": TASK_B_GOLDEN_OUTPUT,
    "evaluation_notes": "정제된 데이터 93건, Plan별 요약표 정확성, 날짜/plan/amount 형식 통일"
}

# ============================================================================
# Task C: 문서 정보 추출 및 충돌 식별
# ============================================================================
TASK_C_INPUT = """첨부된 PDF 문서 'IT_시스템_접근권한_관리절차서.pdf'에서 다음 정보를 추출하세요.

### 추출 항목
1. 문서 제목
2. 문서 코드
3. 문서 버전
4. 작성 부서
5. 작성일자
6. 승인자
7. 문서 분류
8. 처리 기한
9. 검토 주기
10. 자동 폐기 기준

### 특별 요구사항
- 문서 내에서 **정보 충돌**이 발견되면 모두 보고
- 충돌 보고 시 각 항목에 대해 **어디서**(페이지, 섹션) **무엇이** 나타났는지 상세히 기록
- 임의로 하나를 선택하지 말고, 모든 충돌을 명시

### 알려진 충돌 (9개)
1. 부서명 불일치 (IT보안운영팀 vs IT보안팀 vs 정보보호팀 등)
2. 문서 분류 모순 (Confidential vs Internal Use Only)
3. 문서 버전 불일치 (Rev 2.0 vs 2.1 vs 2.2)
4. 문서 코드 불일치
5. 작성일자 모순
6. 승인자 불일치
7. 처리 기한 모순 (24시간 vs 4시간)
8. 검토 주기 모순 (분기 vs 반기)
9. 자동 폐기 기준 중복 (90일 vs 180일)
"""

TASK_C_GOLDEN_OUTPUT = """# 문서 정보 추출 결과

## 1. 기본 정보
- **문서 제목**: IT 시스템 접근 권한 관리 절차서
- **문서 코드**: ⚠️ 충돌 발견
  - 표지: IT-SEC-2025-001
  - 본문 2쪽: IT-SEC-2025-002
- **문서 버전**: ⚠️ 충돌 발견
  - 표지: Rev 2.0
  - 본문 하단: Rev 2.1
  - 부록: Rev 2.2
- **작성 부서**: ⚠️ 충돌 발견
  - 표지: IT보안운영팀
  - 본문 3쪽: IT보안팀
  - 부록: 정보보호팀
- **작성일자**: ⚠️ 충돌 발견
  - 표지: 2025-01-10
  - 승인란: 2025-01-15
- **승인자**: ⚠️ 충돌 발견
  - 표지: 김철수 이사
  - 승인란: 박영희 상무
- **문서 분류**: ⚠️ 충돌 발견
  - 표지: Confidential
  - 본문 상단: Internal Use Only

## 2. 절차 정보
- **처리 기한**: ⚠️ 충돌 발견
  - 본문 5쪽 '신청 절차': 신청 후 24시간 이내 처리
  - 본문 7쪽 '긴급 처리': 긴급 요청 시 4시간 이내 처리
- **검토 주기**: ⚠️ 충돌 발견
  - 본문 9쪽: 분기별 검토
  - 부록: 반기별 검토
- **자동 폐기 기준**: ⚠️ 충돌 발견
  - 본문 10쪽: 미사용 계정 90일 후 자동 폐기
  - 부록: 미사용 계정 180일 후 자동 폐기

## 3. 충돌 요약 (총 9건)
| 항목 | 충돌 내용 | 위치 |
|------|----------|------|
| 문서 코드 | IT-SEC-2025-001 vs IT-SEC-2025-002 | 표지 vs 본문 2쪽 |
| 문서 버전 | Rev 2.0 vs Rev 2.1 vs Rev 2.2 | 표지 vs 본문 vs 부록 |
| 작성 부서 | IT보안운영팀 vs IT보안팀 vs 정보보호팀 | 표지 vs 본문 vs 부록 |
| 작성일자 | 2025-01-10 vs 2025-01-15 | 표지 vs 승인란 |
| 승인자 | 김철수 이사 vs 박영희 상무 | 표지 vs 승인란 |
| 문서 분류 | Confidential vs Internal Use Only | 표지 vs 본문 |
| 처리 기한 | 24시간 vs 4시간 | 본문 5쪽 vs 7쪽 |
| 검토 주기 | 분기별 vs 반기별 | 본문 9쪽 vs 부록 |
| 폐기 기준 | 90일 vs 180일 | 본문 10쪽 vs 부록 |

## 4. 권고사항
문서 관리자는 위 충돌 사항을 확인하고 정확한 정보로 통일해야 합니다.
"""

TASK_C = {
    "title": "Task C: 문서 정보 추출 및 충돌 식별",
    "description": "비구조화된 PDF 문서에서 정보를 추출하고, 문서 내 정보 충돌을 모두 식별하는 프롬프트를 작성하세요.",
    "input_data": TASK_C_INPUT,
    "golden_output": TASK_C_GOLDEN_OUTPUT,
    "evaluation_notes": "9개 충돌 항목 모두 식별, 근거(위치) 명시, 임의 선택 금지"
}

# ============================================================================
# 제출물 생성 (5명 × 3개 과제 = 15개)
# ============================================================================
SUBMISSIONS = {
    "김도현": {
        "Task A": """너는 데이터 분석가야. 다음 KPI 데이터와 하이라이트를 분석해서 경영 요약 보고서를 작성해줘.

**KPI 데이터**
{kpi_data}

**하이라이트**
{highlight}

**단계별 지침**
1. 각 지표의 전월 대비 증감률 계산 (공식: (12월-11월)/11월 × 100)
2. 전전월 대비 증감률도 계산 (공식: (12월-10월)/10월 × 100)
3. 인사이트 3개 도출 (성장세, 신규유입, 서비스안정성)
4. 리스크 2개 식별 (MAU 증가율, 프로모션 종료)
5. 액션 2개 제안 (온보딩, 리텐션)

**출력 형식**
- 섹션: 핵심 지표, 주요 하이라이트, 인사이트, 리스크, 액션 아이템
- 각 지표마다 전월/전전월 대비 계산 결과 표시
""",
        "Task B": """너는 데이터 정제 전문가야. 다음 Excel 파일을 분석하고 정제해줘.

**입력**: task_b_input.xlsx

**정제 단계**
1. 날짜 형식 통일: 'YYYY-MM-DD'로 변환
2. plan 대문자 통일: upper() 함수 적용
3. amount 숫자만 추출: 정규식으로 숫자만 남김
4. 중복 제거: email 기준 drop_duplicates()
5. 테스트 계정 제거: email에 'test' 포함된 행 삭제
6. id 컬럼 삭제
7. 컬럼 순서: name, email, signup_date, last_active, plan, amount

**출력 1: 정제 데이터 (시트명: '정제 데이터')**
- 정제된 고객 목록 93건

**출력 2: 요약 대시보드 (시트명: '요약 대시보드')**
- plan별 groupby 집계
- 컬럼: plan, 건수, amount 합계
- 마지막 행에 '합계' 추가

**검증**
- 정제 데이터 건수가 93건인지 확인
- 요약 대시보드 합계가 1,676,100인지 확인
""",
        "Task C": """너는 문서 분석 전문가야. 다음 PDF 문서를 분석해서 정보를 추출하고 충돌을 식별해줘.

**입력**: IT_시스템_접근권한_관리절차서.pdf

**추출 항목 (10개)**
1. 문서 제목
2. 문서 코드
3. 문서 버전
4. 작성 부서
5. 작성일자
6. 승인자
7. 문서 분류
8. 처리 기한
9. 검토 주기
10. 자동 폐기 기준

**충돌 식별 규칙**
- 같은 항목에 대해 다른 정보가 나타나면 모두 기록
- 각 충돌에 대해 위치(페이지, 섹션) 명시
- 임의로 하나를 선택하지 말 것
- 알려진 충돌 9개를 모두 찾아야 함

**출력 형식**
- 섹션 1: 기본 정보 (충돌 시 ⚠️ 표시 + 모든 값과 위치 나열)
- 섹션 2: 절차 정보 (충돌 시 ⚠️ 표시 + 모든 값과 위치 나열)
- 섹션 3: 충돌 요약 테이블
- 섹션 4: 권고사항

**검증**
- 충돌 9개가 모두 식별되었는지 확인
"""
    },
    "이서연": {
        "Task A": """당신은 전략 기획 전문가입니다. 주어진 KPI와 하이라이트를 기반으로 경영진 보고서를 생성하세요.

[입력 데이터]
{kpi_data}
{highlight}

[작성 가이드]
- 전월 대비 변화율을 자동 계산하여 표시
- 데이터에서 3가지 핵심 인사이트 도출
- 2가지 잠재 리스크 식별
- 2가지 실행 가능한 액션 아이템 제안

[출력 구조]
1. 핵심 지표 (전월/전전월 대비 계산 포함)
2. 주요 하이라이트
3. 인사이트 (3개)
4. 리스크 (2개)
5. 액션 아이템 (2개)

각 섹션은 명확히 구분하고, 수치는 쉼표로 포맷팅하세요.
""",
        "Task B": """당신은 데이터 엔지니어입니다. 지저분한 고객 데이터를 정제하고 요약하세요.

[입력]
- 파일명: task_b_input.xlsx
- 문제: 날짜 형식 불일치, plan 대소문자 혼재, 중복, 테스트 계정

[정제 프로세스]
1단계: 날짜 형식을 'YYYY-MM-DD'로 통일
2단계: plan을 모두 대문자로 변환
3단계: amount에서 숫자만 추출
4단계: email 기준 중복 제거
5단계: 테스트 계정 삭제 (email에 'test' 포함)
6단계: id 컬럼 제거
7단계: 컬럼 순서 재배치 (name, email, signup_date, last_active, plan, amount)

[출력]
시트 1 '정제 데이터': 정제된 고객 목록
시트 2 '요약 대시보드': plan별 건수와 금액 합계 (마지막 행에 '합계' 추가)

[검증 기준]
- 정제 데이터: 93건
- 합계: 1,676,100
""",
        "Task C": """당신은 품질 관리 전문가입니다. PDF 문서에서 정보를 추출하고 불일치를 보고하세요.

[문서명]
IT_시스템_접근권한_관리절차서.pdf

[추출 대상 (10개 항목)]
문서 제목, 문서 코드, 문서 버전, 작성 부서, 작성일자, 승인자, 문서 분류, 처리 기한, 검토 주기, 자동 폐기 기준

[충돌 탐지 규칙]
- 동일 항목에 대해 다른 값이 존재하면 충돌로 간주
- 각 충돌에 대해 모든 값과 출처(페이지/섹션) 기록
- 절대 임의로 하나를 선택하지 말 것
- 총 9개 충돌이 존재함

[보고 형식]
## 1. 기본 정보
각 항목별로 충돌 시 ⚠️ 표시 + 모든 값 나열

## 2. 절차 정보
각 항목별로 충돌 시 ⚠️ 표시 + 모든 값 나열

## 3. 충돌 요약 테이블
| 항목 | 충돌 내용 | 위치 |

## 4. 권고사항
"""
    },
    "박준혁": {
        "Task A": """# 역할: 데이터 애널리스트
# 목표: 2025년 12월 경영 요약 보고서 생성

## 입력
**KPI 데이터**
{kpi_data}

**하이라이트 메모**
{highlight}

## 처리 절차
1. Revenue: 전월 대비 증감 계산
   - 계산식: (1,560,000,000 - 1,420,000,000) / 1,420,000,000 × 100
2. New_Signups: 전월 대비 증감 계산
   - 계산식: (1,400 - 1,320) / 1,320 × 100
3. MAU: 전월 대비 증감 계산
   - 계산식: (20,100 - 19,400) / 19,400 × 100
4. 전전월 대비도 동일하게 계산
5. 인사이트 3개 작성: 성장세, 신규유입, 서비스안정성
6. 리스크 2개 작성: MAU 증가율 둔화, 프로모션 종료 우려
7. 액션 2개 작성: 온보딩 강화, 리텐션 전략

## 출력 형식
- Markdown
- 섹션: 핵심 지표, 주요 하이라이트, 인사이트, 리스크, 액션 아이템
- 수치는 천 단위 쉼표 포함
""",
        "Task B": """# 역할: ETL 엔지니어
# 목표: 고객 데이터 정제 및 요약

## 입력 파일
task_b_input.xlsx (100건, 컬럼: id, name, email, amount, plan, signup_date, last_active)

## 데이터 품질 문제
- 날짜: '04-12-24', '2025.09.23', '2024/10/02' 등 혼재
- plan: 'Enterprise', 'ENTERPRISE', 'enterprise' 등 혼재
- amount: '99000', '₩99,000', '$99,000' 등 혼재
- 중복: email 중복 존재
- 쓰레기: 테스트 계정 (email에 'test' 포함)

## 정제 파이프라인
```python
# 1. 날짜 형식 통일
df['signup_date'] = pd.to_datetime(df['signup_date']).dt.strftime('%Y-%m-%d')
df['last_active'] = pd.to_datetime(df['last_active']).dt.strftime('%Y-%m-%d')

# 2. plan 대문자 통일
df['plan'] = df['plan'].str.upper()

# 3. amount 숫자만 추출
df['amount'] = df['amount'].replace('[^0-9]', '', regex=True).astype(int)

# 4. 중복 제거
df = df.drop_duplicates(subset=['email'])

# 5. 테스트 계정 제거
df = df[~df['email'].str.contains('test', case=False)]

# 6. id 제거 및 컬럼 순서 변경
df = df[['name', 'email', 'signup_date', 'last_active', 'plan', 'amount']]
```

## 출력
**시트 1: 정제 데이터**
- 93건
- 컬럼: name, email, signup_date, last_active, plan, amount

**시트 2: 요약 대시보드**
- plan별 groupby
- 컬럼: plan, 건수, amount 합계
- 마지막 행: '합계', 93, 1676100
""",
        "Task C": """# 역할: 문서 품질 감사관
# 목표: PDF 문서 정보 추출 및 충돌 보고

## 입력 문서
IT_시스템_접근권한_관리절차서.pdf

## 추출 체크리스트
- [ ] 문서 제목
- [ ] 문서 코드
- [ ] 문서 버전
- [ ] 작성 부서
- [ ] 작성일자
- [ ] 승인자
- [ ] 문서 분류
- [ ] 처리 기한
- [ ] 검토 주기
- [ ] 자동 폐기 기준

## 충돌 탐지 프로토콜
**규칙 1**: 동일 항목에 대해 서로 다른 값이 나타나면 충돌로 기록
**규칙 2**: 모든 충돌에 대해 값과 출처(페이지/섹션) 명시
**규칙 3**: 임의 선택 금지 (예: "Rev 2.0과 Rev 2.1이 충돌" → 둘 다 기록)
**규칙 4**: 알려진 충돌 9개를 모두 식별해야 함

## 출력 템플릿
### 1. 기본 정보
- 문서 제목: [값]
- 문서 코드: ⚠️ 충돌 발견
  - 표지: [값1]
  - 본문 2쪽: [값2]
- ...

### 2. 절차 정보
- ...

### 3. 충돌 요약 (총 9건)
| 항목 | 충돌 내용 | 위치 |
|------|----------|------|
| ... | ... | ... |

### 4. 권고사항
문서 관리자는 위 충돌 사항을 확인하고 정확한 정보로 통일해야 합니다.
"""
    },
    "최은지": {
        "Task A": """다음 데이터를 보고 경영 요약 보고서를 작성해주세요.

KPI:
{kpi_data}

메모:
{highlight}

보고서에는 다음이 포함되어야 합니다:
- 각 지표의 전월 대비 변화 (증감률과 금액/수치)
- 인사이트 3개
- 리스크 2개
- 액션 아이템 2개

보고서 형식은 마크다운으로 작성하세요.
""",
        "Task B": """task_b_input.xlsx 파일의 고객 데이터를 정제하세요.

정제 작업:
1. 날짜를 YYYY-MM-DD 형식으로 바꾸기
2. plan을 대문자로 바꾸기
3. amount에서 숫자만 남기기
4. 이메일 중복 제거
5. 테스트 계정 삭제
6. id 컬럼 삭제

출력:
- 시트 1: 정제된 데이터 (name, email, signup_date, last_active, plan, amount)
- 시트 2: plan별 요약 (plan, 건수, amount 합계)

최종 결과는 93건이어야 하고, 합계는 1,676,100이어야 합니다.
""",
        "Task C": """IT_시스템_접근권한_관리절차서.pdf 파일을 분석해서 다음 정보를 찾으세요:

1. 문서 제목
2. 문서 코드
3. 문서 버전
4. 작성 부서
5. 작성일자
6. 승인자
7. 문서 분류
8. 처리 기한
9. 검토 주기
10. 자동 폐기 기준

만약 같은 항목에 대해 다른 정보가 나오면 모두 기록하세요.
예를 들어, 문서 버전이 어떤 페이지에서는 Rev 2.0이고 다른 페이지에서는 Rev 2.1이면 둘 다 적어주세요.

충돌이 발견되면 ⚠️ 표시를 하고, 어디서(페이지) 무엇이 나왔는지 자세히 써주세요.

총 9개의 충돌이 있을 것으로 예상됩니다.
"""
    },
    "정민수": {
        "Task A": """너는 비즈니스 애널리스트야. KPI 데이터로 경영 보고서 만들어줘.

입력:
{kpi_data}
{highlight}

작업:
1. Revenue, New_Signups, MAU 각각 전월 대비 % 계산
2. 전전월 대비도 계산
3. 인사이트 3개 (성장, 신규, 안정성)
4. 리스크 2개 (MAU, 프로모션)
5. 액션 2개 (온보딩, 리텐션)

형식:
# 2025년 12월 경영 요약 보고서
## 1. 핵심 지표
## 2. 주요 하이라이트
## 3. 인사이트
## 4. 리스크
## 5. 액션 아이템
""",
        "Task B": """task_b_input.xlsx를 정제해서 두 개 시트로 출력해줘.

정제:
- 날짜: YYYY-MM-DD
- plan: 대문자
- amount: 숫자만
- 중복/테스트 제거
- id 삭제

출력:
시트1 '정제 데이터': name, email, signup_date, last_active, plan, amount (93건)
시트2 '요약 대시보드': plan, 건수, amount 합계 (마지막에 '합계' 행 추가)
""",
        "Task C": """IT_시스템_접근권한_관리절차서.pdf에서 다음 10개 정보를 추출하고, 정보 충돌을 보고해줘.

추출:
문서 제목, 문서 코드, 문서 버전, 작성 부서, 작성일자, 승인자, 문서 분류, 처리 기한, 검토 주기, 자동 폐기 기준

충돌:
- 같은 항목에 다른 값이 있으면 모두 기록
- 어디서(페이지) 무엇이 나왔는지 써줘
- 총 9개 충돌이 있음

출력:
1. 기본 정보 (충돌 시 ⚠️)
2. 절차 정보 (충돌 시 ⚠️)
3. 충돌 요약 테이블
4. 권고사항
"""
    }
}

def init_database():
    """데이터베이스 초기화"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # 테이블 생성
    c.execute("""
    CREATE TABLE IF NOT EXISTS practitioners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
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
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        practitioner_id INTEGER NOT NULL,
        prompt_text TEXT NOT NULL,
        status TEXT DEFAULT 'submitted',
        grading_result TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        graded_at TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES tasks(id),
        FOREIGN KEY (practitioner_id) REFERENCES practitioners(id)
    )
    """)
    
    conn.commit()
    conn.close()


def create_demo_data():
    """시연 데이터 생성"""
    print("=" * 70)
    print("실제 과제 데이터 생성 시작")
    print("=" * 70)
    
    # 데이터베이스 초기화
    print("\n[1/4] 데이터베이스 초기화...")
    init_database()
    print("✓ 데이터베이스 초기화 완료")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        # 기존 데이터 삭제
        print("\n[2/4] 기존 데이터 삭제...")
        c.execute("DELETE FROM submissions")
        c.execute("DELETE FROM tasks")
        c.execute("DELETE FROM practitioners")
        conn.commit()
        print("✓ 기존 데이터 삭제 완료")
        
        # 실무자 생성
        print("\n[3/4] 실무자 생성...")
        practitioners = {}
        for p_data in PRACTITIONERS:
            c.execute("""
                INSERT INTO practitioners (name)
                VALUES (?)
            """, (p_data["name"],))
            practitioners[p_data["name"]] = c.lastrowid
            print(f"  ✓ {p_data['name']}")
        conn.commit()
        print(f"✓ 총 {len(practitioners)}명 실무자 생성 완료")
        
        # 과제 생성
        print("\n[4/4] 과제 및 제출물 생성...")
        task_data_list = [TASK_A, TASK_B, TASK_C]
        submission_count = 0
        
        for task_data in task_data_list:
            # 과제 생성
            c.execute("""
                INSERT INTO tasks (title, description, input_data, golden_output, evaluation_notes)
                VALUES (?, ?, ?, ?, ?)
            """, (task_data["title"], task_data["description"], task_data["input_data"], 
                  task_data["golden_output"], task_data["evaluation_notes"]))
            task_id = c.lastrowid
            print(f"\n  ✓ {task_data['title']} 생성 완료")
            
            # 각 실무자별 제출물 생성
            for practitioner_name, submissions_dict in SUBMISSIONS.items():
                practitioner_id = practitioners[practitioner_name]
                task_key = task_data["title"].split(":")[0]  # "Task A", "Task B", "Task C"
                
                if task_key in submissions_dict:
                    # Task A의 경우 입력 데이터 포맷팅
                    prompt_text = submissions_dict[task_key]
                    if task_key == "Task A":
                        prompt_text = prompt_text.format(
                            kpi_data=TASK_A_KPI_DATA,
                            highlight=TASK_A_HIGHLIGHT_MEMO
                        )
                    
                    c.execute("""
                        INSERT INTO submissions (task_id, practitioner_id, prompt_text, status)
                        VALUES (?, ?, ?, 'submitted')
                    """, (task_id, practitioner_id, prompt_text))
                    submission_count += 1
                    print(f"    - {practitioner_name} 제출물 생성")
        
        conn.commit()
        print(f"\n✓ 총 {submission_count}개 제출물 생성 완료")
        
        # 요약
        print("\n" + "=" * 70)
        print("시연 데이터 생성 완료")
        print("=" * 70)
        print(f"✓ 실무자: {len(practitioners)}명")
        print(f"✓ 과제: {len(task_data_list)}개")
        print(f"✓ 제출물: {submission_count}개")
        print("\n실무자 목록:")
        for name in practitioners.keys():
            print(f"  - {name}")
        print("\n과제 목록:")
        for task_data in task_data_list:
            print(f"  - {task_data['title']}")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    create_demo_data()
