/**
 * Task-Chat Admin — Real-time обновления
 * Обновление статистики, пользователей и задач в реальном времени
 */

// Конфигурация
const ADMIN_CONFIG = {
    STATS_INTERVAL: 5000,      // Обновление статистики (5 сек)
    USERS_INTERVAL: 10000,     // Обновление пользователей (10 сек)
    TASKS_INTERVAL: 10000      // Обновление задач (10 сек)
};

// ========================================
// Обновление статистики
// ========================================
function updateAdminStats() {
    fetch('/admin/api/stats')
        .then(response => response.json())
        .then(data => {
            // Обновляем числа
            const statUsers = document.getElementById('statUsers');
            const statTasks = document.getElementById('statTasks');
            const statMessages = document.getElementById('statMessages');
            const statFiles = document.getElementById('statFiles');
            
            if (statUsers) statUsers.textContent = data.total_users;
            if (statTasks) statTasks.textContent = data.total_tasks;
            if (statMessages) statMessages.textContent = data.total_messages;
            if (statFiles) statFiles.textContent = data.total_files;
            
            // Обновляем разбивку по статусам задач
            updateStatBreakdown('tasksByStatus', data.tasks_by_status, 'status');
            
            // Обновляем разбивку по ролям
            updateStatBreakdown('usersByRole', data.users_by_role, 'role');
            
            // Обновляем активные чаты
            const activeChatsBadge = document.getElementById('activeChatsBadge');
            if (activeChatsBadge) {
                activeChatsBadge.textContent = `${data.active_chats} активных чатов`;
            }
        })
        .catch(error => console.error('Error updating stats:', error));
}

function updateStatBreakdown(elementId, data, type) {
    const breakdown = document.getElementById(elementId);
    if (!breakdown || !data) return;
    
    let html = '';
    const names = type === 'status' ? {
        'pending': 'ожидает',
        'in_progress': 'в работе',
        'completed': 'выполнено',
        'cancelled': 'отменено'
    } : {
        'admin': 'админ',
        'doctor': 'врач',
        'physicist': 'физик'
    };
    
    for (const [key, count] of Object.entries(data)) {
        const className = type === 'status' ? `status-${key}` : '';
        html += `<span class="stat-badge ${className}">${count} ${names[key] || key}</span>`;
    }
    breakdown.innerHTML = html;
}

// ========================================
// Обновление пользователей
// ========================================
function updateUsersTable() {
    const tableBody = document.getElementById('usersTableBody');
    if (!tableBody) return;
    
    fetch('/admin/api/users')
        .then(response => response.json())
        .then(users => {
            users.forEach(user => {
                const row = tableBody.querySelector(`tr[data-user-id="${user.id}"]`);
                if (row) {
                    // Обновляем статус онлайн/офлайн
                    const statusCell = row.querySelector('.user-status-cell');
                    if (statusCell) {
                        statusCell.innerHTML = user.is_online 
                            ? '<span class="status-online"><i class="fas fa-circle"></i> Онлайн</span>'
                            : '<span class="status-offline"><i class="fas fa-circle"></i> Офлайн</span>';
                    }
                    
                    // Обновляем "Был в сети"
                    const lastSeenCell = row.querySelector('.last-seen');
                    if (lastSeenCell) {
                        lastSeenCell.textContent = user.last_seen;
                    }
                }
            });
        })
        .catch(error => console.error('Error updating users:', error));
}

// ========================================
// Обновление задач
// ========================================
function updateTasksTable() {
    // Обновляем таблицу на главной админки
    updateTable('recentTasksBody');

    // Обновляем таблицу на странице управления задачами
    updateTable('tasksTableBody');
}

function updateTable(tableBodyId) {
    const tableBody = document.getElementById(tableBodyId);
    if (!tableBody) return;

    fetch('/admin/api/tasks')
        .then(response => response.json())
        .then(tasks => {
            // Для таблицы последних задач (главная админки) - переупорядочиваем строки
            const isRecentTasks = tableBodyId === 'recentTasksBody';

            tasks.forEach(task => {
                const row = tableBody.querySelector(`tr[data-task-id="${task.id}"]`);
                if (row) {
                    // Обновляем статус
                    const statusBadge = row.querySelector('.status-badge');
                    if (statusBadge && statusBadge.textContent !== task.status_display) {
                        statusBadge.className = `status-badge status-${task.status}`;
                        statusBadge.textContent = task.status_display;
                        row.dataset.status = task.status;
                    }

                    // Обновляем тип исследования
                    const researchTypeCell = row.querySelector('.research-type');
                    if (researchTypeCell) {
                        const researchTypeMap = {
                            'import_ct': 'Импорт CT',
                            'import_ct_diag': 'CT-диагностика',
                            'mr': 'MR',
                            'pet': 'PET'
                        };
                        const newResearchType = researchTypeMap[task.research_type] || task.research_type;
                        if (researchTypeCell.textContent !== newResearchType) {
                            researchTypeCell.textContent = newResearchType;
                        }
                    }

                    // Обновляем карту пациента
                    const patientCardCell = row.querySelector('td:nth-child(5)');
                    if (patientCardCell && !patientCardCell.classList.contains('status-badge')) {
                        const newPatientCard = task.patient_card || '—';
                        if (patientCardCell.textContent.trim() !== newPatientCard) {
                            patientCardCell.textContent = newPatientCard;
                        }
                    }

                    // Обновляем врача
                    const doctorCell = row.querySelector('.doctor-name');
                    if (doctorCell) {
                        doctorCell.textContent = task.doctor;
                    }

                    // Обновляем дату
                    const dateCell = row.querySelector('.task-created-at');
                    if (dateCell && task.updated_at) {
                        dateCell.textContent = task.updated_at;
                    }
                } else {
                    // Задача не найдена - возможно новая, добавляем
                    prependNewTask(tableBody, task);
                }
            });

            // Для таблицы последних задач - переупорядочиваем строки
            if (isRecentTasks) {
                reorderRecentTasks(tableBody, tasks);
            }
        })
        .catch(error => console.error('Error updating tasks:', error));
}

