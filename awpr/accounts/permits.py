

from awpr.constants import PERMIT_000_NONE, PERMIT_001_READ, PERMIT_002_EDIT, \
                            PERMIT_004_AUTH1, PERMIT_008_AUTH2, PERMIT_016_AUTH3, \
                            PERMIT_032_ANALYZE, PERMIT_064_ADMIN, PERMIT_128_SYSTEM

from awpr.constants import ROLE_000_NONE, ROLE_002_STUDENT, ROLE_004_TEACHER, ROLE_008_SCHOOL, ROLE_016_COMM, ROLE_032_INSP, ROLE_064_ADMIN, ROLE_128_SYSTEM


# ============================================================================
# PERMITS PR2021-03-06
# ============================================================================

def get_permits(request, page):
    permits = {}

    if request.user:
        role = request.user.role
        if role:
            if page == 'page_school':
                permits = {}
            elif page == 'page_student':
                permits = {}
            elif page == 'page_studsubj':
                permits = {}
            elif page == 'page_grades':
                permits = get_permits_page_grades(role)
            elif page == 'page_user':
                permits = {}

    return permits

def get_permits_page_grades(role):
    permits = {}
    if role == ROLE_008_SCHOOL:
        permits = {}
    elif role == ROLE_002_STUDENT:
        permits = {}
    elif role == ROLE_004_TEACHER:
        permits = {}
    elif role == ROLE_008_SCHOOL:
        permits = {}
    elif role == ROLE_016_COMM:
        permits = {}
    elif role == ROLE_032_INSP:
        permits = {}
    elif role == ROLE_064_ADMIN:
        permits = {}
    elif role == ROLE_128_SYSTEM:
        permits = {
            'view': [PERMIT_001_READ, PERMIT_002_EDIT, PERMIT_004_AUTH1, PERMIT_008_AUTH2, PERMIT_016_AUTH3,
                         PERMIT_032_ANALYZE, PERMIT_064_ADMIN, PERMIT_128_SYSTEM],
            'edit': [PERMIT_001_READ, PERMIT_002_EDIT],
            'approve': [PERMIT_004_AUTH1, PERMIT_008_AUTH2, PERMIT_016_AUTH3],
            'submit': [PERMIT_004_AUTH1, PERMIT_008_AUTH2]
        }
    return permits