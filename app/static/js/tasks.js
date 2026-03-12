/**
 * Task-Chat Full — Логика управления задачами
 * Фильтрация, сортировка, обновление в реальном времени
 */

let lastTasksHash = null;
let refreshInterval = null;

// ========================================
// Инициализация
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    // Фильтрация задач
    const filterButtons = document.querySelectorAll('.filter-btn');

    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            const filter = this.dataset.filter;
            filterTasks(filter);
        });
    });

    // Запуск polling для обновления задач
    if (typeof window.currentUserId !== 'undefined' && window.currentUserId > 0) {
        startTasksPolling();
        // Обновляем статистику при загрузке (данные будут получены из API в updateTasksHash)
    }
});

// ========================================
// Обновление статистики
// ========================================
function updateStats(stats) {
    const taskCards = document.querySelectorAll('.task-card');

    // Всего задач
    const totalElement = document.querySelector('.stat-number');
    if (totalElement) {
        totalElement.textContent = taskCards.length;
    }

    // Ожидают (pending)
    const pendingElement = document.querySelectorAll('.stat-number')[1];
    if (pendingElement) {
        const pendingCount = document.querySelectorAll('.task-card.status-pending').length;
        pendingElement.textContent = pendingCount;
    }

    // В работе (in_progress)
    const inProgressElement = document.querySelectorAll('.stat-number')[2];
    if (inProgressElement) {
        const inProgressCount = document.querySelectorAll('.task-card.status-in_progress').length;
        inProgressElement.textContent = inProgressCount;
    }

    // Активные чаты - используем данные из API если есть
    const activeChatsElement = document.getElementById('activeChatsCount');
    if (activeChatsElement) {
        if (stats && stats.active_chats !== undefined) {
            // Используем значение из API (правильный подсчёт)
            activeChatsElement.textContent = stats.active_chats;
        } else {
            // Fallback: считаем карточки с бейджем непрочитанных
            let activeChats = 0;
            taskCards.forEach(card => {
                const unreadBadge = card.querySelector('.chat-badge');
                if (unreadBadge) activeChats++;
            });
            activeChatsElement.textContent = activeChats;
        }
    }
}

