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
    const openModalBtn = document.querySelector('.events-section .add-btn');
    const closeModalBtn = document.getElementById('closeModal');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

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

        displayDailyQuote();
    }

    async function displayDailyQuote() {
        const quoteEl = document.getElementById('dailyQuote');
        if (!quoteEl) return;

        try {
            const response = await fetch('/quote/random/');
            const data = await response.json();
            if (data.status === 'success') {
                quoteEl.innerHTML = `"${data.quote.text}" <br> <span style="font-size: 0.8rem; font-style: normal; opacity: 0.7;">— ${data.quote.author}</span>`;
            }
        } catch (error) {
            console.error('Error fetching quote:', error);
            // Fallback for offline/error
            quoteEl.textContent = '"Believe you can and you\'re halfway there."';
        }
    }

    window.showNotification = function (title, message) {
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

        // play a standard sound (optional/placeholder)
        const audio = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3');
        audio.play().catch(() => console.log('Audio playback prevented'));

        setTimeout(() => {
            toast.style.animation = 'slideIn 0.5s ease reverse forwards';
            setTimeout(() => toast.remove(), 500);
        }, 5000);
    }

    // --- Tasks Logic ---
    async function addTask(title, dueDate, dueTime) {
        try {
            const response = await fetch('/tasks/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: new URLSearchParams({
                    'title': title,
                    'due_date': dueDate || '',
                    'due_time': dueTime || ''
                })
            });
            const data = await response.json();
            console.log('Task saved response:', data);
            if (data.status === 'success') {
                renderTask(data.task);
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
        targetList.appendChild(item);
    }

    // Delegate clicks for both lists
    [pendingTaskList, completedTaskList].forEach(list => {
        list.addEventListener('click', async (e) => {
            const taskItem = e.target.closest('.task-item');
            if (!taskItem) return;
            const taskId = taskItem.dataset.id;

            if (e.target.classList.contains('task-checkbox')) {
                try {
                    const response = await fetch(`/tasks/toggle/${taskId}/`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': csrfToken }
                    });
                    const data = await response.json();
                    if (data.status === 'success') {
                        taskItem.classList.toggle('completed', data.completed);
                        const targetList = data.completed ? completedTaskList : pendingTaskList;
                        targetList.appendChild(taskItem); // Move element
                        updateStats();
                    }
                } catch (error) {
                    console.error('Error toggling task:', error);
                }
            } else if (e.target.classList.contains('delete-task-btn')) {
                try {
                    const response = await fetch(`/tasks/delete/${taskId}/`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': csrfToken }
                    });
                    const data = await response.json();
                    if (data.status === 'success') {
                        taskItem.remove();
                        updateStats();
                    }
                } catch (error) {
                    console.error('Error deleting task:', error);
                }
            }
        });
    });

    quickTaskForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const title = document.getElementById('newTaskTitle').value;
        const dueDate = document.getElementById('newTaskDate').value;
        const dueTime = document.getElementById('newTaskTime').value;
        if (title) addTask(title, dueDate, dueTime);
    });

    const clearTasksBtn = document.getElementById('clearTasksBtn');
    if (clearTasksBtn) {
        clearTasksBtn.addEventListener('click', async () => {
            if (!confirm('Clear all pending tasks?')) return;
            try {
                const response = await fetch('/tasks/clear-pending/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken }
                });
                const data = await response.json();
                if (data.status === 'success') {
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

    async function fetchEvents() {
        try {
            const response = await fetch('/events/');
            const data = await response.json();
            if (data.status === 'success') {
                allUpcomingEvents = data.events;
                renderDateStrip();
                filterEvents(selectedDate);
            }
        } catch (error) {
            console.error('Error fetching events:', error);
        }
    }

    function renderDateStrip() {
        const dateStrip = document.getElementById('dateStrip');
        if (!dateStrip) return;
        dateStrip.innerHTML = '';

        const today = new Date();
        const daysToShow = 14;

        for (let i = 0; i < daysToShow; i++) {
            const d = new Date(today);
            d.setDate(today.getDate() + i);
            const dateStr = d.toISOString().split('T')[0];

            const card = document.createElement('div');
            card.className = `date-card ${dateStr === selectedDate ? 'active' : ''}`;
            card.dataset.date = dateStr;

            const dayName = d.toLocaleDateString('en-US', { weekday: 'short' });
            const dayNum = d.getDate();

            // Check if this date has events
            const hasEvents = allUpcomingEvents.some(e => e.date === dateStr);

            card.innerHTML = `
                <span class="day-name">${dayName}</span>
                <span class="day-number">${dayNum}</span>
                ${hasEvents ? '<div class="has-event-dot"></div>' : ''}
            `;

            card.addEventListener('click', () => {
                document.querySelectorAll('.date-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                selectedDate = dateStr;
                filterEvents(dateStr);
            });

            dateStrip.appendChild(card);
        }
    }

    function filterEvents(dateStr) {
        const eventList = document.getElementById('eventList');
        if (!eventList) return;

        eventList.innerHTML = '';
        const filtered = allUpcomingEvents.filter(e => e.date === dateStr);

        if (filtered.length === 0) {
            eventList.innerHTML = `
                <div class="empty-state">
                    <p class="empty-msg">No events scheduled for this day.</p>
                </div>
            `;
            return;
        }

        filtered.forEach(event => {
            const card = document.createElement('div');
            card.className = 'event-card';
            card.dataset.id = event.id;

            card.innerHTML = `
                <div class="event-time">${event.time}</div>
                <div class="event-details">
                    <h3>${event.title}</h3>
                    <p>${event.location || 'No location'}</p>
                </div>
            `;
            eventList.appendChild(card);
        });
        updateStats();
    }

    eventForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const title = document.getElementById('eventTitle').value;
        const time = document.getElementById('eventTime').value;
        const date = document.getElementById('eventDate').value;
        const location = document.getElementById('eventLocation').value;

        try {
            const response = await fetch('/events/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: new URLSearchParams({
                    'title': title,
                    'event_time': time,
                    'date': date,
                    'location': location
                })
            });
            const data = await response.json();
            if (data.status === 'success') {
                // Instead of reloading, we can just fetch again and update UI
                eventModal.classList.add('hidden');
                eventForm.reset();
                showNotification('Success', 'Event added!');
                fetchEvents(); // Refresh data
            }
        } catch (error) {
            console.error('Error adding event:', error);
        }
    });

    // --- Diary Logic ---
    const diaryModal = document.getElementById('diaryModal');
    const diaryForm = document.getElementById('diaryForm');
    const openDiaryModalBtn = document.getElementById('openDiaryModal');
    const closeDiaryModalBtn = document.getElementById('closeDiaryModal');
    const diaryPreview = document.getElementById('diaryPreview');

    diaryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const saveBtn = document.getElementById('saveDiaryBtn');
        const content = document.getElementById('diaryContent').value;
        const mood = document.querySelector('input[name="mood"]:checked').value;

        saveBtn.classList.add('btn-loading');

        try {
            const response = await fetch('/diary/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: new URLSearchParams({
                    'content': content,
                    'mood': mood
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                showNotification('Success', 'Diary entry saved!');

                // Mood icon mapping
                const moodIcons = {
                    'happy': '😊',
                    'neutral': '😐',
                    'sad': '😔',
                    'excited': '🤩',
                    'stressed': '😫'
                };

                // Update Preview UI
                diaryPreview.innerHTML = `
                    <p class="preview-text">"${content.substring(0, 100)}${content.length > 100 ? '...' : ''}" ${moodIcons[mood]}</p>
                    <span class="date">${data.entry.created_at}</span>
                `;

                diaryForm.reset();
                diaryModal.classList.add('hidden');
            }
        } catch (error) {
            console.error('Error saving diary:', error);
            showNotification('Error', 'Failed to save entry');
        } finally {
            saveBtn.classList.remove('btn-loading');
        }
    });

    // --- Helpers ---
    function updateStats() {
        const pendingTasks = pendingTaskList.querySelectorAll('.task-item').length;
        const completedTasksCount = completedTaskList.querySelectorAll('.task-item').length;
        const upcomingEvents = eventList.querySelectorAll('.event-card').length;

        const taskStat = document.getElementById('taskCountStat');
        const taskCompletedStat = document.getElementById('taskCountCompletedStat');
        const eventStat = document.getElementById('eventCountStat');

        if (taskStat) taskStat.textContent = pendingTasks;
        if (taskCompletedStat) taskCompletedStat.textContent = completedTasksCount;
        if (eventStat) eventStat.textContent = upcomingEvents;
    }

    // Modal Helpers
    openModalBtn.addEventListener('click', () => eventModal.classList.remove('hidden'));
    closeModalBtn.addEventListener('click', () => eventModal.classList.add('hidden'));
    eventModal.addEventListener('click', (e) => { if (e.target === eventModal) eventModal.classList.add('hidden'); });

    openDiaryModalBtn.addEventListener('click', () => diaryModal.classList.remove('hidden'));
    closeDiaryModalBtn.addEventListener('click', () => diaryModal.classList.add('hidden'));
    diaryModal.addEventListener('click', (e) => { if (e.target === diaryModal) diaryModal.classList.add('hidden'); });

    profileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        profileDropdown.classList.toggle('hidden');
    });

    document.addEventListener('click', (e) => {
        if (!profileDropdown.classList.contains('hidden') && !profileDropdown.contains(e.target)) {
            profileDropdown.classList.add('hidden');
        }
    });

    // Init
    updateHeader();
    fetchEvents();
});
