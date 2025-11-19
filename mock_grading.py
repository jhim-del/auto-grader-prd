import sqlite3
import json
import random
from datetime import datetime

# DB 연결
conn = sqlite3.connect('grader.db')
cursor = conn.cursor()

# 제출물 조회
cursor.execute("""
    SELECT id, task_id, practitioner_id, prompt_text
    FROM submissions
    WHERE grading_result IS NULL
    ORDER BY id
""")
submissions = cursor.fetchall()

print(f"총 {len(submissions)}개 제출물 채점 시작...")

for idx, (sub_id, task_id, prac_id, prompt) in enumerate(submissions, 1):
    # 무작위 점수 생성 (70~100점)
    score = random.randint(70, 100)
    
    # 목업 채점 결과 생성
    mock_result = {
        "overall_score": score,
        "final_evaluation": f"{score}점 - 프롬프트가 요구사항을 {'잘' if score >= 85 else '대체로'} 충족합니다.",
        "strengths": [
            "명확한 지시사항 포함",
            "적절한 구조화",
            "핵심 요소 반영"
        ],
        "weaknesses": [
            "세부 조건 보완 필요" if score < 90 else "없음"
        ],
        "detailed_criteria": [
            {
                "criterion": "완성도",
                "score": min(score + random.randint(-5, 5), 100),
                "feedback": "요구사항을 충분히 반영함"
            },
            {
                "criterion": "정확성",
                "score": min(score + random.randint(-5, 5), 100),
                "feedback": "출력 형식이 적절함"
            },
            {
                "criterion": "명확성",
                "score": min(score + random.randint(-5, 5), 100),
                "feedback": "지시사항이 명확함"
            }
        ],
        "execution_results": [
            {
                "attempt": 1,
                "output": f"[실행 결과 1] {prompt[:50]}... 로 생성된 출력",
                "analysis": "기대 출력과 유사한 구조"
            },
            {
                "attempt": 2,
                "output": f"[실행 결과 2] {prompt[:50]}... 로 생성된 출력",
                "analysis": "일관성 있는 결과"
            },
            {
                "attempt": 3,
                "output": f"[실행 결과 3] {prompt[:50]}... 로 생성된 출력",
                "analysis": "안정적인 성능"
            }
        ]
    }
    
    # DB 업데이트
    cursor.execute("""
        UPDATE submissions
        SET 
            execution_output_1 = ?,
            execution_output_2 = ?,
            execution_output_3 = ?,
            grading_result = ?,
            status = 'completed',
            graded_at = ?
        WHERE id = ?
    """, (
        mock_result["execution_results"][0]["output"],
        mock_result["execution_results"][1]["output"],
        mock_result["execution_results"][2]["output"],
        json.dumps(mock_result, ensure_ascii=False),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        sub_id
    ))
    
    if idx % 10 == 0:
        print(f"  진행중... {idx}/{len(submissions)}")

conn.commit()
conn.close()

print(f"\n✅ 총 {len(submissions)}개 제출물 채점 완료!")
