# Clean up script for Quiz App
# Run this script to remove unnecessary files and apply cleanup recommendations

import os
import shutil

# Base directory where the application is located
BASE_DIR = "d:/wysypisko/backend/projekt/quiz-app"

# Files to remove
files_to_remove = [
    # Dotychczasowe pliki
    "fix-cookies.js",
    "debug-cookies.js", 
    "debug-cookies-browser.js",
    "auth-tester.html",
    "backend/fix_cookies.py",
    "backend/app_cors_fix.py",
    "backend/apply_cors_fix.py",
    "backend_v2/utils/debug_browser.py",
    "backend_v2/utils/debug_jwt.py",
    "backend_v2/utils/test_cookies.py",
    
    # Dodatkowe pliki związane z plikami cookie i debugowaniem
    "check-cookies.js",
    "cookie-diagnostics.html",
    "cookie-diagnostics.js",
    "browser-cookie-test.html",
    "simple-cookie-test.html",
    "test-cookies.html",
    
    # Pliki z dokumentacją sprzątania, które stają się zbędne po wykonaniu
    "CLEANUP.md",
    "CLEANUP_API_ROUTES.md",
    
    # Pliki zapasowe i tymczasowe
    "backend/__init__.py.bak",
    "backend/app.py.bak",
    "src/components/DebugAuthState.jsx.bak",
    "src/components/DebugAuthState.jsx.new"
]

# Function to remove backup files
def remove_backup_files():
    """Find and remove all .bak, .old, .temp files"""
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(('.bak', '.old', '.temp')):
                full_path = os.path.join(root, file)
                print(f"Removing backup file: {full_path}")
                os.remove(full_path)

def remove_files():
    """Remove unnecessary files"""
    for file_path in files_to_remove:
        full_path = os.path.join(BASE_DIR, file_path)
        if os.path.exists(full_path):
            print(f"Removing: {full_path}")
            os.remove(full_path)
        else:
            print(f"File not found: {full_path}")

if __name__ == "__main__":
    print("Starting cleanup...")
    remove_files()
    remove_backup_files()
    print("Cleanup completed!")
    
    print("\nAll files successfully processed.")
    
    print("\nNext steps:")
    print("1. Consider splitting the routes.py file into separate modules (auth_routes.py, quiz_routes.py, user_routes.py)")
    print("2. Update the README.md with proper setup instructions")
    print("3. Further reduce debug logging in production builds")
    print("4. Ensure proper security attributes for cookies in production mode (Secure, HttpOnly)")
    print("5. Add rate limiting for login/registration endpoints")
