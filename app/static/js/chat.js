/**
 * Task-Chat Full — Логика чата
 * Отправка сообщений, polling, индикатор "печатает"
 */

// Глобальные переменные
let isTyping = false;
let typingTimeout = null;
let lastMessageId = typeof LAST_MESSAGE_ID !== 'undefined' ? LAST_MESSAGE_ID : 0;
let shouldScrollToBottom = true;
let isFirstLoad = true;
let isPartnerTyping = false;
let partnerTypingTimeout = null;

// ========================================
// Инициализация
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('Chat page loaded, initializing...');

    // Инициализируем время для существующих сообщений
    initMessageTimes();

    // Прокрутка вниз при загрузке
    const messagesList = document.getElementById('messagesList');
    if (messagesList) {
        setTimeout(() => {
            scrollToBottom();
            focusMessageInputOnMobile();
        }, 100);
    }

    // Настройка авторазмера textarea
    setupMessageInput();

    // Запуск обновления сообщений
    startMessagePolling();

    // Настройка формы отправки
    setupMessageForm();

    // Запуск проверки индикатора "печатает"
    setInterval(checkPartnerTyping, 1000);

    // Запуск проверки статуса задачи (каждые 3 секунды)
    startTaskStatusPolling();

    // Обработка изменения размера окна (открытие/закрытие клавиатуры)
    window.addEventListener('resize', handleMobileResize);
});

// ========================================
// Обновление статуса задачи
// ========================================
let lastTaskStatus = null;
let lastTaskTitle = null;

function startTaskStatusPolling() {
    // Первоначальная проверка
    checkTaskStatus();

    // Проверка каждые 3 секунды
    setInterval(checkTaskStatus, 3000);
}

async function checkTaskStatus() {
    try {
        const response = await fetch(`/api/task/${TASK_ID}`);
        const data = await response.json();

        if (!data || data.error) return;

        // Обновляем статус задачи
        if (data.status && data.status !== lastTaskStatus) {
            updateTaskStatusBadge(data.status);
            lastTaskStatus = data.status;

            // Показываем уведомление
            showNotification(`Статус задачи изменен на "${getStatusText(data.status)}"`, 'info');
        }

        // Обновляем название задачи
        if (data.title && data.title !== lastTaskTitle) {
            updateTaskTitle(data.title);
            lastTaskTitle = data.title;
        }

        // Обновляем информацию о задаче в панели
        updateTaskDetailsPanel(data);

    } catch (error) {
        console.error('Error checking task status:', error);
    }
}

function updateTaskTitle(title) {
    // Обновляем заголовок в шапке чата
    const titleEl = document.getElementById('taskTitle');
    if (titleEl) {
        const desktopSpan = titleEl.querySelector('.task-title-desktop');
        const mobileSpan = titleEl.querySelector('.task-title-mobile');
        
        if (desktopSpan) desktopSpan.textContent = title;
        if (mobileSpan) mobileSpan.textContent = '#' + title.split('#').pop();
        
        // Обновляем data-атрибуты
        titleEl.setAttribute('data-full-title', title);
    }

    // Обновляем заголовок в панели информации о задаче (если есть)
    const taskInfoTitle = document.querySelector('.task-info-title');
    if (taskInfoTitle) {
        taskInfoTitle.textContent = title;
    }
}

function updateTaskDetailsPanel(data) {
    // Обновляем поля в панели информации о задаче
    const fields = {
        'patient_card': data.patient_card,
        'research_type': getResearchTypeDisplay(data.research_type),
        'expert_group': data.expert_group,
        'ct_diagnostic': data.ct_diagnostic,
        'treatment': data.treatment
    };

    for (const [key, value] of Object.entries(fields)) {
        const el = document.querySelector(`[data-field="${key}"]`);
        if (el) {
            if (value && value !== 'Нет данных') {
                el.textContent = value;
                el.parentElement.style.display = '';
            } else {
                el.parentElement.style.display = 'none';
            }
        }
    }
}

function getResearchTypeDisplay(type) {
    if (!type) return '';
    const types = {
        'import_ct': 'Импорт CT',
        'import_ct_diag': 'Импорт CT-диагностики',
        'mr': 'Импорт MR',
        'pet': 'Импорт PET'
    };
    return types[type] || type;
}

