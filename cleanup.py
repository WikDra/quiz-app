# Clean up script for Quiz App
# Run this script to remove unnecessary files and apply cleanup recommendations

import os
import shutil

# Base directory where the application is located
BASE_DIR = "d:/wysypisko/backend/projekt/quiz-app"

# Files to remove
files_to_remove = [
    "fix-cookies.js",
    "debug-cookies.js", 
    "debug-cookies-browser.js",
    "auth-tester.html",
    "backend/fix_cookies.py",
    "backend/app_cors_fix.py",
    "backend/apply_cors_fix.py",
    "backend_v2/utils/debug_browser.py",
    "backend_v2/utils/debug_jwt.py",
    "backend_v2/utils/test_cookies.py"
]

# Files to replace with cleaner versions
files_to_replace = {
    "src/components/DebugAuthState.jsx": "src/components/DebugAuthState.jsx.fixed"
}

def remove_files():
    """Remove unnecessary files"""
    for file_path in files_to_remove:
        full_path = os.path.join(BASE_DIR, file_path)
        if os.path.exists(full_path):
            print(f"Removing: {full_path}")
            os.remove(full_path)
        else:
            print(f"File not found: {full_path}")

def replace_files():
    """Replace files with cleaner versions"""
    for old_file, new_file in files_to_replace.items():
        old_path = os.path.join(BASE_DIR, old_file)
        new_path = os.path.join(BASE_DIR, new_file)
        
        if os.path.exists(new_path):
            print(f"Replacing {old_path} with {new_path}")
            # Create backup of the original file
            if os.path.exists(old_path):
                shutil.copy2(old_path, f"{old_path}.bak")
            # Replace with new version
            shutil.copy2(new_path, old_path)
            # Remove the temporary new file
            os.remove(new_path)
        else:
            print(f"Replacement file not found: {new_path}")

if __name__ == "__main__":
    print("Starting cleanup...")
    remove_files()
    replace_files()
    print("Cleanup completed!")
    
    # Check if the files exist after cleanup
    errors = False
    for old_file in files_to_replace:
        full_path = os.path.join(BASE_DIR, old_file)
        if not os.path.exists(full_path):
            print(f"ERROR: {full_path} does not exist after replacement!")
            errors = True
    
    if errors:
        print("\nWARNING: There were errors during cleanup. Check the output above.")
    else:
        print("\nAll files successfully processed.")
    
    print("\nNext steps:")
    print("1. Review the CLEANUP.md and CLEANUP_API_ROUTES.md files for more recommendations")
    print("2. Consider splitting the routes.py file into separate modules")
    print("3. Update the README.md with proper setup instructions")
    print("4. Further reduce debug logging in production builds")
