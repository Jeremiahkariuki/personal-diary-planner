// static/js/reminders.js
// Handles setting and managing email reminders for events, tasks, and diary entries.

document.addEventListener('DOMContentLoaded', () => {
    // Inject the reminder modal elements dynamically into the body
    injectReminderModal();

    // Attach click listener globally using delegation for any class trigger
    document.addEventListener('click', (e) => {
        const trigger = e.target.closest('.reminder-trigger-btn');
        if (trigger) {
            e.preventDefault();
            const targetId = trigger.getAttribute('data-target-id');
            const targetType = trigger.getAttribute('data-target-type');
            const targetTitle = trigger.getAttribute('data-target-title');
            
            showReminderModal(targetType, targetId, targetTitle);
        }
    });
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Inject the glassmorphism modal
function injectReminderModal() {
    if (document.getElementById('reminderModal')) return;

    const modalHTML = `
    <div id="reminderModal" class="modal-overlay hidden" style="z-index: 10000; display: none;">
        <div class="glass-card modal-content" style="max-width: 450px; padding: 2rem; border-radius: 20px;">
            <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h2 style="font-size: 1.5rem; margin: 0; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
                    <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                    </svg>
                    Email Reminder
                </h2>
                <button id="closeReminderModalBtn" class="icon-btn" style="background: none; border: none; color: var(--text-secondary); font-size: 1.8rem; cursor: pointer; padding: 0; line-height: 1;">&times;</button>
            </div>
            
            <div id="reminderConfigArea">
                <p id="reminderTargetInfo" style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.25rem; font-weight: 500; background: rgba(255,255,255,0.05); padding: 0.8rem; border-radius: 10px; border-left: 3px solid var(--accent-primary);"></p>
                
                <form id="reminderForm" class="modal-form" style="display: flex; flex-direction: column; gap: 1rem;">
                    <input type="hidden" id="reminderTargetId">
                    <input type="hidden" id="reminderTargetType">
                    
                    <div class="form-group" style="display: flex; flex-direction: column; gap: 0.5rem;">
                        <label for="reminderDateTime" style="font-size: 0.85rem; color: var(--text-secondary); font-weight: 600;">Choose Date & Time</label>
                        <input type="datetime-local" id="reminderDateTime" required style="width: 100%; padding: 0.8rem; border-radius: 12px; border: 1px solid var(--glass-border); background: var(--glass-bg); color: var(--text-primary); outline: none; font-family: inherit;">
                    </div>
                    
                    <button type="submit" class="primary-btn" style="width: 100%; padding: 0.8rem; border-radius: 12px; font-weight: 600; cursor: pointer; background: var(--accent-primary); border: none; color: white; display: flex; justify-content: center; align-items: center; gap: 6px;">
                        Set Email Reminder
                    </button>
                </form>
            </div>
            
            <hr style="border: 0; height: 1px; background: var(--glass-border); margin: 1.5rem 0;">
            
            <div>
                <h3 style="font-size: 1.1rem; margin-bottom: 0.8rem; color: var(--text-primary);">Configured Reminders</h3>
                <div id="reminderListContainer" style="max-height: 155px; overflow-y: auto; display: flex; flex-direction: column; gap: 0.8rem; padding-right: 4px;">
                    <p style="color: var(--text-secondary); font-size: 0.85rem; font-style: italic;">Loading...</p>
                </div>
            </div>
        </div>
    </div>
    `;

    const div = document.createElement('div');
    div.innerHTML = modalHTML.trim();
    const modalElement = div.firstChild;
    document.body.appendChild(modalElement);
    
    // Wire close listener
    document.getElementById('closeReminderModalBtn').addEventListener('click', hideReminderModal);
    
    // Close on clicking outside content area
    modalElement.addEventListener('click', (e) => {
        if (e.target === modalElement) {
            hideReminderModal();
        }
    });

    // Wire form submit
    document.getElementById('reminderForm').addEventListener('submit', handleReminderSubmit);
}

function showReminderModal(type, id, title) {
    const modal = document.getElementById('reminderModal');
    if (!modal) return;
    
    document.getElementById('reminderTargetId').value = id;
    document.getElementById('reminderTargetType').value = type;
    
    const formattedType = type.charAt(0).toUpperCase() + type.slice(1);
    document.getElementById('reminderTargetInfo').textContent = `${formattedType}: "${title}"`;
    
    // Set default reminder time to 1 hour from now formatted for datetime-local
    const now = new Date();
    now.setHours(now.getHours() + 1);
    now.setSeconds(0);
    now.setMilliseconds(0);
    
    // timezone adjustment for ISO string local representation
    const tzOffset = now.getTimezoneOffset() * 60000; 
    const localISOTime = (new Date(now.getTime() - tzOffset)).toISOString().slice(0, 16);
    document.getElementById('reminderDateTime').value = localISOTime;
    
    // Open modal visually
    modal.style.display = 'flex';
    modal.classList.remove('hidden');
    
    loadReminders(type, id);
}

function hideReminderModal() {
    const modal = document.getElementById('reminderModal');
    if (!modal) return;
    modal.classList.add('hidden');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 200);
}

// Fetch reminders from REST API
function loadReminders(type, id) {
    const container = document.getElementById('reminderListContainer');
    if (!container) return;
    
    container.innerHTML = '<p style="color: var(--text-secondary); font-size: 0.85rem; font-style: italic;">Loading reminders...</p>';
    
    let url = `/api/reminders/?${type}=${id}`;
    
    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error("Could not load reminders.");
            return response.json();
        })
        .then(data => {
            renderReminderList(data, type, id);
        })
        .catch(err => {
            console.error(err);
            container.innerHTML = `<p style="color: #ef4444; font-size: 0.85rem;">Error loading reminders.</p>`;
        });
}

