# PR2018-05-25 PR2020-12-04
# from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as _

USERNAME_MAX_LENGTH = 30
USERNAME_SLICED_MAX_LENGTH = 24
USER_LASTNAME_MAX_LENGTH = 50
MAX_LENGTH_KEY = 24  # number is also hardcoded in _()
MAX_LENGTH_NAME = 50
MAX_LENGTH_SCHOOLCODE = 8
MAX_LENGTH_SCHOOLABBREV = 30
MAX_LENGTH_SCHOOLARTICLE = 3
MAX_LENGTH_FIRSTLASTNAME = 80
MAX_LENGTH_IDNUMBER = 14
MAX_LENGTH_EXAMNUMBER = 20
MAX_LENGTH_20 = 20
MAX_LENGTH_12 = 12
MAX_LENGTH_10 = 10
MAX_LENGTH_04 = 4
MAX_LENGTH_01 = 1

MAX_LEN_DICT_STUDENT = {
    'lastname': MAX_LENGTH_FIRSTLASTNAME,
    'firstname': MAX_LENGTH_FIRSTLASTNAME,
    'prefix': MAX_LENGTH_10,
    'gender': MAX_LENGTH_01,
    'idnumber': MAX_LENGTH_IDNUMBER,
    'birthcountry': USER_LASTNAME_MAX_LENGTH,
    'birthcity': USER_LASTNAME_MAX_LENGTH,
    'classname': MAX_LENGTH_EXAMNUMBER,
    'examnumber': MAX_LENGTH_EXAMNUMBER,
    'regnumber': MAX_LENGTH_EXAMNUMBER,
    'diplomanumber': MAX_LENGTH_10,
    'gradelistnumber': MAX_LENGTH_10
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

MODE_C_CREATED = 'c'
MODE_L_COPIED = 'l'
MODE_U_UPDATED = 'u'
MODE_A_AUTHORIZED = 'a'
MODE_P_APPROVED = 'p'
MODE_D_DELETED = 'd'
MODE_S_SYSTEM = 's'

MODE_DICT = {
    MODE_C_CREATED: _('Created'),
    MODE_L_COPIED: _('Copied from last year'),
    MODE_U_UPDATED: _('Updated'),
    MODE_A_AUTHORIZED: _('Authorized'),
    MODE_P_APPROVED: _('Approved'),
    MODE_D_DELETED: _('Deleted'),
    MODE_S_SYSTEM: _('System')
}


def get_mode_str(self):  # PR2018-11-20
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



GRADETYPE_00_NONE = 0
GRADETYPE_01_NUMBER = 1
GRADETYPE_02_CHARACTER = 2  # goed / voldoende / onvoldoende

GRADETYPE_OPTIONS = {
    GRADETYPE_00_NONE:  _('None'),
    GRADETYPE_01_NUMBER: _('Number'),
    GRADETYPE_02_CHARACTER: _('Good/Sufficient/Insufficient')
}

# PR2018-11-11
GRADETYPE_ABBREVS = {
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

# translation not working in dict, error: 'must be str, not __proxy__'
# Solved by using 'ugettext' instead of 'ugettext_lazy'


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

# PR2019-02-15 PR2020-12-14
EXAMPERIOD_FIRST = 1
EXAMPERIOD_SECOND = 2
EXAMPERIOD_THIRD = 3
EXAMPERIOD_EXEMPTION = 4

EXAMPERIOD_CAPTION = {
    EXAMPERIOD_FIRST: _('First exam period'),
    EXAMPERIOD_SECOND: _('Second exam period'),
    EXAMPERIOD_THIRD: _('Third exam period'),
    EXAMPERIOD_EXEMPTION: _('Exemption')
}
EXAMPERIOD_OPTIONS = [{'value': EXAMPERIOD_FIRST, 'caption': _('First exam period')},
                        {'value': EXAMPERIOD_SECOND, 'caption': _('Second exam period')},
                        {'value': EXAMPERIOD_THIRD, 'caption': _('Third exam period')},
                        {'value': EXAMPERIOD_EXEMPTION, 'caption': _('Exemption')}]


def get_examperiod_caption(examperiod_int):
    return EXAMPERIOD_CAPTION.get(examperiod_int, '')


# options_examtype value = ecamtype, filter = examperiod PR2020-12-17
EXAMTYPE_OPTIONS = [
    {'value': 'se', 'filter': EXAMPERIOD_FIRST, 'caption': _('School exam')},
    {'value': 'pe', 'filter': EXAMPERIOD_FIRST, 'caption': _('Practical exam')},
    {'value': 'ce', 'filter': EXAMPERIOD_FIRST, 'caption': _('Central exam')},
    {'value': 're2', 'filter': EXAMPERIOD_SECOND, 'caption': _('Re-examination')},
        {'value': 're3', 'filter': EXAMPERIOD_THIRD, 'caption': _('Re-examination 3rd period')},
    {'value': 'exm', 'filter': EXAMPERIOD_EXEMPTION, 'caption': _('School- / Central exam')}
    ]

EXAMTYPE_CAPTION = {
    'se': _('School exam'),
    'pe': _('Practical exam'),
    'ce': _('Central exam'),
    're2': _('Re-examination'),
    're3': _('Re-examination 3rd period'),
    'exm': _('Exemption')
}


def get_examtype_caption(examtype_str):
    return EXAMTYPE_CAPTION.get(examtype_str, '')

# PR2018-11-28
# se, pe ce, ce2, ce3, end
NORESULT_RESULT = 0
PASSED_RESULT = 1
FAILED_RESULT = 2
REEXAM_RESULT = 3
WITHDRAWN_RESULT = 4

RESULT_CHOICES = (
    (NORESULT_RESULT, _('No result')),
    (PASSED_RESULT, _('Passed')),
    (FAILED_RESULT, _('Failed')),
    (REEXAM_RESULT, _('Re-examination')),
    (WITHDRAWN_RESULT, _('Withdrawn'))
)

STATUS_NONE = 0
STATUS_00_CREATED = 1
STATUS_01_AUTH1 = 2
STATUS_02_AUTH2 = 4
STATUS_03_AUTH3 = 8
STATUS_04_SUBMITTED = 16
STATUS_05_REQUEST = 32
STATUS_06_WARNING = 64
STATUS_07_REJECTED = 128
STATUS_08_REQUEST_ANSWERED = 256
STATUS_09_WARNING_ANSWERED = 512
STATUS_10_REJECTED_ANSWERED = 1024
STATUS_11_EDIT = 2048
STATUS_12_EDIT_ANSWERED = 4096
STATUS_13_APPROVED = 8192
STATUS_14_LOCKED = 16384

"""
# PR2021-01-014 from https://stackoverflow.com/questions/509211/understanding-slice-notation
# list[start:stop:step] # start through not past stop, by step
#status_str = bin(status_int)[-1:1:-1]  # status 31 becomes '11111', first char is STATUS_001_CREATED

from https://www.postgresql.org/message-id/20040611075402.GA4887@computing-services.oxford.ac.uk
area=> select 6::bit(32);
>                bit
> ----------------------------------
>  00000000000000000000000000000110
> (1 row)
"""


# USER SETTING KEYS PR2018-12-19 PR2020-12-18
KEY_MENU_SELECTED = "menu_selected"
KEY_SELECTED_PK = 'selected_pk'
KEY_SEL_EXAMYEAR_PK = 'sel_examyear_pk'
KEY_SEL_SCHOOLBASE_PK = 'sel_schoolbase_pk'
KEY_SEL_DEPBASE_PK = 'sel_depbase_pk'
KEY_SEL_EXAMPERIOD = 'sel_examperiod'
KEY_SEL_EXAMTYPE = 'sel_examtype'
KEY_SEL_SUBJECT_PK = 'sel_subject_pk'
KEY_SEL_STUDENT_PK = 'sel_student_pk'
KEY_SEL_LEVEL_PK = 'sel_level_pk'
KEY_SEL_SECTOR_PK = 'sel_sector_pk'

# SCHOOL SETTING KEYS PR2018-12-03  PR2020-12-04

KEY_IMPORT_SUBJECT = 'import_subject'
KEY_IMPORT_STUDENT = 'import_student'
KEY_IMPORT_STUDENTSUBJECT = 'import_studentsubject'
KEY_IMPORT_GRADE = 'import_grade'

KEY_COLDEF = {
    KEY_IMPORT_SUBJECT:
        ({'awpColdef': 'code', 'caption': _('Subject abbreviation'), 'linkfield': True},
          {'awpColdef': 'name', 'caption': _('Subject name')},
          {'awpColdef': 'sequence', 'caption': _('Sequence')},
          {'awpColdef': 'depbases', 'caption': _('Departments, in which this subject occurs')}),

    KEY_IMPORT_STUDENTSUBJECT:
        ({'awpColdef': 'examnumber', 'caption': _('Exam number'), 'linkfield': True},
            {'awpColdef': 'idnumber', 'caption': _('ID-number'), 'linkfield': True},
            {'awpColdef': 'pws_title', 'caption': _('Title assignment')},
            {'awpColdef': 'pws_subjects', 'caption': _('Subjects assignment')},

            # to be used for tabular upload :
            {'awpColdef': 'subject', 'caption': _('Subject'), 'tabularfield': True},
            {'awpColdef': 'subjecttype', 'caption': _('Character'), 'tabularfield': True}
         ),

    KEY_IMPORT_STUDENT:
        ({'awpColdef': 'lastname', 'caption': _('Last name')},
        {'awpColdef': 'firstname', 'caption': _('First name')},
        {'awpColdef': 'prefix', 'caption': _('Prefix')},
        {'awpColdef': 'gender', 'caption': _('Gender')},
        {'awpColdef': 'examnumber', 'caption': _('Exam number'), 'linkfield': True},
        {'awpColdef': 'idnumber', 'caption': _('ID-number'), 'linkfield': True},
        {'awpColdef': 'birthdate', 'caption': _('Birthdate'), 'datefield': True},
        {'awpColdef': 'birthcountry', 'caption': _('Country of birth')},
        {'awpColdef': 'birthcity', 'caption': _('Place of birth')},
        {'awpColdef': 'classname', 'caption': _('Class name')},
        #{'awpColdef': 'iseveningstudent', 'caption': _('Evening student')},
        #{'awpColdef': 'hasdyslexia', 'caption': _('Has dyslexia')},
        {'awpColdef': 'bis_exam', 'caption': _('Bis exam')},
        {'awpColdef': 'department', 'caption': _('Department')},

        {'awpColdef': 'level', 'caption': _('Level')},
        {'awpColdef': 'sector', 'caption': _('Sector')},
        {'awpColdef': 'profiel', 'caption': _('Profiel')})
    }

CAPTIONS = {'student': {'lastname': _('Last name'),
                        'firstname': _('First name'),
                        'prefix': _('Prefix'),
                        'gender': _('Gender'),
                        'examnumber': _('Exam number'),
                        'idnumber': _('ID-number'),
                        'birthdate': _('Birthdate'),
                        'birthcountry': _('Country of birth'),
                        'birthcity': _('Place of birth'),
                        'classname': _('Class name'),
                        'iseveningstudent': _('Evening student'),
                        'hasdyslexia': _('Has dyslexia'),
                        'bis_exam': _('Bis exam'),
                        'department': _('Department'),
                        'level': _('Level'),
                        'sector': _('Sector'),
                        'profiel': _('Profiel')}
            }

CAPTION_IMPORT = {'no_file': _('No file is currently selected'),
                  'link_columns': _('Link columns'),
                  'click_items': _('Click items to link or unlink columns'),
                  'excel_columns': _('Excel columns'),
                  'awp_columns': _('AWP columns'),
                  'linked_columns': _('Linked columns')}

LANG_DEFAULT = 'nl'

MONTH_START_EXAMYEAR = 8  # PR2020-11-17
# PR2019-03-23
MONTHS_ABBREV = {'en': ('', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'),
                 'nl': ('', 'jan', 'feb', 'mrt', 'apr', 'mei', 'juni', 'juli', 'aug', 'sep', 'okt', 'nov', 'dec')}
MONTHS_LONG = {'en': ('', 'January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December'),
               'nl': ('', 'januari', 'februari', 'maart', 'april', 'mei', 'juni',
                      'juli', 'augustus', 'september', 'oktober', 'november', 'december')}
# PR2019-04-13
WEEKDAYS_ABBREV = {'en': ('', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'),
                   'nl': ('', 'ma', 'di', 'wo', 'do', 'vr', 'za', 'zo')}
WEEKDAYS_LONG = {'en': ('', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
                 'nl': ('', 'maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag')}

# PR2020-10-06
FIELDS_EXAMYEAR = ('country', 'examyear', 'published', 'locked',
                   'createdat', 'publishedat', 'lockedat', 'modifiedby', 'modifiedat')
FIELDS_SCHOOL = ('base', 'examyear', 'name', 'abbrev', 'article', 'depbases',
                 'isdayschool', 'iseveningschool', 'islexschool',
                 'activated', 'locked', 'activatedat', 'lockedat', 'modifiedby', 'modifiedat')

FIELDS_SUBJECT = ('base', 'examyear', 'name', 'abbrev', 'sequence', 'depbases', 'modifiedby', 'modifiedat')
FIELDS_STUDENT = ('base', 'school', 'department', 'level', 'sector', 'scheme', 'package',
                  'lastname', 'firstname', 'prefix', 'gender', 'idnumber', 'birthdate', 'birthcountry', 'birthcity',
                  'classname', 'examnumber', 'regnumber', 'diplomanumber', 'gradelistnumber',
                  'iseveningstudent', 'hasdyslexia',
                  'locked', 'has_reex', 'bis_exam', 'withdrawn', 'modifiedby', 'modifiedat')
FIELDS_STUDENTSUBJECT = ('student', 'schemeitem', 'cluster', 'is_extra_nocount', 'is_extra_counts', 'is_elective_combi',
                'pws_title', 'pws_subjects', 'has_exemption', 'has_reex', 'has_reex03', 'has_pok',
               'subj_auth1by', 'subj_auth2by', 'subj_published',
               'exem_auth1by', 'exem_auth2by', 'exem_published',
               'reex_auth1by', 'reex_auth2by', 'reex_published',
               'reex3_auth1by', 'reex3_auth2by', 'reex3_published',
               'pok_auth1by', 'pok_auth2by', 'pok_published',
               'deleted', 'modifiedby', 'modifiedat')
FIELDS_GRADE =('studentsubject', 'examperiod', 'pescore', 'cescore',
               'segrade', 'pegrade', 'cegrade', 'pecegrade', 'finalgrade',
               'se_auth1by', 'se_auth2by', 'se_published',
               'pe_auth1by', 'pe_auth2by', 'pe_published',
               'ce_auth1by', 'ce_auth2by', 'ce_published',
               'deleted', 'status', 'modifiedby', 'modifiedat')


STRING_SPACE_30 = ' ' * 30
STRING_SPACE_10 = ' ' * 10
STRING_INDENT_5 = ' ' * 5
STRING_DOUBLELINE_80 = '=' * 80


# ============================================================================
# ROLES AND PERMITS PR2021-02-23
# ============================================================================

# PR2018-05-07
#ROLE_000_NONE = 0
#ROLE_002_STUDENT = 2
#ROLE_004_TEACHER = 4
ROLE_008_SCHOOL = 8
ROLE_016_COMM = 16
ROLE_032_INSP = 32
ROLE_064_ADMIN = 64
ROLE_128_SYSTEM = 128

# PR2018-12-23 used in set_menu_items
ROLE_DICT = {
    ROLE_008_SCHOOL: 'school',
    ROLE_016_COMM: 'comm',
    ROLE_032_INSP: 'insp',
    ROLE_064_ADMIN: 'admin',
    ROLE_128_SYSTEM: 'system'
    }
ROLE_CAPTION = {
    ROLE_008_SCHOOL: _('School'),
    ROLE_016_COMM: _('Commissioner'),
    ROLE_032_INSP: _('Inspection'),
    ROLE_064_ADMIN: _('Division of Examinations'),
    ROLE_128_SYSTEM: _('System manager')
    }


# PR2018-05-21
GROUP_000_NONE = 0
GROUP_001_READ = 1
GROUP_002_EDIT = 2
GROUP_004_AUTH1 = 4
GROUP_008_AUTH2 = 8
GROUP_016_AUTH3 = 16
GROUP_032_ANALYZE = 32
GROUP_064_ADMIN = 64

# PR2018-12-23 used in set_menu_items

GROUP_DICT = {
    GROUP_000_NONE: 'none',
    GROUP_001_READ: 'read',
    GROUP_002_EDIT: 'edit',
    GROUP_004_AUTH1: 'auth1',
    GROUP_008_AUTH2: 'auth2',
    GROUP_016_AUTH3: 'auth3',
    GROUP_032_ANALYZE: 'anlz',
    GROUP_064_ADMIN: 'admin'
}
GROUP_CAPTION = {
    GROUP_001_READ: _('Read'),
    GROUP_002_EDIT: _('Edit'),
    GROUP_004_AUTH1: _('President'),
    GROUP_008_AUTH2: _('Secretary'),
    GROUP_016_AUTH3: _('Commissioner'),
    GROUP_032_ANALYZE: _('Analyze'),
    GROUP_064_ADMIN: _('Administrator')
}

GROUP_LOOKUP = {
    'perm_none': GROUP_000_NONE,
    'perm_read': GROUP_001_READ,
    'perm_edit': GROUP_002_EDIT,
    'perm_auth1': GROUP_004_AUTH1,
    'perm_auth2': GROUP_008_AUTH2,
    'perm_auth3': GROUP_016_AUTH3,
    'perm_anlz': GROUP_032_ANALYZE,
    'perm_admin': GROUP_064_ADMIN

}

GROUP_INDEX_LOOKUP = {
    'perm_read': 0,
    'perm_edit': 1,
    'perm_auth1': 2,
    'perm_auth2': 3,
    'perm_auth3': 4,
    'perm_anlz': 5,
    #'perm_admin': 6,
    'perm_system': 7
}

PAGE_LIST = {
    'users': _('Users'),
    'examyears': _('Exam years'),
    'subjects': _('Subjects'),
    'schools': _('Schools'),
    'students': _('Students'),
    'studentsubjects': _('Subjects of students'),
    'grades': _('Grades')
}

DEFAULT_PERMITS = [
    {'role': 8, 'page': 'page_all', 'sequence': 10, 'action': 'view_users', 'usergroups': 'admin'},
    {'role': 8, 'page': 'page_examyear', 'sequence': 10, 'action': 'view_page', 'usergroups': None},
    {'role': 8, 'page': 'page_grade', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 8, 'page': 'page_grade', 'sequence': 20, 'action': 'edit_grade', 'usergroups': 'edit'},
    {'role': 8, 'page': 'page_grade', 'sequence': 30, 'action': 'approve_grade', 'usergroups': 'auth1;auth2'},
    {'role': 8, 'page': 'page_grade', 'sequence': 40, 'action': 'submit_grade', 'usergroups': 'auth1;auth2'},
    {'role': 8, 'page': 'page_grade', 'sequence': 50, 'action': 'unlock_grade', 'usergroups': None},
    {'role': 8, 'page': 'page_grade', 'sequence': 60, 'action': 'read_note', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 8, 'page': 'page_grade', 'sequence': 70, 'action': 'write_note_intern', 'usergroups': 'auth1;auth2;auth3;edit'},
    {'role': 8, 'page': 'page_grade', 'sequence': 80, 'action': 'write_note_extern', 'usergroups': 'auth1;auth2'},
    {'role': 8, 'page': 'page_school', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 8, 'page': 'page_student', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 8, 'page': 'page_studsubj', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 8, 'page': 'page_subject', 'sequence': 10, 'action': 'view_page', 'usergroups': None},
    {'role': 16, 'page': 'page_all', 'sequence': 10, 'action': 'view_users', 'usergroups': 'admin'},
    {'role': 16, 'page': 'page_examyear', 'sequence': 10, 'action': 'view_page', 'usergroups': None},
    {'role': 16, 'page': 'page_grade', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 16, 'page': 'page_grade', 'sequence': 20, 'action': 'edit_grade', 'usergroups': ''},
    {'role': 16, 'page': 'page_grade', 'sequence': 30, 'action': 'approve_grade', 'usergroups': 'auth3'},
    {'role': 16, 'page': 'page_grade', 'sequence': 40, 'action': 'submit_grade', 'usergroups': None},
    {'role': 16, 'page': 'page_grade', 'sequence': 50, 'action': 'unlock_grade', 'usergroups': None},
    {'role': 16, 'page': 'page_grade', 'sequence': 60, 'action': 'read_note', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 16, 'page': 'page_grade', 'sequence': 70, 'action': 'write_note_intern', 'usergroups': 'auth3'},
    {'role': 16, 'page': 'page_grade', 'sequence': 80, 'action': 'write_note_extern', 'usergroups': 'auth3'},
    {'role': 16, 'page': 'page_school', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 16, 'page': 'page_student', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 16, 'page': 'page_studsubj', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 16, 'page': 'page_subject', 'sequence': 10, 'action': 'view_page', 'usergroups': None},
    {'role': 32, 'page': 'page_all', 'sequence': 10, 'action': 'view_users', 'usergroups': 'admin'},
    {'role': 32, 'page': 'page_examyear', 'sequence': 10, 'action': 'view_page', 'usergroups': None},
    {'role': 32, 'page': 'page_grade', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 32, 'page': 'page_grade', 'sequence': 20, 'action': 'edit_grade', 'usergroups': ''},
    {'role': 32, 'page': 'page_grade', 'sequence': 30, 'action': 'approve_grade', 'usergroups': ''},
    {'role': 32, 'page': 'page_grade', 'sequence': 40, 'action': 'submit_grade', 'usergroups': None},
    {'role': 32, 'page': 'page_grade', 'sequence': 50, 'action': 'unlock_grade', 'usergroups': 'edit'},
    {'role': 32, 'page': 'page_grade', 'sequence': 60, 'action': 'read_note', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 32, 'page': 'page_grade', 'sequence': 70, 'action': 'write_note_intern', 'usergroups': 'auth1;auth2;auth3;edit'},
    {'role': 32, 'page': 'page_grade', 'sequence': 80, 'action': 'write_note_extern', 'usergroups': 'auth1;auth2'},
    {'role': 32, 'page': 'page_school', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 32, 'page': 'page_student', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 32, 'page': 'page_studsubj', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 32, 'page': 'page_subject', 'sequence': 10, 'action': 'view_page', 'usergroups': None},
    {'role': 64, 'page': 'page_all', 'sequence': 10, 'action': 'view_users', 'usergroups': 'admin'},
    {'role': 64, 'page': 'page_examyear', 'sequence': 10, 'action': 'view_page', 'usergroups': None},
    {'role': 64, 'page': 'page_grade', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 64, 'page': 'page_grade', 'sequence': 20, 'action': 'edit_grade', 'usergroups': ''},
    {'role': 64, 'page': 'page_grade', 'sequence': 30, 'action': 'approve_grade', 'usergroups': None},
    {'role': 64, 'page': 'page_grade', 'sequence': 40, 'action': 'submit_grade', 'usergroups': None},
    {'role': 64, 'page': 'page_grade', 'sequence': 50, 'action': 'unlock_grade', 'usergroups': None},
    {'role': 64, 'page': 'page_grade', 'sequence': 60, 'action': 'read_note', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 64, 'page': 'page_grade', 'sequence': 70, 'action': 'write_note_intern', 'usergroups': 'auth1;auth2;auth3;edit'},
    {'role': 64, 'page': 'page_grade', 'sequence': 80, 'action': 'write_note_extern', 'usergroups': 'auth1;auth2'},
    {'role': 64, 'page': 'page_school', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 64, 'page': 'page_student', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 64, 'page': 'page_studsubj', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 64, 'page': 'page_subject', 'sequence': 10, 'action': 'view_page', 'usergroups': None},
    {'role': 128, 'page': 'page_all', 'sequence': 10, 'action': 'view_users', 'usergroups': 'admin'},
    {'role': 128, 'page': 'page_examyear', 'sequence': 10, 'action': 'view_page', 'usergroups': None},
    {'role': 128, 'page': 'page_grade', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 128, 'page': 'page_grade', 'sequence': 20, 'action': 'edit_grade', 'usergroups': 'edit'},
    {'role': 128, 'page': 'page_grade', 'sequence': 30, 'action': 'approve_grade', 'usergroups': 'auth1;auth2;auth3'},
    {'role': 128, 'page': 'page_grade', 'sequence': 40, 'action': 'submit_grade', 'usergroups': 'auth1;auth2'},
    {'role': 128, 'page': 'page_grade', 'sequence': 50, 'action': 'unlock_grade', 'usergroups': None},
    {'role': 128, 'page': 'page_grade', 'sequence': 60, 'action': 'read_note', 'usergroups': 'anlz;auth1;auth2;auth3;edit;read'},
    {'role': 128, 'page': 'page_grade', 'sequence': 70, 'action': 'write_note_intern', 'usergroups': 'auth1;auth2;auth3;edit'},
    {'role': 128, 'page': 'page_grade', 'sequence': 80, 'action': 'write_note_extern', 'usergroups': 'auth1;auth2'},
    {'role': 128, 'page': 'page_school', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 128, 'page': 'page_student', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 128, 'page': 'page_studsubj', 'sequence': 10, 'action': 'view_page', 'usergroups': 'admin;anlz;auth1;auth2;auth3;edit;read'},
    {'role': 128, 'page': 'page_subject', 'sequence': 10, 'action': 'view_page', 'usergroups': None}
]

