#PR2018-05-25
# from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as _

USERNAME_MAX_LENGTH = 30

# PR2018-05-07
ROLE_00_SCHOOL = 0
ROLE_01_INSP = 1
ROLE_02_SYSTEM = 2

# PR2018-12-23 used in set_menu_items
ROLE_STR_00_SCHOOL = 'school'
ROLE_STR_01_INSP = 'insp'
ROLE_STR_02_SYSTEM = 'system'

ROLE_DICT = {
    ROLE_00_SCHOOL: ROLE_STR_00_SCHOOL,
    ROLE_01_INSP: ROLE_STR_01_INSP,
    ROLE_02_SYSTEM: ROLE_STR_02_SYSTEM
    }

# PR2018-05-21
PERMIT_00_NONE = 0
PERMIT_01_READ = 1
PERMIT_02_WRITE = 2
PERMIT_04_AUTH = 4
PERMIT_08_ADMIN = 8

# PR2018-12-23 used in set_menu_items
PERMIT_STR_00_NONE = 'none'
PERMIT_STR_01_READ = 'read'
PERMIT_STR_02_WRITE = 'write'
PERMIT_STR_04_AUTH = 'auth'
PERMIT_STR_08_ADMIN = 'admin'
PERMIT_STR_15_ALL = 'all'

PERMIT_DICT = {
    PERMIT_00_NONE: PERMIT_STR_00_NONE,
    PERMIT_01_READ: PERMIT_STR_01_READ,
    PERMIT_02_WRITE: PERMIT_STR_02_WRITE,
    PERMIT_04_AUTH: PERMIT_STR_04_AUTH,
    PERMIT_08_ADMIN: PERMIT_STR_08_ADMIN
}


GENDER_NONE = '-'  # PR2018-09-05
GENDER_MALE = 'M'
GENDER_FEMALE = 'V'


# PR2018-09-05
GENDER_CHOICES = (
    (GENDER_NONE, '-'),
    (GENDER_MALE, _('M')),
    (GENDER_FEMALE, _('V')),
)


GRADETYPE_00_NONE = 0
GRADETYPE_01_NUMBER = 1
GRADETYPE_02_CHARACTER = 2 # goed / voldoende / onvoldoende





# PR2018-08-01
CHOICES_ROLE = (
    (ROLE_00_SCHOOL, _('School')),
    (ROLE_01_INSP, _('Inspection')),
    (ROLE_02_SYSTEM, _('System'))
)

# PR2018-08-07
CHOICES_ROLE_DICT = {
    ROLE_00_SCHOOL: _('School'),
    ROLE_01_INSP: _('Inspection'),
    ROLE_02_SYSTEM: _('System')
}

MODE_DICT = {
    'c': _('Created'),
    'u': _('Updated'),
    'a': _('Authorized'),
    'p': _('Approved'),
    'd': _('Deleted'),
    's': _('System')
}

def get_mode_str(self): # PR2018-11-20
    mode_str = '-'
    if self.mode is not None:
        mode_str = MODE_DICT.get(str(self.mode))
    return mode_str


# choises must be tuple or list, dictionary gives error: 'int' object is not iterable
CHOICES_NO_YES = (
    (False, _('No')),
    (True, _('Yes'))
)

# choises must be tuple or list, dictionary gives error: 'int' object is not iterable
CHOICES_NO_YES_DICT = {
    0: _('No'),
    1: _('Yes')
}
# choises must be tuple or list, dictionary gives error: 'int' object is not iterable
YES_NO_INT_TUPLE = (
    (1, _('Yes')),
    (0, _('No'))
)

YES_NO_DICT = {
    0: _('No'),
    1: _('Yes')
}

YES_NO_BOOL_DICT = {
    0: _('No'),
    1: _('Yes')
}



# choises must be tuple or list, dictionary gives error: 'int' object is not iterable
CHOICES_LOCKED = (
    (0, _('Unlocked')),
    (1, _('Locked'))
)
LOCKED_DICT = {
    0: _('Unlocked'),
    1: _('Locked')
}

IS_ACTIVE_DICT = {
    0: _('Inactive'),
    1: _('Active')
}
# choises must be tuple or list, dictionary gives error: 'int' object is not iterable
IS_ACTIVE_CHOICES = (
    (0, _('Inactive')),
    (1, _('Active'))
)

INACTIVE_DICT = {
    0: _('Active'),
    1: _('Inactive')
}

# PR2018-07-19 choises must be tuple or list, dictionary gives error: 'int' object is not iterable
INACTIVE_CHOICES = (
    (0, _('Active')),
    (1, _('Inactive'))
)