function renderReminderList(reminders, type, id) {
    const container = document.getElementById('reminderListContainer');
    if (!container) return;
    
    if (reminders.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); font-size: 0.85rem; font-style: italic;">No email reminders set for this item.</p>';
        return;
    }
    
    let html = '';
    reminders.forEach(rem => {
        const statusClass = rem.email_sent ? 'sent' : 'pending';
        const statusLabel = rem.email_sent ? '✓ Sent' : '⏰ Pending';
        const formattedTime = new Date(rem.reminder_time).toLocaleString();
        
        html += `
        <div class="reminder-item" style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03); padding: 0.6rem 0.8rem; border-radius: 10px; border: 1px solid var(--glass-border);">
            <div style="display: flex; flex-direction: column; gap: 2px;">
                <span style="font-size: 0.85rem; color: var(--text-primary); font-weight: 500;">${formattedTime}</span>
                <span style="font-size: 0.75rem; font-weight: 600; color: ${rem.email_sent ? '#10b981' : '#f59e0b'};">${statusLabel}</span>
            </div>
            <button class="delete-reminder-btn icon-btn" data-reminder-id="${rem.id}" style="background: none; border: none; color: #ef4444; cursor: pointer; padding: 4px; border-radius: 6px; display: flex; align-items: center; justify-content: center; opacity: 0.8; transition: all 0.2s;" title="Cancel Reminder">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
        </div>
        `;
    });
    
    container.innerHTML = html;
    
    // Attach delete listeners
    container.querySelectorAll('.delete-reminder-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const remId = btn.getAttribute('data-reminder-id');
            deleteReminder(remId, type, id);
        });
    });
}

function handleReminderSubmit(e) {
    e.preventDefault();
    
    const targetId = document.getElementById('reminderTargetId').value;
    const targetType = document.getElementById('reminderTargetType').value;
    const dateTime = document.getElementById('reminderDateTime').value;
    
    if (!dateTime) return;
    
    // Format payload
    const payload = {
        reminder_time: new Date(dateTime).toISOString()
    };
    
    if (targetType === 'diary') {
        payload.diary_entry = parseInt(targetId);
    } else if (targetType === 'event') {
        payload.event = parseInt(targetId);
    } else if (targetType === 'task') {
        payload.task = parseInt(targetId);
    }
    
    fetch('/api/reminders/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(payload)
    })
    .then(async response => {
        const data = await response.json();
        if (!response.ok) {
            let errorMsg = "Could not schedule reminder.";
            if (data.non_field_errors) errorMsg = data.non_field_errors[0];
            else if (typeof data === 'object') errorMsg = Object.values(data).flat().join(' ');
            throw new Error(errorMsg);
        }
        return data;
    })
    .then(() => {
        // Trigger generic custom audio alert if present
        if (window.playSuccessSound) {
            window.playSuccessSound();
        } else {
            console.log("Success audio sound function not found");
        }
        loadReminders(targetType, targetId);
    })
    .catch(err => {
        console.error(err);
        alert(err.message || "An error occurred.");
    });
}

function deleteReminder(reminderId, type, id) {
    if (!confirm("Are you sure you want to cancel this reminder?")) return;
    
    fetch(`/api/reminders/${reminderId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (!response.ok) throw new Error("Could not cancel reminder.");
        loadReminders(type, id);
    })
    .catch(err => {
        console.error(err);
        alert(err.message || "An error occurred.");
    });
}
