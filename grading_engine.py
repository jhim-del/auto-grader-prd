"""
PRD 준수 채점 엔진
1단계: 프롬프트 3회 실행 (T=0.1)
2단계: 마스터 평가 프롬프트로 평가 (T=0)
"""

import os
import json
import time
from typing import Dict, List, Tuple, Optional
from openai import OpenAI


class GradingEngine:
    """PRD 준수 자동 채점 엔진"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        # OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
        # PRD NFR2: 평가 시 temperature=0
        self.execution_temperature = 0.1  # 프롬프트 실행 시
        self.grading_temperature = 0.0    # 평가 시
    
    def execute_prompt_3_times(
        self, 
        participant_prompt: str, 
        input_file_content: Optional[str] = None,
        max_retries: int = 2
    ) -> Tuple[bool, List[str], Optional[str]]:
        """
        PRD F3.3: 참가자 프롬프트를 3회 실행
        
        Args:
            participant_prompt: 참가자가 제출한 프롬프트
            input_file_content: 대상 파일 내용 (선택적)
            max_retries: 실패 시 재시도 횟수
            
        Returns:
            (성공 여부, [결과1, 결과2, 결과3], 에러 메시지)
        """
        outputs = []
        
        # 입력 프롬프트 구성
        if input_file_content:
            full_prompt = f"{participant_prompt}\n\n[Input Data]\n{input_file_content}"
        else:
            full_prompt = participant_prompt
        
        for attempt in range(3):
            success, output, error = self._execute_single_prompt(
                full_prompt, 
                max_retries
            )
            
            if not success:
                return False, [], f"Execution {attempt+1} failed: {error}"
            
            outputs.append(output)
            time.sleep(0.5)  # Rate limiting
        
        return True, outputs, None
    
    def _execute_single_prompt(
        self, 
        prompt: str, 
        max_retries: int = 2
    ) -> Tuple[bool, str, Optional[str]]:
        """
        단일 프롬프트 실행 (재시도 포함)
        
        Returns:
            (성공 여부, 결과 텍스트, 에러 메시지)
        """
        for retry in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.execution_temperature,
                    max_tokens=4000
                )
                
                output = response.choices[0].message.content
                return True, output, None
                
            except Exception as e:
                error_msg = str(e)
                if retry < max_retries:
                    time.sleep(2 ** retry)  # Exponential backoff
                    continue
                else:
                    return False, "", error_msg
        
        return False, "", "Max retries exceeded"
    
    def evaluate_outputs(
        self,
        participant_prompt: str,
        execution_outputs: List[str],
        golden_output: Optional[str] = None,
        requirements: Optional[str] = None,
        assignment_name: str = "Task"
    ) -> Tuple[bool, Dict, Optional[str]]:
        """
        PRD F3.4: 마스터 평가 프롬프트로 평가 (1회, T=0)
        
        Args:
            participant_prompt: 참가자 프롬프트
            execution_outputs: 3회 실행 결과 리스트
            golden_output: 정답 산출물 (선택적)
            requirements: 과제 요구사항 (선택적)
            assignment_name: 과제명
            
        Returns:
            (성공 여부, 평가 결과 dict, 에러 메시지)
        """
        
        # 마스터 평가 프롬프트 구성
        master_prompt = self._build_master_grading_prompt(
            participant_prompt,
            execution_outputs,
            golden_output,
            requirements,
            assignment_name
        )
        
        # 평가 실행 (T=0, 재시도 포함)
        for retry in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a professional evaluator for prompt engineering competitions. Evaluate submissions objectively and consistently according to the rubric."
                        },
                        {
                            "role": "user", 
                            "content": master_prompt
                        }
                    ],
                    temperature=self.grading_temperature,
                    max_tokens=2000,
                    response_format={"type": "json_object"}
                )
                
                result_text = response.choices[0].message.content
                result = json.loads(result_text)
                
                # 점수 검증
                if not self._validate_grading_result(result):
                    return False, {}, "Invalid grading result format"
                
                return True, result, None
                
            except Exception as e:
                if retry < 2:
                    time.sleep(2 ** retry)
                    continue
                else:
                    return False, {}, f"Grading failed: {str(e)}"
        
        return False, {}, "Max retries exceeded"
    
    def _build_master_grading_prompt(
        self,
        participant_prompt: str,
        execution_outputs: List[str],
        golden_output: Optional[str],
        requirements: Optional[str],
        assignment_name: str
    ) -> str:
        """
        마스터 평가 프롬프트 생성
        PRD R2: 항목별 점수 구간 (정확성 50, 명확성 30, 일관성 20)
        """
        
        prompt = f"""# Prompt Engineering Competition Evaluation

## Assignment: {assignment_name}

## Participant's Prompt:
```
{participant_prompt}
```

## Execution Results (3 runs with temperature=0.1):

### Output 1:
```
{execution_outputs[0][:1500]}{'...' if len(execution_outputs[0]) > 1500 else ''}
```

### Output 2:
```
{execution_outputs[1][:1500]}{'...' if len(execution_outputs[1]) > 1500 else ''}
```

### Output 3:
```
{execution_outputs[2][:1500]}{'...' if len(execution_outputs[2]) > 1500 else ''}
```
"""
        
        if golden_output:
            prompt += f"""
## Golden Output (Expected Result):
```
{golden_output[:1500]}{'...' if len(golden_output) > 1500 else ''}
```
"""
        
        if requirements:
            prompt += f"""
## Requirements & Rubric:
{requirements}
"""
        
        prompt += """
## Evaluation Criteria:

