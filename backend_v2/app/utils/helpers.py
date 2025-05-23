import re
from datetime import datetime, timedelta
import secrets
import string

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Hasło musi mieć co najmniej 6 znaków"
    
    # Check for at least one letter and one number
    if not re.search(r'[A-Za-z]', password):
        return False, "Hasło musi zawierać co najmniej jedną literę"
    
    if not re.search(r'\d', password):
        return False, "Hasło musi zawierać co najmniej jedną cyfrę"
    
    return True, "Hasło jest wystarczająco silne"

def generate_secure_token(length=32):
    """Generate secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def format_datetime(dt):
    """Format datetime for display"""
    if not dt:
        return None
    
    # Convert to Polish timezone if needed
    return dt.strftime('%d.%m.%Y %H:%M')

def calculate_time_ago(dt):
    """Calculate human-readable time ago"""
    if not dt:
        return None
    
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "przed chwilą"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} min temu"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} godz. temu"
    elif seconds < 2592000:  # 30 days
        days = int(seconds // 86400)
        return f"{days} dni temu"
    else:
        return format_datetime(dt)

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename

def paginate_query(query, page=1, per_page=10, max_per_page=100):
    """Helper function for pagination"""
    # Ensure per_page doesn't exceed max
    per_page = min(per_page, max_per_page)
    
    # Get total count
    total = query.count()
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get items
    items = query.offset(offset).limit(per_page).all()
    
    # Calculate pagination info
    pages = (total + per_page - 1) // per_page  # Ceiling division
    has_prev = page > 1
    has_next = page < pages
    
    return {
        'items': items,
        'total': total,
        'pages': pages,
        'page': page,
        'per_page': per_page,
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_num': page - 1 if has_prev else None,
        'next_num': page + 1 if has_next else None
    }
