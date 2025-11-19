"""
파일 파싱 유틸리티
PDF, TXT, Excel 파일을 텍스트로 변환
"""

import os
from typing import Optional, Tuple
import PyPDF2
import pandas as pd
from io import BytesIO


class FileParser:
    """파일을 텍스트로 변환하는 파서"""
    
    @staticmethod
    def parse_file(file_content: bytes, file_type: str) -> Tuple[bool, str]:
        """
        파일을 텍스트로 파싱
        
        Args:
            file_content: 파일 바이너리 내용
            file_type: 'pdf', 'txt', 'excel'
            
        Returns:
            (성공 여부, 파싱된 텍스트 또는 에러 메시지)
        """
        try:
            if file_type == 'txt':
                return FileParser._parse_txt(file_content)
            elif file_type == 'pdf':
                return FileParser._parse_pdf(file_content)
            elif file_type == 'excel':
                return FileParser._parse_excel(file_content)
            else:
                return False, f"Unsupported file type: {file_type}"
        except Exception as e:
            return False, f"Parse error: {str(e)}"
    
    @staticmethod
    def _parse_txt(file_content: bytes) -> Tuple[bool, str]:
        """TXT 파일 파싱"""
        try:
            # UTF-8 시도
            text = file_content.decode('utf-8')
            return True, text
        except UnicodeDecodeError:
            try:
                # CP949 시도 (한글 Windows)
                text = file_content.decode('cp949')
                return True, text
            except:
                return False, "Unable to decode text file"
    
    @staticmethod
    def _parse_pdf(file_content: bytes) -> Tuple[bool, str]:
        """PDF 파일 파싱"""
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            text_parts = []
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    text_parts.append(f"--- Page {page_num} ---\n{text}")
            
            if not text_parts:
                return False, "PDF contains no extractable text"
            
            return True, "\n\n".join(text_parts)
        except Exception as e:
            return False, f"PDF parsing failed: {str(e)}"
    
    @staticmethod
    def _parse_excel(file_content: bytes) -> Tuple[bool, str]:
        """
        Excel 파일 파싱
        PRD R1.2: Excel을 Markdown Table 또는 CSV로 변환
        """
        try:
            # Excel 파일 읽기
            excel_file = BytesIO(file_content)
            
            # 모든 시트 읽기
            xls = pd.ExcelFile(excel_file)
            text_parts = []
            
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                
                # Markdown Table 형식으로 변환
                text_parts.append(f"=== Sheet: {sheet_name} ===\n")
                text_parts.append(df.to_markdown(index=False))
                text_parts.append("\n")
                
                # 기본 통계 추가
                text_parts.append(f"--- Summary ---")
                text_parts.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")
                text_parts.append(f"Columns: {', '.join(df.columns.tolist())}\n")
            
            return True, "\n".join(text_parts)
        except Exception as e:
            return False, f"Excel parsing failed: {str(e)}"
    
    @staticmethod
    def detect_file_type(filename: str) -> Optional[str]:
        """
        파일명에서 파일 타입 추출
        
        Returns:
            'pdf', 'txt', 'excel', or None
        """
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == '.pdf':
            return 'pdf'
        elif ext == '.txt':
            return 'txt'
        elif ext in ['.xlsx', '.xls', '.xlsm']:
            return 'excel'
        else:
            return None


# 테스트 코드
if __name__ == "__main__":
    # TXT 테스트
    txt_content = "안녕하세요.\n이것은 테스트 파일입니다.".encode('utf-8')
    success, result = FileParser.parse_file(txt_content, 'txt')
    print("TXT Test:", success, result[:100] if success else result)
    
    # 파일 타입 감지 테스트
    print("\nFile Type Detection:")
    print("report.pdf ->", FileParser.detect_file_type("report.pdf"))
    print("data.xlsx ->", FileParser.detect_file_type("data.xlsx"))
    print("prompt.txt ->", FileParser.detect_file_type("prompt.txt"))
