import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# </script> 태그 찾기
script_end = html.rfind('</script>')

if script_end == -1:
    print("❌ </script> 태그를 찾을 수 없습니다")
    exit(1)

# 추가할 JavaScript 함수
js_functions = '''
// ============================================================================
// 엑셀 일괄 업로드 함수
// ============================================================================

async function bulkUploadSubmissions() {
    const taskId = document.getElementById('bulk-upload-task').value;
    const fileInput = document.getElementById('bulk-excel-file');
    
    if (!taskId) {
        alert('과제를 선택해주세요');
        return;
    }
    
    if (!fileInput.files || fileInput.files.length === 0) {
        alert('엑셀 파일을 선택해주세요');
        return;
    }
    
    const file = fileInput.files[0];
    
    // 파일 확장자 확인
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        alert('엑셀 파일(.xlsx, .xls)만 업로드 가능합니다');
        return;
    }
    
    // 확인 메시지
    if (!confirm(`${file.name} 파일을 업로드하여 제출물을 일괄 등록하시겠습니까?`)) {
        return;
    }
    
    // FormData 생성
    const formData = new FormData();
    formData.append('task_id', taskId);
    formData.append('excel_file', file);
    
    try {
        // 업로드 중 UI
        const btn = event.target;
        btn.disabled = true;
        btn.textContent = '업로드 중...';
        
        const response = await fetch('/bulk-upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert(`✅ 일괄 업로드 완료!\\n생성: ${result.created}건\\n건너뜀: ${result.skipped}건`);
            
            // 에러가 있으면 표시
            if (result.errors && result.errors.length > 0) {
                console.error('업로드 오류:', result.errors);
                alert('일부 오류:\\n' + result.errors.slice(0, 5).join('\\n'));
            }
            
            // 새로고침
            loadSubmissions();
            loadPractitioners();
            
            // 입력 초기화
            fileInput.value = '';
            document.getElementById('bulk-upload-task').value = '';
            
        } else {
            alert(`❌ 업로드 실패: ${result.detail || '알 수 없는 오류'}`);
        }
        
    } catch (error) {
        console.error('업로드 오류:', error);
        alert('업로드 중 오류가 발생했습니다: ' + error.message);
    } finally {
        const btn = event.target;
        btn.disabled = false;
        btn.textContent = '📤 일괄 업로드 실행';
    }
}

// 과제 선택 드롭다운 로드 함수 수정 (일괄 업로드용 추가)
const originalLoadTasks = loadTasks;
async function loadTasks() {
    await originalLoadTasks();
    
    // 일괄 업로드 드롭다운도 업데이트
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
}

'''

# </script> 전에 삽입
html = html[:script_end] + js_functions + '\n' + html[script_end:]

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ JavaScript 함수 추가 완료")
