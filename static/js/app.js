document.addEventListener('DOMContentLoaded', () => {
    console.log('Jdiary Initialized');

    // Selectors
    const profileBtn = document.getElementById('profileBtn');
    const profileDropdown = document.getElementById('profileDropdown');
    const headerDate = document.querySelector('.dashboard-header p');
    const eventList = document.querySelector('.event-list');
    const eventModal = document.getElementById('eventModal');
    const eventForm = document.getElementById('eventForm');
    const openModalBtn = document.querySelector('.events-section .add-btn');
    const closeModalBtn = document.getElementById('closeModal');

    // State
    let events = JSON.parse(localStorage.getItem('ethereal_events')) || [];

    // Functions
    function updateHeader() {
        const now = new Date();
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        headerDate.textContent = now.toLocaleDateString('en-US', options);
    }

    function renderEvents() {
        eventList.innerHTML = '';
        const upcomingEvents = events
            .filter(e => !e.completed)
            .sort((a, b) => a.time.localeCompare(b.time));

        upcomingEvents.forEach(event => {
            const card = document.createElement('div');
            card.className = 'event-card';
            card.innerHTML = `
                <div class="event-time">${event.time}</div>
                <div class="event-details">
                    <h3>${event.title}</h3>
                    <p>${event.location || 'No location'}</p>
                </div>
            `;
            eventList.appendChild(card);
        });

        // Update stats
        document.querySelector('.stat-item:first-child .value').textContent = upcomingEvents.length;
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

    function checkNotifications() {
        const now = new Date();
        const currentTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

        events.forEach(event => {
            if (event.time === currentTime && !event.notified) {
                showNotification(`Reminder: ${event.title}`, `Happening now at ${event.location}`);
                event.notified = true;
                localStorage.setItem('ethereal_events', JSON.stringify(events));
            }
        });
    }

    // Event Listeners
    openModalBtn.addEventListener('click', () => {
        eventModal.classList.remove('hidden');
    });

    closeModalBtn.addEventListener('click', () => {
        eventModal.classList.add('hidden');
    });

    eventModal.addEventListener('click', (e) => {
        if (e.target === eventModal) eventModal.classList.add('hidden');
    });

    eventForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const newEvent = {
            id: Date.now(),
            title: document.getElementById('eventTitle').value,
            time: document.getElementById('eventTime').value,
            location: document.getElementById('eventLocation').value,
            notified: false,
            completed: false
        };

        events.push(newEvent);
        localStorage.setItem('ethereal_events', JSON.stringify(events));

        renderEvents();
        eventForm.reset();
        eventModal.classList.add('hidden');
    });

    // Profile Dropdown Toggle
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
    renderEvents();
    setInterval(checkNotifications, 30000); // Check every 30 seconds
});
