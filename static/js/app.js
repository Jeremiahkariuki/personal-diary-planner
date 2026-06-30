document.addEventListener('DOMContentLoaded', () => {
    console.log('Jdiary Initialized');

    // Selectors
    const profileBtn = document.getElementById('profileBtn');
    const profileDropdown = document.getElementById('profileDropdown');
    const headerDate = document.querySelector('.dashboard-header p');
    const eventList = document.querySelector('.event-list');
    const pendingTaskList = document.querySelector('.pending-tasks');
    const completedTaskList = document.querySelector('.completed-tasks');
    const eventModal = document.getElementById('eventModal');
    const eventForm = document.getElementById('eventForm');
    const quickTaskForm = document.getElementById('quickTaskForm');
    const openModalBtn = document.querySelector('.events-section .add-btn') || document.getElementById('mainCreateEventBtn');
    const closeModalBtn = document.getElementById('closeModal');
    const sidebarEventList = document.getElementById('sidebarEventList');
    const csrfTokenEl = document.querySelector('[name=csrfmiddlewaretoken]');
    const csrfToken = csrfTokenEl ? csrfTokenEl.value : '';

    // Functions
    function updateHeader() {
        const now = new Date();
        const hour = now.getHours();
        const greeting = hour < 12 ? 'Good Morning' : hour < 18 ? 'Good Afternoon' : 'Good Evening';

        const h1 = document.querySelector('.dashboard-header h1');
        if (h1) h1.textContent = `${greeting}, ${h1.textContent.split(', ')[1] || h1.textContent}`;

        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        const dateDisplay = document.getElementById('currentDateDisplay');
        if (dateDisplay) dateDisplay.textContent = now.toLocaleDateString('en-US', options);
    }

    // Sound Toggle Logic
    let isMuted = localStorage.getItem('isMuted') === 'true';
    const soundToggleBtn = document.getElementById('soundToggleBtn');
    const soundOnIcon = document.querySelector('.sound-on-icon');
    const soundOffIcon = document.querySelector('.sound-off-icon');

    function updateSoundUI() {
        if (!soundOnIcon || !soundOffIcon) return;
        if (isMuted) {
            soundOnIcon.classList.add('hidden');
            soundOffIcon.classList.remove('hidden');
        } else {
            soundOnIcon.classList.remove('hidden');
            soundOffIcon.classList.add('hidden');
        }
    }

    if (soundToggleBtn) {
        updateSoundUI();
        soundToggleBtn.addEventListener('click', () => {
            isMuted = !isMuted;
            localStorage.setItem('isMuted', isMuted);
            updateSoundUI();
            showNotification('Sound', isMuted ? 'Muted' : 'Unmuted', false);
        });
    }

    window.showNotification = function (title, message, playAudio = true) {
        const toast = document.createElement('div');
        toast.className = 'notification-toast';
        toast.innerHTML = `
            <div class="notif-icon">🔔</div>
            <div class="notif-content">
                <strong>${title}</strong>
                <p>${message}</p>
            </div>
        `;
        document.body.appendChild(toast);

        if (!isMuted && playAudio) {
            const audio = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3');
            audio.play().catch(() => console.log('Audio playback prevented'));
        }

        setTimeout(() => {
            toast.style.animation = 'slideIn 0.5s ease reverse forwards';
            setTimeout(() => toast.remove(), 500);
        }, 5000);
    }

    // --- Tasks Logic ---
    async function addTask(title, dueDate, dueTime) {
        try {
            const response = await fetch('/api/tasks/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    'title': title,
                    'due_date': dueDate || null,
                    'due_time': dueTime || null
                })
            });
            if (response.ok) {
                const task = await response.json();
                renderTask(task);
                updateStats();
                quickTaskForm.reset();
                showNotification('Success', 'Task added!');
            } else {
                showNotification('Error', 'Failed to save task.');
            }
        } catch (error) {
            console.error('Error adding task:', error);
        }
    }

    function renderTask(task) {
        const item = document.createElement('div');
        item.className = `task-item ${task.completed ? 'completed' : ''}`;
        item.dataset.id = task.id;

        let dueHtml = '';
        if (task.due_date) {
            const d = new Date(task.due_date);
            const dateStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            dueHtml = `<span class="task-due-date">📅 ${dateStr} ${task.due_time || ''}</span>`;
        }

        item.innerHTML = `
            <input type="checkbox" ${task.completed ? 'checked' : ''} class="task-checkbox">
            <div class="task-info">
                <span class="task-title">${task.title}</span>
                ${dueHtml}
            </div>
            <button class="delete-task-btn">&times;</button>
        `;

        const targetList = task.completed ? completedTaskList : pendingTaskList;
        if (targetList) targetList.appendChild(item);
    }

    [pendingTaskList, completedTaskList].forEach(list => {
        if (!list) return;
        list.addEventListener('click', async (e) => {
            const taskItem = e.target.closest('.task-item');
            if (!taskItem) return;
            const taskId = taskItem.dataset.id;

            if (e.target.classList.contains('task-checkbox')) {
                const isCompleted = e.target.checked;
                const originalList = taskItem.parentElement;

                taskItem.classList.toggle('completed', isCompleted);
                const targetList = isCompleted ? completedTaskList : pendingTaskList;
                targetList.appendChild(taskItem);
                updateStats();

                try {
                    const response = await fetch(`/api/tasks/${taskId}/toggle/`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': csrfToken }
                    });
                    if (!response.ok) throw new Error();
                } catch (error) {
                    taskItem.classList.toggle('completed', !isCompleted);
                    e.target.checked = !isCompleted;
                    originalList.appendChild(taskItem);
                    updateStats();
                    showNotification('Error', 'Failed to update task');
                }
            } else if (e.target.classList.contains('delete-task-btn')) {
                const confirmed = await window.showConfirmModal('Delete Task', 'Are you sure you want to delete this task?');
                if (!confirmed) return;
                try {
                    const response = await fetch(`/api/tasks/${taskId}/`, {
                        method: 'DELETE',
                        headers: { 'X-CSRFToken': csrfToken }
                    });
                    if (response.status === 204) {
                        taskItem.remove();
                        updateStats();
                    }
                } catch (error) {
                    console.error('Error deleting task:', error);
                }
            }
        });
    });

    if (quickTaskForm) {
        quickTaskForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const title = document.getElementById('newTaskTitle').value;
            const dueDate = document.getElementById('newTaskDate').value;
            const dueTime = document.getElementById('newTaskTime').value;
            if (title) addTask(title, dueDate, dueTime);
        });
    }

    const clearTasksBtn = document.getElementById('clearTasksBtn');
    if (clearTasksBtn) {
        clearTasksBtn.addEventListener('click', async () => {
            const confirmed = await window.showConfirmModal('Clear All Tasks', 'Are you sure you want to clear all pending tasks?');
            if (!confirmed) return;
            try {
                const response = await fetch('/api/tasks/clear-pending/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken }
                });
                if (response.ok) {
                    pendingTaskList.innerHTML = '';
                    updateStats();
                    showNotification('Success', 'Cleared all pending tasks');
                }
            } catch (error) {
                console.error('Error clearing tasks:', error);
            }
        });
    }

    // --- Events Logic ---
    let allUpcomingEvents = [];
    let selectedDate = new Date().toISOString().split('T')[0];
    let currentViewDate = new Date();

    async function fetchEvents() {
        try {
            const response = await fetch('/api/events/');
            if (response.ok) {
                allUpcomingEvents = await response.json();
                renderCalendarGrid();
                filterEvents(selectedDate);
            }
        } catch (error) {
            console.error('Error fetching events:', error);
        }
    }

    function renderCalendarGrid() {
        const grid = document.getElementById('calendarGrid') || document.getElementById('fullCalendarBody');
        const monthYearLabel = document.getElementById('calendarMonthYear');
        if (!grid || !monthYearLabel) return;

        const isFullPage = grid.id === 'fullCalendarBody';

        grid.innerHTML = '';
        const year = currentViewDate.getFullYear();
        const month = currentViewDate.getMonth();

        const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
        monthYearLabel.textContent = `${monthNames[month]} ${year}`;

        const firstDayOfMonth = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const daysInPrevMonth = new Date(year, month, 0).getDate();

        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];

        for (let i = firstDayOfMonth - 1; i >= 0; i--) {
            grid.appendChild(createDayCard(year, month - 1, daysInPrevMonth - i, true, isFullPage));
        }

        for (let i = 1; i <= daysInMonth; i++) {
            const card = createDayCard(year, month, i, false, isFullPage);
            const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(i).padStart(2, "0")}`;
            if (dateStr === todayStr) card.classList.add('day-today');
            if (dateStr === selectedDate) card.classList.add('day-selected');
            grid.appendChild(card);
        }

        const remainingSlots = 42 - grid.children.length;
        for (let i = 1; i <= remainingSlots; i++) {
            grid.appendChild(createDayCard(year, month + 1, i, true, isFullPage));
        }
    }

    function createDayCard(year, month, day, isOutside, isFullPage = false) {
        const d = new Date(year, month, day);
        const y = d.getFullYear();
        const m = d.getMonth() + 1;
        const dayFormatted = d.getDate();
        const dateStr = `${y}-${String(m).padStart(2, "0")}-${String(dayFormatted).padStart(2, "0")}`;

        const card = document.createElement('div');
        card.className = isFullPage ? `calendar-day-cell ${isOutside ? 'day-outside' : ''}` : `calendar-day ${isOutside ? 'day-outside' : ''}`;
        card.innerHTML = `<span class="${isFullPage ? 'day-num' : 'day-number'}">${day}</span>`;

        const daysEvents = allUpcomingEvents.filter(e => e.date === dateStr);
        if (daysEvents.length > 0) {
            if (isFullPage) {
                const eventContainer = document.createElement('div');
                eventContainer.className = 'cell-events';
                daysEvents.slice(0, 3).forEach(e => {
                    const pill = document.createElement('div');
                    pill.className = 'day-event-pill';
                    pill.textContent = e.title;
                    eventContainer.appendChild(pill);
                });
                if (daysEvents.length > 3) {
                    const more = document.createElement('div');
                    more.className = 'day-event-pill';
                    more.style.background = 'rgba(255,255,255,0.1)';
                    more.textContent = `+${daysEvents.length - 3} more`;
                    eventContainer.appendChild(more);
                }
                card.appendChild(eventContainer);
            } else {
                const dot = document.createElement('div');
                dot.className = 'event-dot';
                card.appendChild(dot);
            }
        }

        card.addEventListener('click', () => {
            selectedDate = dateStr;
            if (isOutside) {
                currentViewDate = new Date(year, month, 1);
                renderCalendarGrid();
            } else {
                document.querySelectorAll('.calendar-day').forEach(cd => cd.classList.remove('day-selected'));
                card.classList.add('day-selected');
            }
            filterEvents(selectedDate);
        });
        return card;
    }

    document.getElementById('prevMonthBtn')?.addEventListener('click', () => {
        currentViewDate.setMonth(currentViewDate.getMonth() - 1);
        renderCalendarGrid();
    });
    document.getElementById('nextMonthBtn')?.addEventListener('click', () => {
        currentViewDate.setMonth(currentViewDate.getMonth() + 1);
        renderCalendarGrid();
    });

    document.getElementById('todayBtn')?.addEventListener('click', () => {
        currentViewDate = new Date();
        selectedDate = currentViewDate.toISOString().split('T')[0];
        renderCalendarGrid();
        filterEvents(selectedDate);
    });

    function filterEvents(dateStr) {
        const targetList = eventList || sidebarEventList;
        if (!targetList) return;
        targetList.innerHTML = '';
        const filtered = allUpcomingEvents.filter(e => e.date === dateStr);

        if (filtered.length === 0) {
            targetList.innerHTML = `<div class="empty-state"><p class="empty-msg">No events scheduled.</p></div>`;
            return;
        }

        filtered.forEach(event => {
            const card = document.createElement('div');
            card.className = 'event-card';
            card.dataset.id = event.id;
            card.innerHTML = `
                <div class="event-time">${event.time}</div>
                <div class="event-details"><h3>${event.title}</h3><p>${event.location || 'No location'}</p></div>
                <div class="event-actions">
                    <button class="edit-event-btn" title="Edit">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                    </button>
                    <button class="delete-event-btn" title="Delete">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                    </button>
                </div>`;
            eventList.appendChild(card);
        });
        updateStats();
    }

    function openEditModal(eventId) {
        const event = allUpcomingEvents.find(e => e.id == eventId);
        if (!event) return;
        document.getElementById('eventId').value = event.id;
        document.getElementById('eventTitle').value = event.title;
        document.getElementById('eventTime').value = event.time;
        document.getElementById('eventDate').value = event.date;
        document.getElementById('eventLocation').value = event.location || '';
        const modalHeader = eventModal.querySelector('.modal-header h2');
        const submitBtn = eventForm.querySelector('button[type="submit"]');
        if (modalHeader) modalHeader.textContent = 'Edit Event';
        if (submitBtn) submitBtn.textContent = 'Update Event';
        eventModal.classList.remove('hidden');
    }

    async function deleteEvent(eventId) {
        const confirmed = await window.showConfirmModal('Delete Event', 'Are you sure you want to delete this event?');
        if (!confirmed) return;
        try {
            const response = await fetch(`/api/events/${eventId}/`, {
                method: 'DELETE',
                headers: { 'X-CSRFToken': csrfToken }
            });
            if (response.status === 204) {
                allUpcomingEvents = allUpcomingEvents.filter(e => e.id != eventId);
                showNotification('Success', 'Event deleted');
                renderCalendarGrid();
                filterEvents(selectedDate);
            }
        } catch (error) {
            console.error('Error deleting event:', error);
        }
    }

    if (eventList) {
        eventList.addEventListener('click', (e) => {
            const editBtn = e.target.closest('.edit-event-btn');
            const deleteBtn = e.target.closest('.delete-event-btn');
            const card = e.target.closest('.event-card');
            if (card) {
                const eventId = card.dataset.id;
                if (editBtn) openEditModal(eventId);
                if (deleteBtn) deleteEvent(eventId);
            }
        });
    }

    let isSubmitting = false;
    if (eventForm) {
        eventForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (isSubmitting) return;
            const saveBtn = eventForm.querySelector('button[type="submit"]');
            isSubmitting = true;
            if (saveBtn) { saveBtn.disabled = true; saveBtn.classList.add('btn-loading'); }

            const eventId = document.getElementById('eventId').value;
            const url = eventId ? `/api/events/${eventId}/` : '/api/events/';
            const method = eventId ? 'PUT' : 'POST';

            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify({
                        'title': document.getElementById('eventTitle').value,
                        'time': document.getElementById('eventTime').value,
                        'date': document.getElementById('eventDate').value,
                        'location': document.getElementById('eventLocation').value
                    })
                });
                if (response.ok) {
                    const savedEvent = await response.json();
                    eventModal.classList.add('hidden');
                    eventForm.reset();
                    showNotification('Success', eventId ? 'Event updated!' : 'Event added!');
                    if (eventId) {
                        const index = allUpcomingEvents.findIndex(e => e.id == eventId);
                        if (index !== -1) allUpcomingEvents[index] = savedEvent;
                    } else {
                        allUpcomingEvents.push(savedEvent);
                    }
                    renderCalendarGrid();
                    filterEvents(selectedDate);
                }
            } catch (error) {
                console.error('Error saving event:', error);
            } finally {
                isSubmitting = false;
                if (saveBtn) { saveBtn.disabled = false; saveBtn.classList.remove('btn-loading'); }
            }
        });
    }

    function updateStats() {
        const pendingTasksCount = pendingTaskList?.querySelectorAll('.task-item').length || 0;
        const completedTasksCount = completedTaskList?.querySelectorAll('.task-item').length || 0;
        const upcomingEventsCount = eventList?.querySelectorAll('.event-card').length || 0;

        const taskStat = document.getElementById('taskCountStat');
        const taskCompletedStat = document.getElementById('taskCountCompletedStat');
        const eventStat = document.getElementById('eventCountStat');

        if (taskStat) taskStat.textContent = pendingTasksCount;
        if (taskCompletedStat) taskCompletedStat.textContent = completedTasksCount;
        if (eventStat) eventStat.textContent = upcomingEventsCount;

        handleEmptyTasks(pendingTasksCount, completedTasksCount);
    }

    function handleEmptyTasks(pendingCount, completedCount) {
        if (pendingTaskList) {
            const existingPendingEmpty = pendingTaskList.querySelector('.empty-state');
            if (pendingCount === 0) {
                if (!existingPendingEmpty) pendingTaskList.innerHTML = `<div class="empty-state"><p>No pending tasks. Relax or add a new one above!</p></div>`;
            } else if (existingPendingEmpty) existingPendingEmpty.remove();
        }

        if (completedTaskList) {
            const existingCompletedEmpty = completedTaskList.querySelector('.empty-state');
            if (completedCount === 0) {
                if (!existingCompletedEmpty) completedTaskList.innerHTML = `<div class="empty-state"><p>No completed tasks yet.</p></div>`;
            } else if (existingCompletedEmpty) existingCompletedEmpty.remove();
        }
    }

    // Modal Helpers
    const headerCreateBtn = document.getElementById('headerCreateBtn');

    function openEventCreationModal() {
        document.getElementById('eventId').value = '';
        eventForm.reset();
        const modalHeader = eventModal.querySelector('.modal-header h2');
        const submitBtn = eventForm.querySelector('button[type="submit"]');
        if (modalHeader) modalHeader.textContent = 'Add New Event';
        if (submitBtn) submitBtn.textContent = 'Save Event';
        eventModal.classList.remove('hidden');
    }

    headerCreateBtn?.addEventListener('click', openEventCreationModal);
    openModalBtn?.addEventListener('click', openEventCreationModal);
    closeModalBtn?.addEventListener('click', () => eventModal.classList.add('hidden'));
    eventModal?.addEventListener('click', (e) => { if (e.target === eventModal) eventModal.classList.add('hidden'); });

    profileBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        profileDropdown.classList.toggle('hidden');
    });
    document.addEventListener('click', () => profileDropdown?.classList.add('hidden'));

    // Initial Execution
    updateHeader();
    fetchEvents();
});

// Global helpers (Id-based, safe outside closure)
window.showConfirmModal = function (title, message) {
    return new Promise((resolve) => {
        const modal = document.getElementById('confirmModal');
        const titleEl = document.getElementById('confirmTitle');
        const msgEl = document.getElementById('confirmMessage');
        const okBtn = document.getElementById('okConfirmBtn');
        const cancelBtn = document.getElementById('cancelConfirmBtn');

        if (!modal || !titleEl || !msgEl || !okBtn || !cancelBtn) {
            console.error('Confirm modal elements missing');
            resolve(confirm(message));
            return;
        }

        titleEl.textContent = title;
        msgEl.textContent = message;
        modal.classList.remove('hidden');

        const handleOk = () => { modal.classList.add('hidden'); cleanup(); resolve(true); };
        const handleCancel = () => { modal.classList.add('hidden'); cleanup(); resolve(false); };
        const cleanup = () => { okBtn.removeEventListener('click', handleOk); cancelBtn.removeEventListener('click', handleCancel); };

        okBtn.addEventListener('click', handleOk);
        cancelBtn.addEventListener('click', handleCancel);
        modal.onclick = (e) => { if (e.target === modal) handleCancel(); };
    });
}
