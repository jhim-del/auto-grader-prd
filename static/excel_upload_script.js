// ============================================================================
// 엑셀 일괄 업로드 함수
// ============================================================================

async function bulkUploadSubmissions() {
    const taskId = document.getElementById('bulk-upload-task').value;
    const fileInput = document.getElementById('bulk-excel-file');
    const statusDiv = document.getElementById('bulk-upload-status');
    
    // 유효성 검사
    if (!taskId) {
        alert('⚠️ 과제를 선택해주세요');
        return;
    }
    
    if (!fileInput.files || fileInput.files.length === 0) {
        alert('⚠️ 엑셀 파일을 선택해주세요');
        return;
    }
    
    const file = fileInput.files[0];
    
    // 파일 확장자 확인
    const fileName = file.name.toLowerCase();
    if (!fileName.endsWith('.xlsx') && !fileName.endsWith('.xls')) {
        alert('⚠️ 엑셀 파일(.xlsx, .xls)만 업로드 가능합니다');
        return;
    }
    
    // 확인 메시지
    if (!confirm(`📁 ${file.name}\n\n이 파일을 업로드하여 제출물을 일괄 등록하시겠습니까?`)) {
        return;
    }
    
    // FormData 생성
    const formData = new FormData();
    formData.append('task_id', taskId);
    formData.append('excel_file', file);
    
    try {
        // 업로드 중 UI 표시
        statusDiv.style.display = 'block';
        statusDiv.style.background = '#FED3DB';
        statusDiv.style.border = '2px solid #FA0030';
        statusDiv.innerHTML = `
            <div style="text-align: center;">
                <strong style="color: #FA0030;">⏳ 업로드 중...</strong>
                <p style="color: #666; margin-top: 5px;">잠시만 기다려주세요</p>
            </div>
        `;
        
        // 버튼 비활성화
        const btn = event.target;
        btn.disabled = true;
        btn.style.opacity = '0.5';
        btn.textContent = '업로드 중...';
        
        // API 호출
        const response = await fetch('/bulk-upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // 성공 메시지
            statusDiv.style.background = '#D4F3FC';
            statusDiv.style.border = '2px solid #93E6F5';
            statusDiv.innerHTML = `
                <div>
                    <strong style="color: #FA0030;">✅ 일괄 업로드 완료!</strong>
                    <ul style="margin-top: 10px; padding-left: 20px; color: #333;">
                        <li>생성된 제출물: <strong>${result.created}건</strong></li>
                        <li>건너뛴 항목: ${result.skipped}건</li>
                    </ul>
                    ${result.errors && result.errors.length > 0 ? `
                        <p style="color: #cc0000; margin-top: 10px;">
                            ⚠️ 일부 오류 발생 (${result.errors.length}건)
                        </p>
                    ` : ''}
                </div>
            `;
            
            // 에러 상세 로그
            if (result.errors && result.errors.length > 0) {
                console.error('업로드 오류 상세:', result.errors);
            }
            
            // 목록 새로고침
            setTimeout(() => {
                loadSubmissions();
                loadPractitioners();
                loadDashboard();
            }, 500);
            
            // 입력 초기화
            fileInput.value = '';
            
        } else {
            // 실패 메시지
            statusDiv.style.background = '#ffe0e0';
            statusDiv.style.border = '2px solid #ff4444';
            statusDiv.innerHTML = `
                <div>
                    <strong style="color: #cc0000;">❌ 업로드 실패</strong>
                    <p style="color: #666; margin-top: 5px;">${result.detail || '알 수 없는 오류가 발생했습니다'}</p>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('업로드 오류:', error);
        statusDiv.style.display = 'block';
        statusDiv.style.background = '#ffe0e0';
        statusDiv.style.border = '2px solid #ff4444';
        statusDiv.innerHTML = `
            <div>
                <strong style="color: #cc0000;">❌ 업로드 오류</strong>
                <p style="color: #666; margin-top: 5px;">${error.message}</p>
            </div>
        `;
    } finally {
        // 버튼 활성화
        const btn = event.target;
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.textContent = '📤 일괄 업로드 실행';
    }
}

// 페이지 로드 시 과제 목록을 일괄 업로드 드롭다운에도 채우기
document.addEventListener('DOMContentLoaded', function() {
    // 기존 loadTasks 함수 실행 후 일괄 업로드 드롭다운도 업데이트
    const originalLoadTasks = window.loadTasks;
    if (originalLoadTasks) {
        window.loadTasks = async function() {
            await originalLoadTasks();
            await updateBulkUploadTaskDropdown();
        };
    }
});

async function updateBulkUploadTaskDropdown() {
    try {
        const response = await fetch('/tasks');
        const tasks = await response.json();
        
        const bulkSelect = document.getElementById('bulk-upload-task');
        if (bulkSelect) {
            bulkSelect.innerHTML = '<option value="">과제를 선택하세요</option>';
            tasks.forEach(task => {
                const option = document.createElement('option');
                option.value = task.id;
                option.textContent = task.title;
                bulkSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('과제 목록 로드 실패:', error);
    }
}
