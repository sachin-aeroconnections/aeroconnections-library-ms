# Utils package


def is_superadmin(user):
    """Permission check: returns True if the user is a superuser.
    Use with @user_passes_test(is_superadmin) on views.
    """
    return user.is_superuser
