"""
A script to directly fix the JWT cookie settings in __init__.py
"""
import os
import re

# Path to the __init__.py file
init_file_path = os.path.join(os.path.dirname(__file__), '__init__.py')

# Read the current content
with open(init_file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Create a backup
backup_path = os.path.join(os.path.dirname(__file__), '__init__.py.bak')
with open(backup_path, 'w', encoding='utf-8') as file:
    file.write(content)
print(f"Backup created at {backup_path}")

# Add JWT cookie configuration
jwt_config = """
    # Configure JWT cookie settings
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = False  # Set to True in production
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False  # Set to True in production
    app.config["JWT_COOKIE_SAMESITE"] = "None"  # Required for cross-site requests
"""

# Find the right position to insert the configuration (after JWT_REFRESH_TOKEN_EXPIRES)
pattern = r'(app\.config\["JWT_REFRESH_TOKEN_EXPIRES"\] = timedelta\(days=30\))'
if re.search(pattern, content):
    modified_content = re.sub(pattern, r'\1\n' + jwt_config, content)
    
    # Write the modified content back
    with open(init_file_path, 'w', encoding='utf-8') as file:
        file.write(modified_content)
    print("Added JWT cookie configuration to __init__.py")
else:
    print("Could not find the appropriate place to insert JWT cookie configuration")

# Add custom after_request function to ensure cookies are properly set
after_request_code = """
    # Custom after_request function to fix SameSite attribute in cookies
    @app.after_request
    def set_cookie_attributes(response):
        # Get all cookie headers
        cookie_headers = response.headers.getlist('Set-Cookie')
        new_cookie_headers = []
        
        # Process each cookie
        for header in cookie_headers:
            # Replace samesite=Lax with samesite=None
            if 'samesite=Lax' in header:
                header = header.replace('samesite=Lax', 'samesite=None')
            # Add samesite=None if not present
            elif 'samesite=' not in header:
                header = header + '; samesite=None'
            new_cookie_headers.append(header)
        
        # Clear original cookies and set the modified ones
        response.headers.pop('Set-Cookie', None)
        for header in new_cookie_headers:
            response.headers.add('Set-Cookie', header)
        
        return response
"""

# Find the right position to insert the after_request function (before return app)
pattern = r'([\s]+return app)'
if re.search(pattern, content):
    modified_content = re.sub(pattern, after_request_code + r'\n\1', modified_content if 'modified_content' in locals() else content)
    
    # Write the modified content back
    with open(init_file_path, 'w', encoding='utf-8') as file:
        file.write(modified_content)
    print("Added after_request function to __init__.py")
else:
    print("Could not find the appropriate place to insert after_request function")

print("Cookie fixes applied. Please restart your Flask server for the changes to take effect.")
