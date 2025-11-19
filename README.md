# 🎯 Auto-Grader v2.0 - PRD 준수

프롬프트 경진대회 자동 평가 플랫폼 (PRD v1.0 완벽 준수)

## 📋 PRD 핵심 요구사항

### 평가 프로세스
1. **1단계: 프롬프트 3회 실행** (temperature=0.1)
   - 참가자 프롬프트 + 대상 파일 → LLM 실행
   - 3개의 결과물 생성 (Output 1, 2, 3)

2. **2단계: 마스터 평가** (temperature=0)
   - 3개 결과물 + 정답셋 + 요구사항 → 평가
   - 정확성(50점) + 명확성(30점) + 일관성(20점) = 총 100점

### 4가지 입력 요소
1. **참가자 프롬프트** (필수)
2. **대상 파일** (PDF/TXT/Excel, 선택적)
3. **정답 산출물** (Golden Set, 선택적)
4. **요구사항** (Rubric, 선택적)

## 🚀 빠른 시작

### 로컬 실행
```bash
# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
export OPENAI_API_KEY="your-api-key"

# 서버 시작
python main.py
```

### Railway 배포
1. GitHub 저장소 연결
2. 환경변수 설정: `OPENAI_API_KEY`
3. 자동 배포

### 시연 데이터 생성
```bash
python create_demo_data.py
```

## 📊 과제 예시

### Task A: 경영 보고서
- **대상 파일**: 분기별 매출 데이터 (TXT)
- **요구사항**: 3가지 인사이트, 정량적 근거
- **평가**: 데이터 기반 분석, 비즈니스 시사점

### Task B: 데이터 정제
- **대상 파일**: 고객 데이터 (Excel → Markdown Table)
- **요구사항**: 중복/결측값/이상치 처리
- **평가**: 정제 프로세스, 요약 통계

### Task C: 일정 충돌 식별
- **대상 파일**: 회의 일정 (TXT)
- **요구사항**: 모든 충돌 식별, 해결 방안
- **평가**: 정확성, 추가 오류 발견 시 가점

## 🏗️ 시스템 아키텍처

```
Frontend (Vanilla JS)
    ↓
FastAPI Backend
    ↓
┌─────────────────┬────────────────┬──────────────┐
│ File Parser     │ Grading Engine │ SQLite DB    │
│ (PDF/TXT/Excel) │ (2-stage)      │ (4 inputs)   │
└─────────────────┴────────────────┴──────────────┘
    ↓
OpenAI API (GPT-4o-mini)
```

## 📁 프로젝트 구조

```
auto-grader-prd/
├── main.py              # FastAPI 백엔드
├── grading_engine.py    # 2단계 채점 엔진
├── file_parser.py       # PDF/TXT/Excel 파서
├── schema.sql           # 데이터베이스 스키마
├── create_demo_data.py  # 시연 데이터 생성
├── requirements.txt     # 패키지 의존성
└── static/
    └── index.html       # 웹 UI (추후 추가)
```

## 🔧 주요 기능

### F1: 대회 관리
- [x] 대회 생성 (모델 선택 포함)
- [x] 과제 설정 (4가지 입력 요소)
- [x] 정답셋 및 평가 기준 업로드

### F2: 참가자 및 제출물 관리
- [x] 참가자 일괄 등록 (CSV)
- [x] 제출물 일괄 업로드 (ZIP)
- [x] 자동 매칭 (파일명 규칙)

### F3: 자동 채점
- [x] 프롬프트 3회 실행 (T=0.1)
- [x] 마스터 평가 (T=0)
- [x] 에러 핸들링 및 재시도

### F4: 결과 대시보드
- [x] 종합 리더보드
- [x] 상세 평가 리포트 (항목별 점수 + 사유)
- [x] 상태 플래그 (완료/실패/수동검토)

## 📊 평가 기준 (PRD R2)

| 항목 | 배점 | 세부 기준 |
|------|------|-----------|
| **정확성** | 50점 | 정답셋 일치 또는 개념적 기준 충족 |
| **명확성** | 30점 | 명확한 역할, 문맥, 단계별 지시 |
| **일관성** | 20점 | 3회 실행 결과 일치도 + 검증 장치 |

## 🔒 비기능적 요구사항

- **NFR1**: 비개발자용 웹 UI (코드 없이 클릭만으로 운영)
- **NFR2**: 평가 시 temperature=0 (일관성 보장)
- **NFR3**: GPT-4o-mini 사용 (비용 효율성)
- **NFR4**: 40명 × 3과제 = 120개 제출물 1시간 내 처리

## 📞 지원

- **GitHub**: https://github.com/kstyle2198/auto-grader-prd
- **Railway**: https://railway.app/
- **문의**: PRD 기반 시스템 구현 문의
