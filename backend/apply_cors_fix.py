import os
import shutil

# Define file paths
app_file = 'd:/wysypisko/backend/projekt/quiz-app/backend/app.py'
fix_file = 'd:/wysypisko/backend/projekt/quiz-app/backend/app_cors_fix.py'
backup_file = 'd:/wysypisko/backend/projekt/quiz-app/backend/app.py.bak'

# Create backup of original file
shutil.copy2(app_file, backup_file)
print(f"Backup created at {backup_file}")

# Replace app.py with the fixed version
shutil.copy2(fix_file, app_file)
print(f"CORS fix applied to {app_file}")
print("Please restart your Flask server for the changes to take effect.")
