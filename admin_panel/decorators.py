from django.shortcuts import redirect
from functools import wraps

# Allow both superadmin and staff (must be logged in)
def admin_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_id'):
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper

# Only superadmin allowed
def superadmin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_id') or request.session.get('admin_role') != 'superadmin':
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