function updateTaskStatusBadge(status) {
    // Обновляем бейдж в шапке чата
    const statusBadge = document.querySelector('.task-status-badge .task-status');
    if (statusBadge) {
        statusBadge.className = `task-status status-${status}`;
        statusBadge.innerHTML = getStatusIcon(status) + ` <span class="status-text">${getStatusText(status)}</span>`;
    }
    
    // Обновляем бейдж в панели информации о задаче (если есть)
    const statusSelect = document.querySelector('.status-select');
    if (statusSelect) {
        statusSelect.value = status;
    }
}

function getStatusIcon(status) {
    const icons = {
        'pending': '<i class="fas fa-clock"></i>',
        'in_progress': '<i class="fas fa-spinner"></i>',
        'completed': '<i class="fas fa-check"></i>',
        'cancelled': '<i class="fas fa-ban"></i>'
    };
    return icons[status] || '';
}

function getStatusText(status) {
    const texts = {
        'pending': 'Ожидает',
        'in_progress': 'В работе',
        'completed': 'Выполнена',
        'cancelled': 'Отменена'
    };
    return texts[status] || status;
}

// ========================================
// Форматирование времени
// ========================================
function initMessageTimes() {
    const messageTimes = document.querySelectorAll('.message-time');
    messageTimes.forEach(element => {
        const timestamp = element.getAttribute('data-timestamp');
        if (timestamp) {
            try {
                const date = new Date(timestamp);
                if (!isNaN(date.getTime())) {
                    const timeStr = date.getHours().toString().padStart(2, '0') + ':' +
                                   date.getMinutes().toString().padStart(2, '0');
                    // Сохраняем только время, статус оставляем
                    const statusHtml = element.querySelector('.message-status')?.outerHTML || '';
                    element.innerHTML = timeStr + (statusHtml ? ' ' + statusHtml : '');
                }
            } catch (e) {
                console.error('Error parsing date:', e);
            }
        }
    });
}

// ========================================
// Прокрутка
// ========================================
function scrollToBottom() {
    const container = document.getElementById('messagesContainer');
    if (!container) return;

    shouldScrollToBottom = true;

    setTimeout(() => {
        container.scrollTop = container.scrollHeight;

        if (isMobile()) {
            setTimeout(() => {
                const messagesList = document.getElementById('messagesList');
                if (messagesList && messagesList.lastElementChild) {
                    messagesList.lastElementChild.scrollIntoView({
                        behavior: 'smooth',
                        block: 'end'
                    });
                }
            }, 100);
        }
    }, 50);
}

function isAtBottom() {
    const container = document.getElementById('messagesContainer');
    if (!container) return true;

    const threshold = isMobile() ? 150 : 100; // Больше порог на мобильных
    const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    return distanceFromBottom <= threshold;
}

function isMobile() {
    return window.innerWidth <= 768;
}

// Обработка изменения размера окна (открытие клавиатуры)
function handleMobileResize() {
    if (isMobile()) {
        // При изменении размера (открытии клавиатуры) прокручиваем вниз
        setTimeout(() => {
            scrollToBottom();
        }, 300);
    }
}

function focusMessageInputOnMobile() {
    if (isMobile()) {
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            setTimeout(() => {
                messageInput.focus({ preventScroll: true });
                setTimeout(() => {
                    messageInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 200);
            }, 300);
        }
    }
}

// ========================================
// Поле ввода сообщений
// ========================================
function setupMessageInput() {
    const textarea = document.getElementById('messageInput');
    if (!textarea) return;

    // Авторазмер
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        const newHeight = Math.min(this.scrollHeight, 120);
        this.style.height = newHeight + 'px';

        // Отправляем статус "печатает"
        sendTypingStatus();

        if (isMobile() && this === document.activeElement) {
            setTimeout(() => {
                this.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 100);
        }
    });

    // Обработка Enter
    textarea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            // На мобильных Enter добавляет перенос строки
            // Отправка только по кнопке
            if (isMobile()) {
                // Просто добавляем перенос строки
                e.preventDefault();
                const cursorPos = this.selectionStart;
                const textBefore = this.value.substring(0, cursorPos);
                const textAfter = this.value.substring(cursorPos);

                this.value = textBefore + '\n' + textAfter;

                // Перемещаем курсор после переноса строки
                this.selectionStart = this.selectionEnd = cursorPos + 1;

                // Обновляем высоту
                this.dispatchEvent(new Event('input'));
                return;
            }
            
            // На десктопе Shift+Enter - перенос, Enter - отправка
            if (e.shiftKey) {
                // Shift+Enter - перенос строки
                e.preventDefault();
                const cursorPos = this.selectionStart;
                const textBefore = this.value.substring(0, cursorPos);
                const textAfter = this.value.substring(cursorPos);

                this.value = textBefore + '\n' + textAfter;

                // Перемещаем курсор после переноса строки
                this.selectionStart = this.selectionEnd = cursorPos + 1;

                // Обновляем высоту
                this.dispatchEvent(new Event('input'));
                return;
            }
            
            // На десктопе без Shift - отправка
            if (!isMobile() && !e.repeat) {
                e.preventDefault();
                sendMessage();
            }
        }
    });
}

