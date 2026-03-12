/**
 * Task-Chat Full — Основная логика
 * Обработка непрочитанных сообщений, модальные окна, утилиты
 */

// Глобальные переменные
window.unreadData = null;

// ========================================
// Tooltip для мобильных (полное ФИО по клику)
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    if (window.innerWidth <= 768) {
        // Мобильные устройства - показ tooltip по клику
        const tooltipElements = document.querySelectorAll(
            'td strong[title], .participant-name[title], .doctor-name[title], ' +
            '.chat-partner-info h3[title], .user-role[title]'
        );
        
        tooltipElements.forEach(el => {
            el.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Если уже открыт - закрываем
                if (this.classList.contains('show-tooltip')) {
                    this.classList.remove('show-tooltip');
                    return;
                }
                
                // Закрываем другие открытые tooltip
                document.querySelectorAll('.show-tooltip').forEach(item => {
                    item.classList.remove('show-tooltip');
                });
                
                // Открываем текущий
                this.classList.add('show-tooltip');
            });
        });
        
        // Закрытие tooltip по клику вне элемента
        document.addEventListener('click', function(e) {
            const tooltipElements = document.querySelectorAll(
                'td strong[title], .participant-name[title], .doctor-name[title], ' +
                '.chat-partner-info h3[title], .user-role[title]'
            );
            
            let clickedOnTooltip = false;
            tooltipElements.forEach(el => {
                if (el.contains(e.target)) {
                    clickedOnTooltip = true;
                }
            });
            
            if (!clickedOnTooltip) {
                document.querySelectorAll('.show-tooltip').forEach(item => {
                    item.classList.remove('show-tooltip');
                });
            }
        });
    }
});

// ========================================
// Проверка непрочитанных сообщений
// ========================================
function checkUnreadMessages() {
    if (!window.currentUserId) return;

    fetch('/unread_messages')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('unreadCount');
            if (badge && data.total_unread > 0) {
                let badgeText = data.total_unread.toString();
                if (data.total_unread > 99) {
                    badgeText = '99+';
                } else if (data.total_unread > 9 && window.innerWidth <= 768) {
                    badge.style.fontSize = '9px';
                }
                badge.textContent = badgeText;
                badge.style.display = 'flex';
                
                // Обновляем заголовок вкладки
                const originalTitle = document.title.replace(/^\(\d+\)\s*/, '');
                document.title = `(${data.total_unread}) ${originalTitle}`;
            } else if (badge) {
                badge.style.display = 'none';
                // Восстанавливаем заголовок
                document.title = document.title.replace(/^\(\d+\)\s*/, '');
            }

            // Сохраняем данные для модального окна
            window.unreadData = data;
        })
        .catch(error => console.error('Ошибка проверки сообщений:', error));
}

// ========================================
// Модальное окно непрочитанных сообщений
// ========================================
function showUnreadTasks() {
    if (!window.unreadData || window.unreadData.total_unread === 0) {
        alert('Нет непрочитанных сообщений');
        return;
    }

    const modal = document.getElementById('unreadModal');
    const list = document.getElementById('unreadTasksList');

    list.innerHTML = '';

    if (window.unreadData.tasks_with_unread.length === 0) {
        list.innerHTML = '<p class="no-messages">Нет непрочитанных сообщений</p>';
    } else {
        window.unreadData.tasks_with_unread.forEach(task => {
            const taskItem = document.createElement('div');
            taskItem.className = 'unread-task-item';
            taskItem.innerHTML = `
                <div class="unread-task-info">
                    <h4>${task.task_title}</h4>
                    <p>
                        <span class="unread-count">${task.unread_count} непрочитанных</span>
                        <span class="last-sender">От: ${task.last_sender || 'Неизвестно'}</span>
                    </p>
                </div>
                <a href="/task/${task.task_id}/chat" class="btn btn-small btn-primary">
                    <i class="fas fa-comment"></i> Перейти в чат
                </a>
            `;
            list.appendChild(taskItem);
        });
    }

    modal.style.display = 'block';
}

