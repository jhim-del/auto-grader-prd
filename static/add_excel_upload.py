import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 제출물 관리 섹션 찾기
submissions_section = '''        <div id="submissions" class="tab-content">
            <div class="section-title">제출물 관리</div>
            <button class="btn btn-primary" onclick="showSubmissionModal()">+ 새 제출물 등록</button>'''

excel_upload_section = '''        <div id="submissions" class="tab-content">
            <div class="section-title">제출물 관리</div>
            
            <!-- 엑셀 일괄 업로드 섹션 -->
            <div style="background: #D4F3FC; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #FA0030; margin-bottom: 15px;">📊 엑셀 일괄 업로드</h3>
                <p style="margin-bottom: 15px; color: #333;">
                    엑셀 파일 형식: <strong>1행(이름 | 프롬프트)</strong>, 2행부터 참가자 데이터
                </p>
                
                <div class="form-group">
                    <label>과제 선택:</label>
                    <select id="bulk-upload-task">
                        <option value="">과제를 선택하세요</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>엑셀 파일 업로드:</label>
                    <input type="file" id="bulk-excel-file" accept=".xlsx,.xls" style="display: block; margin-top: 10px;">
                </div>
                
                <button class="btn btn-primary" onclick="bulkUploadSubmissions()">
                    📤 일괄 업로드 실행
                </button>
            </div>
            
            <button class="btn btn-secondary" onclick="showSubmissionModal()">+ 개별 제출물 등록</button>'''

html = html.replace(submissions_section, excel_upload_section)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ 엑셀 업로드 UI 추가 완료")