function reorderRecentTasks(tableBody, tasks) {
    // Получаем все строки в таблице
    const rows = Array.from(tableBody.querySelectorAll('tr'));
    
    // Создаем копию первых 5 задач для избежания изменений
    const top5Tasks = tasks.slice(0, 5).map(t => ({ id: String(t.id) }));
    
    // Создаем множество ID задач, которые должны быть в таблице (первые 5 из API)
    const taskIdsToKeep = new Set(top5Tasks.map(t => t.id));
    
    // Удаляем строки, которых нет в первых 5 задачах API
    rows.forEach(row => {
        const taskId = String(row.dataset.taskId);
        if (!taskIdsToKeep.has(taskId)) {
            row.remove();
        }
    });
    
    // Создаем карту ID -> позиция в отсортированном списке из копии
    const taskOrder = new Map(top5Tasks.map((t, i) => [t.id, i]));
    
    // Получаем оставшиеся строки
    const remainingRows = Array.from(tableBody.querySelectorAll('tr'));
    
    // Сортируем строки согласно порядку задач из API
    remainingRows.sort((a, b) => {
        const aId = String(a.dataset.taskId);
        const bId = String(b.dataset.taskId);
        const aIndex = taskOrder.has(aId) ? taskOrder.get(aId) : Infinity;
        const bIndex = taskOrder.has(bId) ? taskOrder.get(bId) : Infinity;
        return aIndex - bIndex;
    });
    
    // Переставляем строки в таблице
    remainingRows.forEach(row => tableBody.appendChild(row));
}

function prependNewTask(tableBody, task) {
    // Определяем тип исследования
    let researchType = task.research_type;
    if (researchType === 'import_ct') researchType = 'Импорт CT';
    else if (researchType === 'import_ct_diag') researchType = 'CT-диагностика';
    else if (researchType === 'mr') researchType = 'MR';
    else if (researchType === 'pet') researchType = 'PET';

    // Проверяем тип таблицы - для главной админки или для страницы задач
    const isMainAdmin = tableBody.id === 'recentTasksBody';
    
    if (isMainAdmin) {
        // Для главной админки - без чекбокса
        const row = document.createElement('tr');
        row.dataset.taskId = task.id;
        row.dataset.status = task.status;
        row.innerHTML = `
            <td>#${task.id}</td>
            <td><strong>${task.title}</strong></td>
            <td><span class="research-type">${researchType}</span></td>
            <td>${task.patient_card || '—'}</td>
            <td><span class="status-badge status-${task.status}">${task.status_display}</span></td>
            <td>${task.doctor}</td>
            <td class="task-created-at">${task.created_at}</td>
            <td class="admin-actions">
                <a href="/admin/tasks/${task.id}/edit" class="btn btn-small btn-warning"><i class="fas fa-edit"></i></a>
                <a href="/task/${task.id}/chat" class="btn btn-small btn-chat"><i class="fas fa-comments"></i></a>
            </td>
        `;
        tableBody.insertBefore(row, tableBody.firstChild);
    } else {
        // Для страницы управления задачами - с чекбоксом
        const row = document.createElement('tr');
        row.dataset.taskId = task.id;
        row.dataset.status = task.status;
        row.innerHTML = `
            <td><input type="checkbox" class="task-checkbox" value="${task.id}" onchange="updateSelectedCount()"></td>
            <td>#${task.id}</td>
            <td><strong>${task.title}</strong></td>
            <td><span class="research-type">${researchType}</span></td>
            <td>${task.patient_card || '—'}</td>
            <td><span class="status-badge status-${task.status}">${task.status_display}</span></td>
            <td class="doctor-name">${task.doctor}</td>
            <td class="task-created-at">${task.created_at}</td>
            <td class="admin-actions">
                <a href="/admin/tasks/${task.id}/edit" class="btn btn-small btn-warning"><i class="fas fa-edit"></i></a>
                <a href="/task/${task.id}/chat" class="btn btn-small btn-chat"><i class="fas fa-comments"></i></a>
            </td>
        `;
        tableBody.insertBefore(row, tableBody.firstChild);
    }
}

// ========================================
// Инициализация
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем, что мы в админ-панели
    if (!document.querySelector('.admin-dashboard, .admin-panel')) return;
    
    console.log('Admin real-time updates initialized');
    
    // Запускаем обновления
    updateAdminStats();
    updateUsersTable();
    updateTasksTable();
    
    // Периодические обновления
    setInterval(updateAdminStats, ADMIN_CONFIG.STATS_INTERVAL);
    setInterval(updateUsersTable, ADMIN_CONFIG.USERS_INTERVAL);
    setInterval(updateTasksTable, ADMIN_CONFIG.TASKS_INTERVAL);
});