function closeUnreadModal() {
    document.getElementById('unreadModal').style.display = 'none';
}

// Закрыть модальное окно при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('unreadModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
    
    // Также закрываем модальное окно файлов
    const filesModal = document.getElementById('filesModal');
    if (event.target == filesModal) {
        closeFilesModal();
    }
}

// ========================================
// Утилиты
// ========================================

// Проверка на мобильное устройство
function isMobile() {
    return window.innerWidth <= 768;
}

// Форматирование времени
function formatTime(date) {
    return date.getHours().toString().padStart(2, '0') + ':' +
           date.getMinutes().toString().padStart(2, '0');
}

// Экранирование HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========================================
// Инициализация
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    // Автоматически закрывать flash-сообщения через 5 секунд
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            setTimeout(() => flash.remove(), 300);
        }, 5000);
    });

    // Запуск проверки непрочитанных сообщений
    if (window.currentUserId) {
        setInterval(checkUnreadMessages, 10000);
        checkUnreadMessages(); // Первая проверка сразу
    }
    
    // Адаптация для мобильных
    function adaptForMobile() {
        const isMobileView = window.innerWidth <= 768;
        const userInfo = document.querySelector('.user-info-mobile .user-role');

        if (isMobileView && userInfo) {
            userInfo.classList.add('mobile-compact');
        } else if (userInfo) {
            userInfo.classList.remove('mobile-compact');
        }
    }

    adaptForMobile();
    window.addEventListener('resize', adaptForMobile);
    
    // Фикс для мобильных: предотвращение zoom при фокусе
    if (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) {
        document.addEventListener('focusin', function(e) {
            if (e.target.tagName === 'INPUT' || 
                e.target.tagName === 'TEXTAREA' || 
                e.target.tagName === 'SELECT') {
                setTimeout(() => {
                    e.target.style.fontSize = '16px';
                }, 100);
            }
        });
    }
});

// ========================================
// Функции для работы с файлами (общие)
// ========================================
let currentTaskId = null;
let currentTaskStatus = null;