### 1. 정확성 (Prompt Accuracy) - 50점
- 50점: 프롬프트 실행 결과가 목표 산출물과 내용/형식 모두 일치
- 30점: 핵심 내용은 일치하나, 일부 누락 요소가 있거나 형식이 불일치
- 20점 이하: 주요 내용이 누락되거나 구조 자체가 다름

### 2. 명확성 (Prompt Clarity) - 30점
- 30점: 명확한 역할 지시(예: '너는 데이터 분석가') + 단계별 수행 지침 + 논리적이고 직관적
- 20점: 이해 가능하지만 일부 모호한 표현이 포함됨
- 10점 이하: 구조나 지시문이 애매하거나 모순적

### 3. 구성 및 검증 (Prompt Validation & Consistency) - 20점
- 20점: 재실행 시 동일한 결과가 나오며 편차가 없음
- 10점: 경미한 편차가 있으나 핵심 내용은 유지됨
- 10점 이하: 매 실행마다 크게 다른 결과가 나옴

## Output Format (JSON):
{
  "accuracy_score": 50,
  "accuracy_feedback": "Detailed explanation...",
  "clarity_score": 30,
  "clarity_feedback": "Detailed explanation...",
  "consistency_score": 20,
  "consistency_feedback": "Detailed explanation with output comparison...",
  "total_score": 100,
  "overall_feedback": "Summary of strengths and areas for improvement..."
}

Evaluate objectively and provide constructive feedback in Korean.
"""
        
        return prompt
    
    def _validate_grading_result(self, result: Dict) -> bool:
        """평가 결과 검증"""
        required_keys = [
            "accuracy_score", "accuracy_feedback",
            "clarity_score", "clarity_feedback",
            "consistency_score", "consistency_feedback",
            "total_score", "overall_feedback"
        ]
        
        for key in required_keys:
            if key not in result:
                return False
        
        # 점수 범위 검증
        if not (0 <= result["accuracy_score"] <= 50):
            return False
        if not (0 <= result["clarity_score"] <= 30):
            return False
        if not (0 <= result["consistency_score"] <= 20):
            return False
        
        # 총점 검증
        expected_total = (
            result["accuracy_score"] + 
            result["clarity_score"] + 
            result["consistency_score"]
        )
        if abs(result["total_score"] - expected_total) > 0.1:
            return False
        
        return True
    
    def grade_submission(
        self,
        participant_prompt: str,
        input_file_content: Optional[str] = None,
        golden_output: Optional[str] = None,
        requirements: Optional[str] = None,
        assignment_name: str = "Task"
    ) -> Tuple[bool, Dict, List[str], Optional[str]]:
        """
        전체 채점 프로세스 실행
        
        Returns:
            (성공 여부, 평가 결과, 실행 결과 리스트, 에러 메시지)
        """
        
        # 1단계: 프롬프트 3회 실행
        success, outputs, error = self.execute_prompt_3_times(
            participant_prompt,
            input_file_content
        )
        
        if not success:
            return False, {}, [], error
        
        # 2단계: 마스터 평가 프롬프트로 평가
        success, grading_result, error = self.evaluate_outputs(
            participant_prompt,
            outputs,
            golden_output,
            requirements,
            assignment_name
        )
        
        if not success:
            return False, {}, outputs, error
        
        return True, grading_result, outputs, None


# 테스트 코드
if __name__ == "__main__":
    import os
    
    # API 키 확인
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        exit(1)
    
    # 엔진 초기화
    engine = GradingEngine(api_key)
    
    # 테스트 프롬프트
    test_prompt = """당신은 경영 보고서 작성 전문가입니다. 
다음 데이터를 분석하여 3가지 핵심 인사이트를 도출하고, 
각 인사이트에 대한 구체적인 근거를 제시하세요."""
    
    test_data = """
Q1 매출: 100억원
Q2 매출: 120억원
Q3 매출: 150억원
Q4 매출: 180억원
"""
    
    print("=== 채점 엔진 테스트 ===\n")
    
    # 1단계: 3회 실행
    print("1단계: 프롬프트 3회 실행 중...")
    success, outputs, error = engine.execute_prompt_3_times(test_prompt, test_data)
    
    if not success:
        print(f"실행 실패: {error}")
        exit(1)
    
    print("✅ 3회 실행 완료")
    for i, output in enumerate(outputs, 1):
        print(f"\n출력 {i} (처음 100자):")
        print(output[:100] + "...")
    
    # 2단계: 평가
    print("\n2단계: 마스터 평가 프롬프트로 평가 중...")
    
    golden = """
인사이트 1: 매출이 지속적으로 증가하고 있으며, 특히 하반기(Q3-Q4)에 가속화되고 있습니다.
인사이트 2: 전분기 대비 성장률이 Q1-Q2: 20%, Q2-Q3: 25%, Q3-Q4: 20%로 Q3에 최고점을 기록했습니다.
인사이트 3: 연간 총 매출은 550억원으로, Q4 단독으로 전체의 32.7%를 차지하여 계절성이 있을 가능성이 있습니다.
"""
    
    requirements = """
- 데이터에 기반한 구체적인 인사이트 3개 이상
- 각 인사이트에 대한 정량적 근거 제시
- 명확하고 간결한 문장 구조
"""
    
    success, result, error = engine.evaluate_outputs(
        test_prompt,
        outputs,
        golden,
        requirements,
        "Task A - 경영 보고서"
    )
    
    if not success:
        print(f"평가 실패: {error}")
        exit(1)
    
    print("✅ 평가 완료\n")
    print("=== 평가 결과 ===")
    print(f"정확성: {result['accuracy_score']}/50")
    print(f"명확성: {result['clarity_score']}/30")
    print(f"일관성: {result['consistency_score']}/20")
    print(f"총점: {result['total_score']}/100")
    print(f"\n종합 피드백:\n{result['overall_feedback']}")
