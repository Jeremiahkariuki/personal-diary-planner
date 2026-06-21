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
    const diaryDetailModal = document.getElementById('diaryDetailModal');
    const closeDetailModalBtn = document.getElementById('closeDetailModal');
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

    // Sound Toggle Logic
    let isMuted = localStorage.getItem('isMuted') === 'true';
    const soundToggleBtn = document.getElementById('soundToggleBtn');
    const soundOnIcon = document.querySelector('.sound-on-icon');
    const soundOffIcon = document.querySelector('.sound-off-icon');

    function updateSoundUI() {
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
            // Show notification without playing the sound itself during toggle
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

        // Play sound only if not muted AND audio is requested
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
    let currentViewDate = new Date(); // Tracks which month is currently visible in the grid

    async function fetchEvents() {
        try {
            const response = await fetch('/events/');
            const data = await response.json();
            if (data.status === 'success') {
                allUpcomingEvents = data.events;
                renderCalendarGrid();
                filterEvents(selectedDate);
            }
        } catch (error) {
            console.error('Error fetching events:', error);
        }
    }

    function renderCalendarGrid() {
        const grid = document.getElementById('calendarGrid');
        const monthYearLabel = document.getElementById('calendarMonthYear');
        if (!grid || !monthYearLabel) return;

        grid.innerHTML = '';
        const year = currentViewDate.getFullYear();
        const month = currentViewDate.getMonth();

        // Update Label
        const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
        monthYearLabel.textContent = `${monthNames[month]} ${year}`;

        // Get days logic
        const firstDayOfMonth = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const daysInPrevMonth = new Date(year, month, 0).getDate();

        // Today's date for highlighting
        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];

        // 1. Previous Month Padding Days
        for (let i = firstDayOfMonth - 1; i >= 0; i--) {
            const dayNum = daysInPrevMonth - i;
            const card = createDayCard(year, month - 1, dayNum, true);
            grid.appendChild(card);
        }

        // 2. Current Month Days
        for (let i = 1; i <= daysInMonth; i++) {
            const card = createDayCard(year, month, i, false);
            const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(i).padStart(2, "0")}`;

            if (dateStr === todayStr) card.classList.add('day-today');
            if (dateStr === selectedDate) card.classList.add('day-selected');

            grid.appendChild(card);
        }

        // 3. Next Month Padding Days
        const totalSlots = 42; // 6 rows of 7 days
        const remainingSlots = totalSlots - grid.children.length;
        for (let i = 1; i <= remainingSlots; i++) {
            const card = createDayCard(year, month + 1, i, true);
            grid.appendChild(card);
        }
    }

    function createDayCard(year, month, day, isOutside) {
        // Correct date handling for cross-month navigation
        const d = new Date(year, month, day);
        const y = d.getFullYear();
        const m = d.getMonth() + 1;
        const dayFormatted = d.getDate();
        const dateStr = `${y}-${String(m).padStart(2, "0")}-${String(dayFormatted).padStart(2, "0")}`;

        const card = document.createElement('div');
        card.className = `calendar-day ${isOutside ? 'day-outside' : ''}`;
        card.innerHTML = `<span class="day-number">${day}</span>`;

        // Check for events
        const hasEvents = allUpcomingEvents.some(e => e.date === dateStr);
        if (hasEvents) {
            const dot = document.createElement('div');
            dot.className = 'event-dot';
            card.appendChild(dot);
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

    // Navigation Listeners
    document.getElementById('prevMonthBtn')?.addEventListener('click', () => {
        currentViewDate.setMonth(currentViewDate.getMonth() - 1);
        renderCalendarGrid();
    });

    document.getElementById('nextMonthBtn')?.addEventListener('click', () => {
        currentViewDate.setMonth(currentViewDate.getMonth() + 1);
        renderCalendarGrid();
    });

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
                <div class="event-actions">
                    <button class="edit-event-btn" title="Edit">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                    </button>
                    <button class="delete-event-btn" title="Delete">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                    </button>
                </div>
            `;
            eventList.appendChild(card);
        });
        updateStats();
    }

    // --- Events Logic Helpers ---
    function openEditModal(eventId) {
        const event = allUpcomingEvents.find(e => e.id == eventId);
        if (!event) return;

        // Populate form
        document.getElementById('eventId').value = event.id;
        document.getElementById('eventTitle').value = event.title;
        document.getElementById('eventTime').value = event.time;
        document.getElementById('eventDate').value = event.date;
        document.getElementById('eventLocation').value = event.location || '';

        // Change modal UI
        const modalHeader = eventModal.querySelector('.modal-header h2');
        const submitBtn = eventForm.querySelector('button[type="submit"]');
        if (modalHeader) modalHeader.textContent = 'Edit Event';
        if (submitBtn) submitBtn.textContent = 'Update Event';

        eventModal.classList.remove('hidden');
    }

    async function deleteEvent(eventId) {
        if (!confirm('Are you sure you want to delete this event?')) return;

        try {
            const response = await fetch(`/events/delete/${eventId}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken }
            });
            const data = await response.json();
            if (data.status === 'success') {
                allUpcomingEvents = allUpcomingEvents.filter(e => e.id != eventId);
                showNotification('Success', 'Event deleted');
                renderCalendarGrid();
                filterEvents(selectedDate);
            }
        } catch (error) {
            console.error('Error deleting event:', error);
            showNotification('Error', 'Failed to delete event');
        }
    }

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

    let isSubmitting = false;

    eventForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (isSubmitting) return;
        const saveBtn = eventForm.querySelector('button[type="submit"]');

        isSubmitting = true;
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.classList.add('btn-loading');
        }

        const eventId = document.getElementById('eventId').value;
        const title = document.getElementById('eventTitle').value;
        const time = document.getElementById('eventTime').value;
        const date = document.getElementById('eventDate').value;
        const location = document.getElementById('eventLocation').value;

        const url = eventId ? `/events/update/${eventId}/` : '/events/';

        try {
            const formData = new URLSearchParams({
                'title': title,
                'event_time': time,
                'date': date,
                'location': location
            });

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: formData
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();

            if (data.status === 'success') {
                eventModal.classList.add('hidden');
                eventForm.reset();
                showNotification('Success', eventId ? 'Event updated!' : 'Event added!');

                // Update local data
                if (data.event) {
                    if (eventId) {
                        const index = allUpcomingEvents.findIndex(e => e.id == eventId);
                        if (index !== -1) allUpcomingEvents[index] = data.event;
                    } else {
                        allUpcomingEvents.push(data.event);
                    }
                    allUpcomingEvents.sort((a, b) => a.date.localeCompare(b.date) || a.time.localeCompare(b.time));
                }

                selectedDate = date;
                setTimeout(() => {
                    renderCalendarGrid();
                    filterEvents(selectedDate);
                }, 50);
            } else {
                showNotification('Error', 'Failed to save event.');
            }
        } catch (error) {
            console.error('Error saving event:', error);
            showNotification('Error', 'Something went wrong. Please try again.');
        } finally {
            isSubmitting = false;
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.classList.remove('btn-loading');
            }
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
        const entryId = document.getElementById('diaryEntryId').value;
        const url = entryId ? `/diary/update/${entryId}/` : '/diary/save/';

        saveBtn.classList.add('btn-loading');

        try {
            const response = await fetch(url, {
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
                showNotification('Success', entryId ? 'Diary entry updated!' : 'Diary entry saved!');

                // Mood icon mapping
                const moodIcons = {
                    'happy': '😊',
                    'neutral': '😐',
                    'sad': '😔',
                    'excited': '🤩',
                    'stressed': '😫'
                };

                // Update Preview UI with professional layout

                // Update Preview UI with professional layout
                diaryPreview.innerHTML = `
                    <div class="diary-mood-badge mood-${data.entry.mood}">
                        <span class="mood-icon">${moodIcons[data.entry.mood]}</span>
                        <span class="mood-text">${data.entry.mood.charAt(0).toUpperCase() + data.entry.mood.slice(1)}</span>
                    </div>
                    <div class="diary-content-preview">
                        <p class="preview-text">"${data.entry.content.substring(0, 180)}${data.entry.content.length > 180 ? '...' : ''}"</p>
                    </div>
                    <div class="diary-footer">
                        <span class="date">${data.entry.created_at.split(' ')[0] + ' ' + data.entry.created_at.split(' ')[1] + ' ' + data.entry.created_at.split(' ')[2]}</span>
                        <div class="diary-card-actions">
                            <button class="icon-btn edit-diary-btn" title="Edit Entry" data-id="${data.entry.id}">
                                <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
                            </button>
                            <button class="icon-btn delete-diary-btn" title="Delete Entry" data-id="${data.entry.id}">
                                <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                            </button>
                        </div>
                        <button id="readMoreBtn" class="read-more-link" data-id="${data.entry.id}">Read Full Entry →</button>
                    </div>
                    <!-- Hidden full content for modal -->
                    <div id="fullDiaryId" style="display:none;">${data.entry.id}</div>
                    <div id="fullDiaryContent" style="display:none;">${data.entry.content}</div>
                    <div id="fullDiaryMood" style="display:none;">${data.entry.mood}</div>
                    <div id="fullDiaryDate" style="display:none;">${data.entry.created_at}</div>
                `;

                diaryForm.reset();
                document.getElementById('diaryEntryId').value = '';
                saveBtn.textContent = 'Save Entry';
                diaryModal.classList.add('hidden');
                initDiaryDetailHandler(); // Re-attach listener to new button
            }
        } catch (error) {
            console.error('Error saving diary:', error);
            showNotification('Error', 'Failed to save entry');
        } finally {
            saveBtn.classList.remove('btn-loading');
        }
    });

    function initDiaryDetailHandler() {
        const readMoreBtn = document.getElementById('readMoreBtn');
        if (readMoreBtn) {
            readMoreBtn.addEventListener('click', () => {
                const content = document.getElementById('fullDiaryContent').textContent;
                const mood = document.getElementById('fullDiaryMood').textContent;
                const date = document.getElementById('fullDiaryDate').textContent;

                const moodIcons = {
                    'happy': '😊', 'neutral': '😐', 'sad': '😔', 'excited': '🤩', 'stressed': '😫'
                };

                document.getElementById('detailMoodIcon').textContent = moodIcons[mood] || '😐';
                document.getElementById('detailMoodText').textContent = mood.charAt(0).toUpperCase() + mood.slice(1);
                document.getElementById('detailDate').textContent = date;
                document.getElementById('detailContentText').textContent = content;

                diaryDetailModal.classList.remove('hidden');
            });
        }
    }

    if (closeDetailModalBtn) {
        closeDetailModalBtn.addEventListener('click', () => diaryDetailModal.classList.add('hidden'));
    }

    // Edit and Delete Listeners
    document.addEventListener('click', async (e) => {
        // Edit Entry (either from preview card or detail modal)
        const editBtn = e.target.closest('.edit-diary-btn') || e.target.closest('#editEntryBtn');
        if (editBtn) {
            const id = document.getElementById('fullDiaryId')?.textContent.trim();
            const content = document.getElementById('fullDiaryContent')?.textContent.trim();
            const mood = document.getElementById('fullDiaryMood')?.textContent.trim();
            if (id) {
                document.getElementById('diaryEntryId').value = id;
                document.getElementById('diaryContent').value = content;
                const moodRadio = document.querySelector(`input[name="mood"][value="${mood}"]`);
                if (moodRadio) moodRadio.checked = true;

                document.getElementById('saveDiaryBtn').textContent = 'Update Entry';
                diaryDetailModal.classList.add('hidden');
                diaryModal.classList.remove('hidden');
            }
        }

        // Delete Entry
        const deleteBtn = e.target.closest('.delete-diary-btn') || e.target.closest('#deleteEntryBtn');
        if (deleteBtn) {
            const id = deleteBtn.dataset.id || document.getElementById('fullDiaryId')?.textContent.trim();
            if (id && confirm('Are you sure you want to completely delete this diary entry?')) {
                try {
                    const response = await fetch(`/diary/delete/${id}/`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': csrfToken }
                    });
                    const data = await response.json();

                    if (data.status === 'success') {
                        showNotification('Success', 'Diary entry deleted.');
                        diaryDetailModal.classList.add('hidden');

                        if (data.latest_entry) {
                            const entry = data.latest_entry;
                            const moodIcons = { 'happy': '😊', 'neutral': '😐', 'sad': '😔', 'excited': '🤩', 'stressed': '😫' };
                            diaryPreview.innerHTML = `
                                <div class="diary-mood-badge mood-${entry.mood}">
                                    <span class="mood-icon">${moodIcons[entry.mood]}</span>
                                    <span class="mood-text">${entry.mood.charAt(0).toUpperCase() + entry.mood.slice(1)}</span>
                                </div>
                                <div class="diary-content-preview">
                                    <p class="preview-text">"${entry.content.substring(0, 180)}${entry.content.length > 180 ? '...' : ''}"</p>
                                </div>
                                <div class="diary-footer">
                                    <span class="date">${entry.created_at.split(' ')[0] + ' ' + entry.created_at.split(' ')[1] + ' ' + entry.created_at.split(' ')[2]}</span>
                                    <div class="diary-card-actions">
                                        <button class="icon-btn edit-diary-btn" title="Edit Entry" data-id="${entry.id}">
                                            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
                                        </button>
                                        <button class="icon-btn delete-diary-btn" title="Delete Entry" data-id="${entry.id}">
                                            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                                        </button>
                                    </div>
                                    <button id="readMoreBtn" class="read-more-link" data-id="${entry.id}">Read Full Entry →</button>
                                </div>
                                <!-- Hidden full content for modal -->
                                <div id="fullDiaryId" style="display:none;">${entry.id}</div>
                                <div id="fullDiaryContent" style="display:none;">${entry.content}</div>
                                <div id="fullDiaryMood" style="display:none;">${entry.mood}</div>
                                <div id="fullDiaryDate" style="display:none;">${entry.created_at}</div>
                            `;
                            initDiaryDetailHandler();
                        } else {
                            diaryPreview.innerHTML = `
                                <div class="empty-diary">
                                    <p class="preview-text">"No entries yet. Start writing your journey today..."</p>
                                    <span class="date">New Beginning</span>
                                </div>
                            `;
                        }
                    }
                } catch (error) {
                    console.error('Error deleting entry:', error);
                    showNotification('Error', 'Failed to delete entry');
                }
            }
        }
    });

    // Modal click-outside logic for detail modal
    diaryDetailModal?.addEventListener('click', (e) => {
        if (e.target === diaryDetailModal) diaryDetailModal.classList.add('hidden');
    });

    // Initial attach
    initDiaryDetailHandler();

    // --- Helpers ---
    function updateStats() {
        const pendingTasksCount = pendingTaskList.querySelectorAll('.task-item').length;
        const completedTasksCount = completedTaskList.querySelectorAll('.task-item').length;
        const upcomingEventsCount = eventList.querySelectorAll('.event-card').length;

        const taskStat = document.getElementById('taskCountStat');
        const taskCompletedStat = document.getElementById('taskCountCompletedStat');
        const eventStat = document.getElementById('eventCountStat');

        if (taskStat) taskStat.textContent = pendingTasksCount;
        if (taskCompletedStat) taskCompletedStat.textContent = completedTasksCount;
        if (eventStat) eventStat.textContent = upcomingEventsCount;

        handleEmptyTasks(pendingTasksCount, completedTasksCount);
    }

    function handleEmptyTasks(pendingCount, completedCount) {
        // Handle Pending
        const existingPendingEmpty = pendingTaskList.querySelector('.empty-state');
        if (pendingCount === 0) {
            if (!existingPendingEmpty) {
                pendingTaskList.innerHTML = `
                    <div class="empty-state">
                        <p>No pending tasks. Relax or add a new one above!</p>
                    </div>
                `;
            }
        } else if (existingPendingEmpty) {
            existingPendingEmpty.remove();
        }

        // Handle Completed
        const existingCompletedEmpty = completedTaskList.querySelector('.empty-state');
        if (completedCount === 0) {
            if (!existingCompletedEmpty) {
                completedTaskList.innerHTML = `
                    <div class="empty-state">
                        <p>No completed tasks yet.</p>
                    </div>
                `;
            }
        } else if (existingCompletedEmpty) {
            existingCompletedEmpty.remove();
        }
    }

    // Modal Helpers
    openModalBtn.addEventListener('click', () => {
        document.getElementById('eventId').value = '';
        eventForm.reset();
        const modalHeader = eventModal.querySelector('.modal-header h2');
        const submitBtn = eventForm.querySelector('button[type="submit"]');
        if (modalHeader) modalHeader.textContent = 'Add New Event';
        if (submitBtn) submitBtn.textContent = 'Save Event';
        eventModal.classList.remove('hidden');
    });
    closeModalBtn.addEventListener('click', () => eventModal.classList.add('hidden'));
    eventModal.addEventListener('click', (e) => { if (e.target === eventModal) eventModal.classList.add('hidden'); });

    openDiaryModalBtn.addEventListener('click', () => {
        document.getElementById('diaryEntryId').value = '';
        document.getElementById('saveDiaryBtn').textContent = 'Save Entry';
        diaryForm.reset();
        diaryModal.classList.remove('hidden');
    });

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
