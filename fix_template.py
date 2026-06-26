import os

path = r'c:\Users\Administrator\Desktop\personal-diary-planner\templates\write_entry.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix multi-line inputs
inputs_to_fix = [
    ("{% if not entry or entry.mood=='happy'\n                        %}checked{% endif %}", "{% if not entry or entry.mood == 'happy' %}checked{% endif %}"),
    ("{% if entry.mood=='neutral'\n                        %}checked{% endif %}", "{% if entry.mood == 'neutral' %}checked{% endif %}"),
    ("{% if entry.mood=='sad' %}checked{% endif\n                        %}", "{% if entry.mood == 'sad' %}checked{% endif %}"),
    ("{% if entry.mood=='excited'\n                        %}checked{% endif %}", "{% if entry.mood == 'excited' %}checked{% endif %}"),
    ("{% if entry.mood=='stressed'\n                        %}checked{% endif %}", "{% if entry.mood == 'stressed' %}checked{% endif %}")
]

new_content = content
for old, new in inputs_to_fix:
    new_content = new_content.replace(old, new)

if new_content == content:
    print("No changes made. Patterns might not match.")
    # Debug: print a chunk of the content
    start = content.find('<div class="mood-selector">')
    if start != -1:
        print("Found mood-selector block:")
        print(content[start:start+300])
else:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("File updated successfully.")
