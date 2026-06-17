document.addEventListener('DOMContentLoaded', () => {
    console.log('Jdiary Initialized');

    // Selectors
    const profileBtn = document.getElementById('profileBtn');
    const profileDropdown = document.getElementById('profileDropdown');
    const headerDate = document.querySelector('.dashboard-header p');
    const eventList = document.querySelector('.event-list');
    const taskList = document.querySelector('.task-list');
    const eventModal = document.getElementById('eventModal');
    const eventForm = document.getElementById('eventForm');
    const quickTaskForm = document.getElementById('quickTaskForm');
    const openModalBtn = document.querySelector('.events-section .add-btn');
    const closeModalBtn = document.getElementById('closeModal');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Functions
    function updateHeader() {
        const now = new Date();
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        headerDate.textContent = now.toLocaleDateString('en-US', options);
    }

    function showNotification(title, message) {
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
    async function addTask(title) {
        try {
            const response = await fetch('/tasks/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: new URLSearchParams({ 'title': title })
            });
            const data = await response.json();
            if (data.status === 'success') {
                renderTask(data.task);
                updateStats();
                quickTaskForm.reset();
            }
        } catch (error) {
            console.error('Error adding task:', error);
        }
    }

    function renderTask(task) {
        const item = document.createElement('div');
        item.className = `task-item ${task.completed ? 'completed' : ''}`;
        item.dataset.id = task.id;
        item.innerHTML = `
            <input type="checkbox" ${task.completed ? 'checked' : ''} class="task-checkbox">
            <span class="task-title">${task.title}</span>
            <button class="delete-task-btn">&times;</button>
        `;

        // Remove empty message if it exists
        const emptyMsg = taskList.querySelector('.empty-msg');
        if (emptyMsg) emptyMsg.remove();

        taskList.appendChild(item);
    }

    taskList.addEventListener('click', async (e) => {
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
                    if (taskList.children.length === 0) {
                        taskList.innerHTML = '<p class="empty-msg">No tasks yet.</p>';
                    }
                }
            } catch (error) {
                console.error('Error deleting task:', error);
            }
        }
    });

    quickTaskForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const title = document.getElementById('newTaskTitle').value;
        if (title) addTask(title);
    });

    // --- Events Logic ---
    async function fetchEvents() {
        try {
            const response = await fetch('/events/');
            const data = await response.json();
            if (data.status === 'success') {
                renderEventsList(data.events);
            }
        } catch (error) {
            console.error('Error fetching events:', error);
        }
    }

    function renderEventsList(events) {
        eventList.innerHTML = '';
        if (events.length === 0) {
            eventList.innerHTML = '<p class="empty-msg">No upcoming events.</p>';
            return;
        }

        // Group by date
        const grouped = events.reduce((acc, event) => {
            if (!acc[event.date]) acc[event.date] = [];
            acc[event.date].push(event);
            return acc;
        }, {});

        const todayStr = new Date().toISOString().split('T')[0];

        Object.keys(grouped).sort().forEach(date => {
            const dateGroup = document.createElement('div');
            dateGroup.className = 'date-group';

            const d = new Date(date);
            const dateHeader = document.createElement('h3');
            dateHeader.className = 'date-header';
            dateHeader.textContent = (date === todayStr) ? 'Today' : d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

            dateGroup.appendChild(dateHeader);

            grouped[date].forEach(event => {
                const card = document.createElement('div');
                card.className = `event-card ${date === todayStr ? 'today-highlight' : ''}`;
                card.dataset.id = event.id;

                card.innerHTML = `
                    <div class="event-time">${event.time}</div>
                    <div class="event-details">
                        <h3>${event.title}</h3>
                        <p>${event.location || 'No location'}</p>
                    </div>
                `;
                dateGroup.appendChild(card);
            });

            eventList.appendChild(dateGroup);
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
                showNotification('Success', 'Event added!');
                fetchEvents();
                eventForm.reset();
                eventModal.classList.add('hidden');
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
        const pendingTasks = taskList.querySelectorAll('.task-item:not(.completed)').length;
        const upcomingEvents = eventList.querySelectorAll('.event-card').length;

        const taskStat = document.getElementById('taskCountStat');
        const eventStat = document.getElementById('eventCountStat');

        if (taskStat) taskStat.textContent = pendingTasks;
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
    // fetchEvents(); // Initial state is rendered by Django template
});