// ========================================
// Статус "печатает"
// ========================================
async function sendTypingStatus() {
    if (isTyping) {
        clearTimeout(typingTimeout);
    } else {
        isTyping = true;
        try {
            await fetch(`/task/${TASK_ID}/typing`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ is_typing: true })
            });
        } catch (error) {
            console.error('Error sending typing status:', error);
        }
    }

    typingTimeout = setTimeout(async () => {
        isTyping = false;
        try {
            await fetch(`/task/${TASK_ID}/typing`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ is_typing: false })
            });
        } catch (error) {
            console.error('Error sending typing stop:', error);
        }
    }, 2000);
}

async function checkPartnerTyping() {
    try {
        const response = await fetch(`/task/${TASK_ID}/typing_status`);
        const data = await response.json();

        if (data.is_typing) {
            showPartnerTyping(data.username || PARTNER_USERNAME);
        } else {
            hidePartnerTyping();
        }
    } catch (error) {
        console.error('Error checking typing status:', error);
    }
}

function showPartnerTyping(username) {
    if (!isPartnerTyping) {
        isPartnerTyping = true;
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.classList.add('show');
            const textElement = indicator.querySelector('.typing-text');
            if (textElement) {
                textElement.textContent = `${username} печатает...`;
            }
        }
    }

    clearTimeout(partnerTypingTimeout);
    partnerTypingTimeout = setTimeout(() => {
        hidePartnerTyping();
    }, 5000);
}

function hidePartnerTyping() {
    isPartnerTyping = false;
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.classList.remove('show');
    }
}

// ========================================
// Отправка сообщений
// ========================================
function setupMessageForm() {
    const form = document.getElementById('messageForm');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        sendMessage();
    });
}