// ========================================
// Фильтрация задач
// ========================================
function filterTasks(filter) {
    const taskCards = document.querySelectorAll('.task-card');
    
    taskCards.forEach(card => {
        const status = card.dataset.status;
        
        if (filter === 'all') {
            card.style.display = '';
        } else if (status === filter) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

// ========================================
// Сортировка задач
// ========================================
function sortTasks(sortBy) {
    const tasksList = document.getElementById('tasksList');
    const taskCards = Array.from(tasksList.querySelectorAll('.task-card'));
    
    taskCards.sort((a, b) => {
        const timestampA = parseFloat(a.dataset.updatedTimestamp || a.dataset.createdTimestamp || 0);
        const timestampB = parseFloat(b.dataset.updatedTimestamp || b.dataset.createdTimestamp || 0);
        
        switch(sortBy) {
            case 'newest':
                return timestampB - timestampA;
            case 'oldest':
                return timestampA - timestampB;
            case 'updated':
                return timestampB - timestampA;
            default:
                return 0;
        }
    });
    
    taskCards.forEach(card => tasksList.appendChild(card));
}

// ========================================
// Polling для обновления задач
// ========================================
function startTasksPolling() {
    // Первоначальная загрузка хэша
    updateTasksHash();

    // Проверка каждые 3 секунды
    refreshInterval = setInterval(() => {
        checkForUpdates();
    }, 3000);
}

function stopTasksPolling() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

async function checkForUpdates() {
    try {
        const response = await fetch('/api/tasks');
        const data = await response.json();

        // API возвращает {tasks: [...], stats: {...}}, извлекаем массив
        const tasks = data.tasks || data;
        const stats = data.stats;

        if (!Array.isArray(tasks)) {
            console.error('[Polling] API вернул не массив:', data);
            return;
        }

        // Получаем текущие ID задач на странице
        const existingIds = new Set(
            Array.from(document.querySelectorAll('.task-card'))
                .map(card => parseInt(card.dataset.taskId))
        );

        // Проверяем есть ли новые задачи
        const hasNewTasks = tasks.some(t => !existingIds.has(t.id));

        // Создаем хэш текущего состояния
        const newHash = createTasksHash(tasks);

        // Если есть новые задачи или данные изменились, обновляем
        if (hasNewTasks || newHash !== lastTasksHash) {
            await updateTasksList(tasks, stats);
            lastTasksHash = newHash;
        } else {
            // Даже если хэш не изменился, обновляем бейджи и статистику
            updateAllBadges(tasks);
        }

        // Всегда обновляем статистику (количество задач в статусах могло измениться)
        updateStats(stats);
    } catch (error) {
        console.error('Error checking for updates:', error);
    }
}

function updateAllBadges(tasks) {
    for (const task of tasks) {
        const card = document.querySelector(`.task-card[data-task-id="${task.id}"]`);
        if (card && task.unread_count !== undefined) {
            updateChatBadge(card, task.id, task.unread_count);
        }
    }
}

function createTasksHash(tasks) {
    // Создаем контрольную сумму из данных задач + unread_count
    return tasks.map(t => `${t.id}-${t.status}-${t.updated_at || t.created_at}-${t.unread_count || 0}`).join('|');
}

async function updateTasksList(tasks, stats) {
    const tasksList = document.getElementById('tasksList');
    if (!tasksList) {
        console.error('[updateTasksList] tasksList не найден!');
        return;
    }

    // Сохраняем текущие открытые модальные окна и прокрутку
    const scrollTop = window.scrollY;

    // Получаем текущие ID задач на странице
    const existingIds = new Set(
        Array.from(document.querySelectorAll('.task-card'))
            .map(card => parseInt(card.dataset.taskId))
    );

    // Получаем новые ID задач
    const newIds = new Set(tasks.map(t => t.id));

    // Проверяем есть ли новые задачи
    const hasNewTasks = tasks.some(t => !existingIds.has(t.id));

    // Проверяем есть ли удаленные задачи
    const hasRemovedTasks = Array.from(existingIds).some(id => !newIds.has(id));

    // Если есть новые задачи, добавляем их
    if (hasNewTasks) {
        await addNewTasks(tasks, existingIds);
    }

    // Если есть удаленные задачи, удаляем их
    if (hasRemovedTasks) {
        await removeDeletedTasks(existingIds, newIds);
    }

    // Обновляем существующие карточки (статусы, бейджи и т.д.)
    await updateChangedCards(tasks);

    // Обновляем статистику
    updateStats(stats);

    // Восстанавливаем прокрутку
    window.scrollTo(0, scrollTop);
}

async function addNewTasks(tasks, existingIds) {
    try {
        const response = await fetch('/');
        const html = await response.text();

        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newTasksList = doc.getElementById('tasksList');

        if (newTasksList) {
            // Находим новые задачи и добавляем их
            for (const task of tasks) {
                if (!existingIds.has(task.id)) {
                    const newCard = newTasksList.querySelector(`.task-card[data-task-id="${task.id}"]`);
                    if (newCard) {
                        const tasksList = document.getElementById('tasksList');
                        tasksList.insertBefore(newCard, tasksList.firstChild);
                        
                        // Показываем уведомление о новой задаче
                        showNotification(`Новая задача #${task.id} создана`, 'success');
                    } else {
                        console.error(`[addNewTasks] Не нашли карточку задачи #${task.id} в HTML`);
                    }
                }
            }
            
            // Переназначаем обработчики фильтров для новых карточек
            const filterButtons = document.querySelectorAll('.filter-btn');
            filterButtons.forEach(button => {
                button.addEventListener('click', function() {
                    filterButtons.forEach(btn => btn.classList.remove('active'));
                    this.classList.add('active');
                    filterTasks(this.dataset.filter);
                });
            });
        } else {
            console.error(`[addNewTasks] Не получили tasksList из HTML`);
        }
    } catch (error) {
        console.error('Error adding new tasks:', error);
    }
}

async function removeDeletedTasks(existingIds, newIds) {
    for (const id of existingIds) {
        if (!newIds.has(id)) {
            const card = document.querySelector(`.task-card[data-task-id="${id}"]`);
            if (card) {
                card.remove();
            }
        }
    }
}

async function refreshTasksFull(tasks) {
    try {
        const response = await fetch('/');
        const html = await response.text();

        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newTasksList = doc.getElementById('tasksList');

        if (newTasksList) {
            const tasksList = document.getElementById('tasksList');
            tasksList.innerHTML = newTasksList.innerHTML;

            // Переназначаем обработчики фильтров
            const filterButtons = document.querySelectorAll('.filter-btn');
            filterButtons.forEach(button => {
                button.addEventListener('click', function() {
                    filterButtons.forEach(btn => btn.classList.remove('active'));
                    this.classList.add('active');
                    filterTasks(this.dataset.filter);
                });
            });

            // Обновляем статистику
            updateStats();

            // Показываем уведомление
            showNotification('Задачи обновлены', 'info');
        }
    } catch (error) {
        console.error('Error refreshing tasks:', error);
    }
}

async function updateChangedCards(tasks) {
    let changed = false;

    for (const task of tasks) {
        const card = document.querySelector(`.task-card[data-task-id="${task.id}"]`);
        if (!card) continue;
        
        // Проверяем изменился ли статус
        const currentStatus = card.dataset.status;
        if (currentStatus !== task.status) {
            // Обновляем классы статуса
            card.classList.remove(`status-${currentStatus}`);
            card.classList.add(`status-${task.status}`);
            card.dataset.status = task.status;

            // Обновляем бейдж статуса
            const statusBadge = card.querySelector('.task-status');
            if (statusBadge) {
                statusBadge.className = `task-status status-${task.status}`;
                statusBadge.innerHTML = getStatusIcon(task.status) + ` <span class="status-text">${getStatusText(task.status)}</span>`;
            }
            changed = true;
        }

        // Обновляем заголовок задачи
        const titleEl = card.querySelector('h4');
        if (titleEl && task.title && titleEl.textContent.trim() !== task.title) {
            titleEl.textContent = task.title;
            changed = true;
        }

        // Обновляем описание
        const descEl = card.querySelector('.task-description');
        if (descEl && task.description !== undefined) {
            const newDesc = task.description || 'Нет описания';
            if (descEl.textContent.trim() !== newDesc) {
                descEl.textContent = newDesc;
                changed = true;
            }
        }

        // Обновляем приоритет (если есть на карточке)
        const priorityEl = card.querySelector('.priority-badge');
        if (priorityEl && task.priority_display !== undefined) {
            if (priorityEl.textContent !== task.priority_display) {
                priorityEl.textContent = task.priority_display;
                changed = true;
            }
        }

        // Обновляем врача (если есть на карточке)
        const doctorEl = card.querySelector('.participant-name');
        if (doctorEl && task.doctor !== undefined) {
            if (doctorEl.textContent.trim() !== task.doctor) {
                doctorEl.textContent = task.doctor;
                changed = true;
            }
        }

        // Обновляем бейдж непрочитанных сообщений
        if (task.unread_count !== undefined) {
            updateChatBadge(card, task.id, task.unread_count);
        }

        // Обновляем карту пациента
        if (task.patient_card !== undefined) {
            updatePatientCard(card, task.patient_card);
        }

        // Обновляем тип исследования
        if (task.research_type !== undefined) {
            updateResearchType(card, task.research_type);
        }

        // Обновляем или добавляем экспертную группу
        if (task.expert_group) {
            updateOrAddField(card, 'expert_group', 'Экспертная группа', task.expert_group, 'fa-user-md');
        } else {
            hideField(card, 'expert_group');
        }

        // Обновляем или добавляем CT диагностику
        if (task.ct_diagnostic) {
            updateOrAddField(card, 'ct_diagnostic', 'CT диагностика', task.ct_diagnostic, 'fa-microscope');
        } else {
            hideField(card, 'ct_diagnostic');
        }

        // Обновляем или добавляем лечение
        if (task.treatment) {
            // Извлекаем контроль по дыханию из treatment если он там есть (для старых задач)
            let treatmentText = task.treatment;
            let extractedBreathControl = null;
            
            const breathMatch = task.treatment.match(/ - (на задержке|свободное дыхание)$/);
            if (breathMatch) {
                treatmentText = task.treatment.replace(/ - (на задержке|свободное дыхание)$/, '');
                extractedBreathControl = breathMatch[1] === 'на задержке' ? 'breath_hold' : 'free';
            }
            
            updateOrAddField(card, 'treatment', 'Лечение', treatmentText, 'fa-radiation');
            
            // Обновляем или добавляем контроль по дыханию
            const breathControlValue = task.breath_control || extractedBreathControl;
            if (breathControlValue && breathControlValue !== 'no') {
                const breathControlText = {
                    'breath_hold': 'На задержке',
                    'free': 'Свободное дыхание'
                }[breathControlValue] || breathControlValue;
                updateOrAddField(card, 'breath_control', 'Контроль по дыханию', breathControlText, 'fa-lungs');
            } else {
                hideField(card, 'breath_control');
            }
        } else {
            hideField(card, 'treatment');
            hideField(card, 'breath_control');
        }
        
        // Обновляем или добавляем MR диагностику
        if (task.mr_diagnostic) {
            updateOrAddField(card, 'mr_diagnostic', 'MR диагностика', task.mr_diagnostic, 'fa-dna');
        } else {
            hideField(card, 'mr_diagnostic');
        }
        
        // Обновляем или добавляем PET диагностику
        if (task.pet_diagnostic) {
            updateOrAddField(card, 'pet_diagnostic', 'PET диагностика', task.pet_diagnostic, 'fa-atom');
        } else {
            hideField(card, 'pet_diagnostic');
        }
    }

    // Обновляем статистику если что-то изменилось
    if (changed) {
        updateStats();
    }
}

function updateChatBadge(card, taskId, unreadCount) {
    const chatBtn = card.querySelector('.btn-chat');
    if (!chatBtn) return;
    
    // Находим существующий бейдж или создаем новый
    let badge = chatBtn.querySelector('.chat-badge');
    
    if (unreadCount > 0) {
        if (!badge) {
            // Создаем новый бейдж
            badge = document.createElement('span');
            badge.className = 'chat-badge';
            badge.style.cssText = 'position: absolute; top: -6px; right: -6px; min-width: 20px; height: 20px; font-size: 10px; border-radius: 50%; background: #ef4444; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; box-shadow: 0 2px 8px rgba(239, 68, 68, 0.5); border: 2px solid white;';
            chatBtn.appendChild(badge);
        }
        badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
    } else if (badge) {
        // Удаляем бейдж если нет непрочитанных
        badge.remove();
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
// Функции обновления полей задачи
// ========================================
function updatePatientCard(card, patientCard) {
    const metaItems = card.querySelectorAll('.meta-item');
    for (const item of metaItems) {
        const label = item.querySelector('.meta-label');
        if (label && label.textContent.includes('Карта пациента')) {
            const valueEl = item.querySelector('.meta-value');
            if (valueEl) {
                const textNode = Array.from(valueEl.childNodes).find(n => n.nodeType === 3);
                if (textNode) {
                    textNode.textContent = ' ' + (patientCard || 'Нет данных');
                }
            }
            break;
        }
    }
}

function updateResearchType(card, researchType) {
    const metaItems = card.querySelectorAll('.meta-item');
    const typesMap = {
        'import_ct': 'Импорт CT',
        'import_ct_diag': 'Импорт CT-диагностики',
        'mr': 'Импорт MR',
        'pet': 'Импорт PET'
    };
    for (const item of metaItems) {
        const label = item.querySelector('.meta-label');
        if (label && label.textContent.includes('Тип исследования')) {
            const valueEl = item.querySelector('.meta-value');
            if (valueEl) {
                valueEl.textContent = typesMap[researchType] || researchType;
            }
            break;
        }
    }
}

function updateExpertGroup(card, expertGroup) {
    const metaItem = card.querySelector('.meta-item[data-field="expert_group"]');
    if (metaItem) {
        const valueEl = metaItem.querySelector('.meta-value');
        if (valueEl) {
            valueEl.textContent = expertGroup || 'Не указано';
        }
    }
}

function updateCTDiagnostic(card, ctDiagnostic) {
    const metaItem = card.querySelector('.meta-item[data-field="ct_diagnostic"]');
    if (metaItem) {
        const valueEl = metaItem.querySelector('.meta-value');
        if (valueEl) {
            valueEl.textContent = ctDiagnostic || 'Не указано';
        }
    }
}

function updateTreatment(card, treatment) {
    const metaItem = card.querySelector('.meta-item[data-field="treatment"]');
    if (metaItem) {
        const valueEl = metaItem.querySelector('.meta-value');
        if (valueEl) {
            valueEl.textContent = treatment || 'Не указано';
        }
    }
}

function updateMRDiagnostic(card, mrDiagnostic) {
    const metaItem = card.querySelector('.meta-item[data-field="mr_diagnostic"]');
    if (metaItem) {
        const valueEl = metaItem.querySelector('.meta-value');
        if (valueEl) {
            valueEl.textContent = mrDiagnostic || 'Не указано';
        }
    }
}

function updatePETDiagnostic(card, petDiagnostic) {
    const metaItem = card.querySelector('.meta-item[data-field="pet_diagnostic"]');
    if (metaItem) {
        const valueEl = metaItem.querySelector('.meta-value');
        if (valueEl) {
            valueEl.textContent = petDiagnostic || 'Не указано';
        }
    }
}

// Обновляет или добавляет поле в карточку задачи
function updateOrAddField(card, fieldName, fieldLabel, value, iconClass) {
    // Сначала ищем по data-field
    let metaItem = card.querySelector(`.meta-item[data-field="${fieldName}"]`);
    
    // Если не нашли, ищем по тексту метки (для старых карточек)
    if (!metaItem) {
        const metaItems = card.querySelectorAll('.meta-item');
        for (const item of metaItems) {
            const label = item.querySelector('.meta-label');
            if (label && label.textContent.includes(fieldLabel)) {
                metaItem = item;
                break;
            }
        }
    }
    
    if (metaItem) {
        // Поле есть - обновляем значение и показываем
        const valueEl = metaItem.querySelector('.meta-value');
        if (valueEl) {
            valueEl.textContent = value;
        }
        metaItem.style.display = '';
    } else {
        // Поля нет - добавляем новый meta-item в правильное место
        const metaInfo = card.querySelector('.task-meta-info');
        if (metaInfo) {
            // Определяем порядок полей
            const fieldOrder = ['expert_group', 'ct_diagnostic', 'treatment', 'breath_control', 'mr_diagnostic', 'pet_diagnostic'];
            const currentIndex = fieldOrder.indexOf(fieldName);
            
            // Ищем место для вставки
            let referenceNode = null;
            for (let i = currentIndex + 1; i < fieldOrder.length; i++) {
                referenceNode = metaInfo.querySelector(`.meta-item[data-field="${fieldOrder[i]}"]`);
                if (referenceNode && referenceNode.style.display !== 'none') {
                    break;
                }
                referenceNode = null;
            }
            
            const newMetaItem = document.createElement('div');
            newMetaItem.className = 'meta-item';
            newMetaItem.dataset.field = fieldName;
            newMetaItem.innerHTML = `
                <span class="meta-label"><i class="fas ${iconClass}"></i> ${fieldLabel}:</span>
                <span class="meta-value">${value}</span>
            `;
            
            if (referenceNode) {
                metaInfo.insertBefore(newMetaItem, referenceNode);
            } else {
                metaInfo.appendChild(newMetaItem);
            }
        }
    }
}

// Скрывает поле
function hideField(card, fieldName) {
    const metaItem = card.querySelector(`.meta-item[data-field="${fieldName}"]`);
    if (metaItem) {
        metaItem.style.display = 'none';
    }
}

// ========================================
// Обновление задач (AJAX)
// ========================================
async function refreshTasks() {
    const btn = document.querySelector('.btn-refresh');
    if (btn) {
        btn.classList.add('spinning');
    }

    try {
        const response = await fetch('/api/tasks');
        const data = await response.json();
        const tasks = data.tasks || data;
        const stats = data.stats;

        await updateTasksList(tasks, stats);
        updateTasksHash();
    } catch (error) {
        console.error('Error refreshing tasks:', error);
        showNotification('Ошибка обновления задач', 'error');
    } finally {
        if (btn) {
            btn.classList.remove('spinning');
        }
    }
}

function updateTasksHash() {
    fetch('/api/tasks')
        .then(r => r.json())
        .then(data => {
            const tasks = data.tasks || data;
            const stats = data.stats;
            if (Array.isArray(tasks)) {
                lastTasksHash = createTasksHash(tasks);
                // Обновляем бейджи при первой загрузке
                updateAllBadges(tasks);
                // Обновляем статистику
                updateStats(stats);
            } else {
                console.error('[updateTasksHash] API вернул не массив:', data);
            }
        })
        .catch(err => console.error('Error updating hash:', err));
}

// ========================================
// Быстрое обновление статуса
// ========================================
function confirmStatusChange(form) {
    return confirm('Изменить статус задачи?');
}

// ========================================
// Уведомления
// ========================================
function showNotification(message, type = 'info') {
    // Создаем уведомление
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ========================================
// Поиск задач (для админ-панели)
// ========================================
function searchTasks() {
    const searchInput = document.getElementById('searchTasks');
    if (!searchInput) return;
    
    const searchTerm = searchInput.value.toLowerCase();
    const taskRows = document.querySelectorAll('#tasksTableBody tr');
    
    taskRows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

// ========================================
// Массовые действия (для админ-панели)
// ========================================
function toggleSelectAll() {
    const selectAll = document.getElementById('selectAll');
    if (!selectAll) return;
    
    document.querySelectorAll('.task-checkbox').forEach(cb => {
        cb.checked = selectAll.checked;
    });
}

function performMassAction() {
    const actionSelect = document.getElementById('massActionSelect');
    const newStatusSelect = document.getElementById('newStatusSelect');
    const newPhysicistSelect = document.getElementById('newPhysicistSelect');
    
    if (!actionSelect) return;
    
    const action = actionSelect.value;
    const selectedIds = Array.from(document.querySelectorAll('.task-checkbox:checked'))
                              .map(cb => parseInt(cb.value));
    
    if (!action || selectedIds.length === 0) {
        alert('Выберите действие и задачи');
        return;
    }
    
    let data = { action, task_ids: selectedIds };
    
    if (action === 'change_status') {
        data.new_status = newStatusSelect.value;
    } else if (action === 'change_physicist') {
        data.new_physicist = parseInt(newPhysicistSelect.value);
    } else if (action === 'delete') {
        if (!confirm(`Удалить ${selectedIds.length} задач(и)?`)) return;
    }
    
    const url = action === 'delete' 
        ? '/admin/tasks/mass_delete' 
        : '/admin/tasks/mass_update';
    
    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Ошибка: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка выполнения действия');
    });
}

// Обработчик изменения выбора массового действия
document.addEventListener('DOMContentLoaded', function() {
    const massActionSelect = document.getElementById('massActionSelect');
    const newStatusSelect = document.getElementById('newStatusSelect');
    const newPhysicistSelect = document.getElementById('newPhysicistSelect');
    
    if (massActionSelect) {
        massActionSelect.addEventListener('change', function() {
            if (newStatusSelect) {
                newStatusSelect.style.display = this.value === 'change_status' ? '' : 'none';
            }
            if (newPhysicistSelect) {
                newPhysicistSelect.style.display = this.value === 'change_physicist' ? '' : 'none';
            }
        });
    }
});

// ========================================
// Анимация кнопки обновления
// ========================================
const style = document.createElement('style');
style.textContent = `
    .btn-refresh.spinning i {
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 20px;
        border-radius: 10px;
        color: white;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: slideInRight 0.3s ease-out;
        max-width: 350px;
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 500;
    }
    
    .notification-success {
        background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
    }
    
    .notification-error {
        background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
    }
    
    .notification-info {
        background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%);
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Остановка polling при уходе со страницы
window.addEventListener('beforeunload', stopTasksPolling);
window.addEventListener('pagehide', stopTasksPolling);