# PR2018-10-15
IS_TEMPLATE_DICT = {
    0: _('Not a template'),
    1: _('Template')
}
# PR2018-10-15  choises must be tuple or list, dictionary gives error: 'int' object is not iterable
IS_TEMPLATE_CHOICES = (
    (0, _('Not a template')),
    (1, _('Template'))
)



# PR2018-07-31 choise 0 = 'None' for empty choice
CHOICE_NONE = (0, _('None'))

# PR2018-08-04 for Examyear.publishes
PUBLISHED_CHOICES = (
    (0, _('Not published')),
    (1, _('Published'))
)
PUBLISHED_DICT = {
    0: _('Not published'),
    1: _('Published')
}

GRADETYPE_CHOICES = (
    (GRADETYPE_00_NONE, _('None')),
    (GRADETYPE_01_NUMBER, _('Number')),
    (GRADETYPE_02_CHARACTER, _('Good/Sufficient/Insufficient'))
)

# PR2018-11-11
GRADETYPE_ABBREV = {
    GRADETYPE_00_NONE: _('-'),
    GRADETYPE_01_NUMBER: _('nr.'),
    GRADETYPE_02_CHARACTER: _('g/s/i')
}




# PR2019-01-19
SCHEMEFIELD_MANDATORY = 'mand'
SCHEMEFIELD_COMBI = 'comb'
SCHEMEFIELD_CHOICECOMBI_ALLOWED = 'chal'
SCHEMEFIELD_PRACTEXAM = 'prac'

SCHEMEFIELD_CHOICES = (
    (SCHEMEFIELD_MANDATORY, _('Mandatory')),
    (SCHEMEFIELD_COMBI, _('Combination subject')),
    (SCHEMEFIELD_CHOICECOMBI_ALLOWED, _('Choice combi allowed')),
    (SCHEMEFIELD_PRACTEXAM, _('Practical exam')),
)

# translation not working in dict, error: 'must be str, not __proxy__' Solved by using 'ugettext' instead of 'ugettext_lazy'
SCHEMEFIELD_DICT = {
    SCHEMEFIELD_MANDATORY: _('Mandatory'),
    SCHEMEFIELD_COMBI: _('Combi subject'),
    SCHEMEFIELD_CHOICECOMBI_ALLOWED: _('Choice combi'),
    SCHEMEFIELD_PRACTEXAM: _('Practical exam')
}


# PR2019-02-15
# se, pe ce, ce2, ce3, end
SCHOOLEXAM = 1
PRACTICALEXAM = 2
CENTRALEXAM = 3
CENTRALEXAM2 = 4
CENTRALEXAM3 = 5
SCHOOLEXAM_EXEMPTION = 6
CENTRALEXAM_EXEMPTION = 7

EXAMCODE_CHOICES = (
    (SCHOOLEXAM, _('School exam')),
    (PRACTICALEXAM, _('Practical exam')),
    (CENTRALEXAM, _('Central exam')),
    (CENTRALEXAM2, _('Re-examination')),
    (CENTRALEXAM3, _('Re-examination third period')),
    (SCHOOLEXAM_EXEMPTION, _('School exam exemption')),
    (CENTRALEXAM_EXEMPTION, _('Central exam exemption'))
)

# PR2019-02-15
SCORE = 1
GRADE = 2
PECE = 3
FINAL = 4

GRADECODE_CHOICES = (
    (SCORE, _('Score')),
    (GRADE, _('Grade')),
    (PECE, _('CE-PE')),
    (FINAL, _('Final grade'))
)

# PR2019-02-15
PERIOD_1 = 1
PERIOD_2 = 2
PERIOD_3 = 2

PERIOD_CHOICES = (
    (PERIOD_1, _('Period 1')),
    (PERIOD_2, _('Period 2')),
    (PERIOD_3, _('Period 3'))
)

# PR2018-11-28
# se, pe ce, ce2, ce3, end
NORESULT_RESULT = 0
PASSED_RESULT = 1
FAILED_RESULT = 2
WITHDRAWN_RESULT = 3

RESULT_CHOICES = (
    (NORESULT_RESULT, _('No result')),
    (PASSED_RESULT, _('Passed')),
    (FAILED_RESULT, _('Failed')),
    (WITHDRAWN_RESULT, _('Withdrawn'))
)

# SCHOOL SETTING KEYS PR2018-12-03
KEY_STUDENT_MAPPED_COLDEFS = "student_mapped_coldefs"

# USER SETTING KEYS PR2018-12-19
KEY_USER_MENU_SELECTED = "menu_selected"