async function sendMessage() {
    const textarea = document.getElementById('messageInput');
    const message = textarea.value.trim();

    if (!message) return;

    // Очищаем поле
    textarea.value = '';
    textarea.style.height = 'auto';

    // Показываем сообщение локально
    addMessageToChat(message, true);

    // Отправляем на сервер
    try {
        const response = await fetch(`/task/${TASK_ID}/send_message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: message })
        });

        const data = await response.json();

        if (data.success) {
            // Обновляем ID сообщения
            const lastMessage = document.querySelector('.message-outgoing:last-child');
            if (lastMessage) {
                lastMessage.dataset.messageId = data.message.id;
                
                // Обновляем время
                const timeElement = lastMessage.querySelector('.message-time');
                if (timeElement && data.message.created_at) {
                    const date = new Date(data.message.created_at);
                    const timeStr = date.getHours().toString().padStart(2, '0') + ':' +
                                   date.getMinutes().toString().padStart(2, '0');
                    timeElement.innerHTML = timeStr + ' <span class="message-status sent"><i class="fas fa-check"></i></span>';
                }
            }

            lastMessageId = data.message.id;
            
            // Сохраняем фокус на поле ввода на мобильных
            if (isMobile()) {
                setTimeout(() => textarea.focus(), 100);
            }
        } else {
            showNotification('Ошибка отправки сообщения', 'error');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        showNotification('Ошибка отправки сообщения', 'error');
    }
}

// ========================================
// Добавление сообщения в чат
// ========================================
function addMessageToChat(content, isOutgoing = false, messageId = null, created_at_iso = null, senderUsername = null) {
    const messagesList = document.getElementById('messagesList');
    if (!messagesList) return;

    const wasAtBottom = isAtBottom();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isOutgoing ? 'message-outgoing' : 'message-incoming'}`;
    if (messageId) {
        messageDiv.dataset.messageId = messageId;
    }

    // Форматируем время
    let timeStr = '';
    if (created_at_iso) {
        const date = new Date(created_at_iso);
        if (!isNaN(date.getTime())) {
            timeStr = date.getHours().toString().padStart(2, '0') + ':' +
                     date.getMinutes().toString().padStart(2, '0');
        }
    }
    
    if (!timeStr) {
        const now = new Date();
        timeStr = now.getHours().toString().padStart(2, '0') + ':' +
                 now.getMinutes().toString().padStart(2, '0');
    }

    // Форматируем контент (сохраняем переносы строк)
    const formattedContent = escapeHtml(content).replace(/\n/g, '<br>');

    // Определяем имя отправителя
    const senderName = isOutgoing ? CURRENT_USERNAME : (senderUsername || PARTNER_USERNAME);

    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-text">${formattedContent}</div>
            <div class="message-time">
                ${timeStr}
                ${isOutgoing ? '<span class="message-status sent"><i class="fas fa-check"></i></span>' : ''}
            </div>
        </div>
        <div class="message-sender">
            ${senderName}
        </div>
    `;

    messagesList.appendChild(messageDiv);

    if (messageId && messageId > lastMessageId) {
        lastMessageId = messageId;
    }

    if (wasAtBottom || isOutgoing) {
        scrollToBottom();
    }
}

// ========================================
// Загрузка новых сообщений (polling)
// ========================================
async function loadNewMessages() {
    try {
        const response = await fetch(`/task/${TASK_ID}/get_messages?last_id=${lastMessageId}`);
        const data = await response.json();

        if (data && data.length > 0) {
            const wasAtBottom = isAtBottom();

            for (const message of data) {
                // Проверяем, нет ли уже такого сообщения
                const existingMessage = document.querySelector(`[data-message-id="${message.id}"]`);
                if (!existingMessage) {
                    addMessageToChat(
                        message.content,
                        message.sender_id === CURRENT_USER_ID,
                        message.id,
                        message.created_at_iso,
                        message.sender_name
                    );
                }
            }

            if (wasAtBottom || isFirstLoad) {
                scrollToBottom();
                isFirstLoad = false;
            }
            
            // Обновляем участников чата - добавляем новых отправителей
            updateParticipantsStatus();
        }

        // Обновляем статусы прочтения для всех сообщений
        updateMessageReadStatuses();

    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

// Обновление статусов прочтения сообщений
function updateMessageReadStatuses() {
    fetch(`/task/${TASK_ID}/get_messages?last_id=0`)
        .then(r => r.json())
        .then(messages => {
            messages.forEach(msg => {
                const messageEl = document.querySelector(`[data-message-id="${msg.id}"]`);
                if (messageEl) {
                    const statusEl = messageEl.querySelector('.message-status');
                    if (statusEl && msg.sender_id === CURRENT_USER_ID) {
                        if (msg.is_read) {
                            statusEl.className = 'message-status read';
                            statusEl.innerHTML = '<i class="fas fa-check-double"></i>';
                            statusEl.title = 'Прочитано';
                        } else {
                            statusEl.className = 'message-status sent';
                            statusEl.innerHTML = '<i class="fas fa-check"></i>';
                            statusEl.title = 'Отправлено';
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error updating read statuses:', error));
}

function startMessagePolling() {
    // Проверяем каждые 2 секунды
    setInterval(loadNewMessages, 2000);
    
    // Первоначальная загрузка
    setTimeout(loadNewMessages, 500);
}

// ========================================
// Переключение деталей задачи
// ========================================
function toggleTaskDetails() {
    const content = document.getElementById('taskDetailsContent');
    const desktopIcon = document.getElementById('toggleDetailsIcon');
    const mobileIcon = document.getElementById('toggleDetailsIconMobile');

    // Проверяем фактическое отображение элемента через getComputedStyle
    const isExpanded = window.getComputedStyle(content).display !== 'none';

    if (isExpanded) {
        // Сворачиваем панель
        content.style.display = 'none';
        if (desktopIcon) desktopIcon.className = 'fas fa-chevron-down desktop-chevron';
        if (mobileIcon) mobileIcon.className = 'fas fa-chevron-down mobile-chevron';
    } else {
        // Разворачиваем панель
        content.style.display = 'block';
        if (desktopIcon) desktopIcon.className = 'fas fa-chevron-up desktop-chevron';
        if (mobileIcon) mobileIcon.className = 'fas fa-chevron-up mobile-chevron';
    }
}
