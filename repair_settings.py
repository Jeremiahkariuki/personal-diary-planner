import os

file_path = r"C:\Users\Administrator\Desktop\personal-diary-planner\templates\settings.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Flatten option tags
bad_opt_1 = """                                                <option value="whole_diary" {% if share.share_type=='whole_diary'
                                                    %}selected{% endif %}>📚 Entire Diary</option>"""
good_opt_1 = """                                                <option value="whole_diary" {% if share.share_type == 'whole_diary' %}selected{% endif %}>📚 Entire Diary</option>"""

bad_opt_2 = """                                                <option value="whole_events" {% if share.share_type=='whole_events'
                                                    %}selected{% endif %}>🗓️ All Events Calendar</option>"""
good_opt_2 = """                                                <option value="whole_events" {% if share.share_type == 'whole_events' %}selected{% endif %}>🗓️ All Events Calendar</option>"""

content = content.replace(bad_opt_1.replace("\n", "\r\n"), good_opt_1)
content = content.replace(bad_opt_1, good_opt_1)
content = content.replace(bad_opt_2.replace("\n", "\r\n"), good_opt_2)
content = content.replace(bad_opt_2, good_opt_2)

# 2. Flatten event title
bad_title = """<span class="share-type-label">📅 Specific Event: "{{ share.event.title
                                             }}"</span>"""
good_title = """<span class="share-type-label">📅 Specific Event: "{{ share.event.title }}"</span>"""

content = content.replace(bad_title.replace("\n", "\r\n"), good_title)
content = content.replace(bad_title, good_title)

# 3. Flatten created_at date in grants table
bad_date_grants = """                                    <td style="padding: 12px 5px; color: var(--text-secondary);">{{
                                        share.created_at|date:"M d, Y" }}</td>"""
good_date_grants = """                                    <td style="padding: 12px 5px; color: var(--text-secondary);">{{ share.created_at|date:"M d, Y" }}</td>"""

content = content.replace(bad_date_grants.replace("\n", "\r\n"), good_date_grants)
content = content.replace(bad_date_grants, good_date_grants)

# 4. Flatten owner username/email in received table
bad_owner = """                                    <td style="padding: 12px 5px;">{{ share.owner.username }} ({{
                                         share.owner.email|default:share.owner.username }})</td>"""
# Let's also do spacing variants
bad_owner_2 = """                                    <td style="padding: 12px 5px;">{{ share.owner.username }} ({{
                                        share.owner.email|default:share.owner.username }})</td>"""

good_owner = """                                    <td style="padding: 12px 5px;">{{ share.owner.username }} ({{ share.owner.email|default:share.owner.username }})</td>"""

content = content.replace(bad_owner.replace("\n", "\r\n"), good_owner)
content = content.replace(bad_owner, good_owner)
content = content.replace(bad_owner_2.replace("\n", "\r\n"), good_owner)
content = content.replace(bad_owner_2, good_owner)

# 5. Flatten created_at date in received table
bad_date_received = """                                    <td style="padding: 12px 5px; color: var(--text-secondary);">{{
                                         share.created_at|date:"M d, Y" }}</td>"""
# Spacing variants
bad_date_received_2 = """                                    <td style="padding: 12px 5px; color: var(--text-secondary);">{{
                                        share.created_at|date:"M d, Y" }}</td>"""

good_date_received = """                                    <td style="padding: 12px 5px; color: var(--text-secondary);">{{ share.created_at|date:"M d, Y" }}</td>"""

content = content.replace(bad_date_received.replace("\n", "\r\n"), good_date_received)
content = content.replace(bad_date_received, good_date_received)
content = content.replace(bad_date_received_2.replace("\n", "\r\n"), good_date_received)
content = content.replace(bad_date_received_2, good_date_received)

# Write output
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Repair completed successfully!")