async function showTaskFiles(taskId) {
    console.log('Opening files modal for task:', taskId);

    currentTaskId = taskId;
    const modal = document.getElementById('filesModal');
    const content = document.getElementById('filesModalContent');

    // Показываем загрузку
    content.innerHTML = '<div class="files-loading"><i class="fas fa-spinner fa-spin"></i> Загрузка файлов...</div>';
    modal.style.display = 'flex';

    try {
        const response = await fetch(`/task/${taskId}/files`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        showFilesList(content, data, taskId);
    } catch (error) {
        console.error('Error loading files:', error);
        showFilesError(content, error.message);
    }
}

function showFilesList(content, data, taskId) {
    const { files, stats, task_title } = data;

    let filesHtml = '<div class="files-grid">';

    filesHtml += `<div class="files-header" style="grid-column: 1/-1; margin-bottom: 20px;">
        <h4>Файлы задачи: ${task_title}</h4>
        <div class="files-stats" style="display: flex; gap: 15px; margin-top: 10px; flex-wrap: wrap;">
            <span class="stat-item"><i class="fas fa-image"></i> Изображений: ${stats.images}</span>
            <span class="stat-item"><i class="fas fa-file-pdf"></i> PDF: ${stats.pdfs}</span>
            <span class="stat-item"><i class="fas fa-file-archive"></i> Архивов: ${stats.archives}</span>
            <span class="stat-item"><i class="fas fa-file-medical"></i> DICOM: ${stats.dicom}</span>
            <span class="stat-item"><i class="fas fa-file-alt"></i> Других: ${stats.other}</span>
        </div>
    </div>`;

    if (files.length === 0) {
        filesHtml += `
        <div class="no-files" style="grid-column: 1/-1;">
            <i class="fas fa-file-excel fa-3x"></i>
            <h4>Файлы отсутствуют</h4>
            <p>К этой задаче еще не прикреплены файлы</p>
        </div>`;
    } else {
        files.forEach((file) => {
            filesHtml += `
            <div class="file-card" data-file-id="${file.id}">
                <div class="file-preview">
                    ${file.is_image ?
                        `<img src="${file.view_url || file.download_url}"
                              alt="${file.original_filename}"
                              onclick="openFileFullscreen('${file.view_url || file.download_url}', '${file.original_filename.replace(/'/g, "\\'")}')">` :
                        `<div class="file-icon">
                            <i class="fas ${file.icon_class}"></i>
                        </div>`
                    }
                </div>
                <div class="file-info">
                    <div class="file-name" title="${file.original_filename}">
                        ${file.original_filename}
                    </div>
                    <div class="file-meta">
                        <span class="file-size">${file.file_size_mb} MB</span>
                        <span class="file-date">${file.uploaded_at}</span>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-small btn-primary"
                                onclick="downloadFile(${taskId}, ${file.id})">
                            <i class="fas fa-download"></i> Скачать
                        </button>
                        ${file.is_image || file.is_pdf ?
                            `<button class="btn btn-small btn-secondary"
                                    onclick="window.open('${file.view_url || file.download_url}', '_blank')">
                                <i class="fas fa-expand"></i> Открыть
                            </button>` :
                            ''
                        }
                        ${window.currentUserRole === 'admin' || window.currentUserId === file.uploader_id ?
                            `<button class="btn btn-small btn-danger"
                                    onclick="deleteFile(${taskId}, ${file.id}, this)">
                                <i class="fas fa-trash"></i> Удалить
                            </button>` :
                            ''
                        }
                    </div>
                </div>
            </div>`;
        });
    }

    filesHtml += '</div>';
    content.innerHTML = filesHtml;
}

function showFilesError(content, errorMessage) {
    content.innerHTML = `
        <div class="error" style="text-align: center; padding: 40px;">
            <i class="fas fa-exclamation-triangle fa-3x" style="color: #e74c3c; margin-bottom: 20px;"></i>
            <h4>Ошибка при загрузке файлов</h4>
            <p style="color: #7f8c8d;">${errorMessage}</p>
            <button class="btn btn-primary" onclick="showTaskFiles(${currentTaskId})" style="margin-top: 15px;">
                <i class="fas fa-redo"></i> Повторить попытку
            </button>
        </div>
    `;
}

function closeFilesModal() {
    document.getElementById('filesModal').style.display = 'none';
    document.getElementById('filesModalContent').innerHTML = '';
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(ext)) {
        return 'fa-file-image';
    } else if (ext === 'pdf') {
        return 'fa-file-pdf';
    } else if (ext === 'dcm') {
        return 'fa-file-medical';
    } else if (['zip', 'rar', '7z'].includes(ext)) {
        return 'fa-file-archive';
    } else {
        return 'fa-file-alt';
    }
}

function downloadFile(taskId, fileId) {
    window.open(`/task/${taskId}/files/${fileId}/download`, '_blank');
}

async function deleteFile(taskId, fileId, button) {
    if (!confirm('Вы уверены, что хотите удалить этот файл? Это действие нельзя отменить.')) return;

    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Удаление...';

    try {
        const response = await fetch(`/task/${taskId}/files/${fileId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            const fileCard = button.closest('.file-card');
            if (fileCard) {
                fileCard.classList.add('removing');
                setTimeout(() => fileCard.remove(), 300);
            }
            showNotification('Файл успешно удален', 'success');
        } else {
            throw new Error(data.error || 'Ошибка при удалении файла');
        }
    } catch (error) {
        console.error('Error deleting file:', error);
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-trash"></i> Удалить';
        showNotification('Ошибка при удалении файла: ' + error.message, 'error');
    }
}

function openFileFullscreen(url, filename) {
    const fullscreen = document.createElement('div');
    fullscreen.className = 'file-fullscreen';
    fullscreen.id = 'fileFullscreen';
    fullscreen.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.95);
        z-index: 99999 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        animation: fadeIn 0.3s ease-out;
        cursor: zoom-out;
    `;

    fullscreen.innerHTML = `
        <div class="fullscreen-header" style="position: absolute; top: 20px; left: 20px; color: white; z-index: 100000 !important;">
            <h4 style="margin: 0; color: white;">${filename}</h4>
        </div>
        <button class="fullscreen-close" onclick="closeFileFullscreen()"
                style="position: absolute; top: 20px; right: 30px; background: none; border: none; color: white; font-size: 40px; font-weight: bold; cursor: pointer; z-index: 100001 !important; transition: color 0.3s;"
                onmouseover="this.style.color='#4f46e5'" onmouseout="this.style.color='white'">
            <i class="fas fa-times"></i>
        </button>
        <div class="fullscreen-content" style="max-width: 90%; max-height: 85vh; z-index: 100000 !important;">
            <img src="${url}" alt="${filename}" style="max-width: 100%; max-height: 85vh; object-fit: contain; cursor: zoom-out; border-radius: 8px; box-shadow: 0 20px 60px rgba(0,0,0,0.5);">
        </div>
        <div style="position: absolute; bottom: 30px; color: white; font-size: 14px; opacity: 0.8; z-index: 100000 !important;">
            <i class="fas fa-mouse-pointer"></i> Кликните для закрытия или нажмите ESC
        </div>
    `;

    // Закрытие по клику на fullscreen
    fullscreen.onclick = function(e) {
        if (e.target === fullscreen || e.target.tagName === 'IMG') {
            closeFileFullscreen();
        }
    };

    document.body.appendChild(fullscreen);
    document.body.style.overflow = 'hidden';

    // Закрытие по ESC
    const closeOnEsc = (e) => {
        if (e.key === 'Escape') {
            closeFileFullscreen();
        }
    };
    document.addEventListener('keydown', closeOnEsc);
}

function closeFileFullscreen() {
    const fullscreen = document.getElementById('fileFullscreen');
    if (fullscreen) {
        fullscreen.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => {
            fullscreen.remove();
            document.body.style.overflow = '';
        }, 300);
    }
}

// Добавляем анимацию fadeOut
if (!document.getElementById('fullscreen-styles')) {
    const style = document.createElement('style');
    style.id = 'fullscreen-styles';
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
        .file-fullscreen {
            animation: fadeIn 0.3s ease-out;
        }
    `;
    document.head.appendChild(style);
}

async function addFilesToTask(taskId) {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = '.jpg,.jpeg,.png,.gif,.bmp,.webp,.pdf,.dcm,.zip,.rar,.doc,.docx,.xls,.xlsx';

    input.onchange = async function(e) {
        const files = e.target.files;
        if (files.length === 0) return;

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        try {
            const response = await fetch(`/task/${taskId}/add_files`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                showNotification(`Успешно загружено ${data.uploaded_files.length} файлов`, 'success');
                if (typeof showTaskFiles === 'function') {
                    await showTaskFiles(taskId);
                }
                // Обновляем страницу если мы на странице задачи
                if (typeof TASK_ID !== 'undefined' && TASK_ID === taskId) {
                    location.reload();
                }
            } else {
                throw new Error(data.errors ? data.errors.join(', ') : 'Ошибка загрузки файлов');
            }
        } catch (error) {
            console.error('Error uploading files:', error);
            showNotification('Ошибка при загрузке файлов: ' + error.message, 'error');
        }
    };

    input.click();
}

// ========================================
// Уведомления
// ========================================
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#2ecc71' : type === 'error' ? '#e74c3c' : '#3498db'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
        max-width: 300px;
    `;

    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}
