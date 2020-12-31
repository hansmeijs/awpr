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


# PR2018-05-07
ROLE_00_NONE = 0
ROLE_02_STUDENT = 2
ROLE_04_TEACHER = 4
ROLE_08_SCHOOL = 8
ROLE_16_INSP = 16
ROLE_32_ADMIN = 32
ROLE_64_SYSTEM = 64

# PR2018-12-23 used in set_menu_items
ROLE_STR_08_SCHOOL = 'school'
ROLE_STR_16_INSP = 'insp'
ROLE_STR_32_ADMIN = 'admin'
ROLE_STR_64_SYSTEM = 'system'

ROLE_DICT = {
    ROLE_08_SCHOOL: ROLE_STR_08_SCHOOL,
    ROLE_16_INSP: ROLE_STR_16_INSP,
    ROLE_32_ADMIN: ROLE_STR_32_ADMIN,
    ROLE_64_SYSTEM: ROLE_STR_64_SYSTEM
    }

# PR2018-05-21
PERMIT_00_NONE = 0
PERMIT_01_READ = 1
PERMIT_02_EDIT = 2
PERMIT_04_AUTH1 = 4
PERMIT_08_AUTH2 = 8
PERMIT_16_ANALYZE = 16
PERMIT_32_ADMIN = 32
PERMIT_64_SYSTEM = 64

# PR2018-12-23 used in set_menu_items
PERMIT_STR_00_NONE = 'none'
PERMIT_STR_01_READ = 'read'
PERMIT_STR_02_EDIT = 'edit'
PERMIT_STR_04_AUTH1 = 'auth1'
PERMIT_STR_08_AUTH2 = 'auth2'
PERMIT_STR_16_ANALYZE = 'anlz'
PERMIT_STR_32_ADMIN = 'admin'
PERMIT_STR_64_SYSTEM = 'system'

PERMIT_DICT = {
    PERMIT_00_NONE: PERMIT_STR_00_NONE,
    PERMIT_01_READ: PERMIT_STR_01_READ,
    PERMIT_02_EDIT: PERMIT_STR_02_EDIT,
    PERMIT_04_AUTH1: PERMIT_STR_04_AUTH1,
    PERMIT_08_AUTH2: PERMIT_STR_08_AUTH2,
    PERMIT_16_ANALYZE: PERMIT_STR_16_ANALYZE,
    PERMIT_32_ADMIN: PERMIT_STR_32_ADMIN,
    PERMIT_64_SYSTEM: PERMIT_STR_64_SYSTEM
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

# PR2018-08-01
CHOICES_ROLE = (
    (ROLE_08_SCHOOL, _('School')),
    (ROLE_16_INSP, _('Inspection')),
    (ROLE_32_ADMIN, _('Administrator')),
    (ROLE_64_SYSTEM, _('System'))
)

# PR2018-08-07
CHOICES_ROLE_DICT = {
    ROLE_08_SCHOOL: _('School'),
    ROLE_16_INSP: _('Inspection'),
    ROLE_32_ADMIN: _('Administrator'),
    ROLE_64_SYSTEM: _('System')
}

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
# options_examtype value = ecamtype, filter = examperiod PR2020-12-17
EXAMTYPE_OPTIONS = [
    {'value': 'se', 'filter': EXAMPERIOD_FIRST, 'caption': _('School exam')},
    {'value': 'pe', 'filter': EXAMPERIOD_FIRST, 'caption': _('Practical exam')},
    {'value': 'ce', 'filter': EXAMPERIOD_FIRST, 'caption': _('Central exam')},
    {'value': 're2', 'filter': EXAMPERIOD_SECOND, 'caption': _('Re-examination')},
        {'value': 're3', 'filter': EXAMPERIOD_THIRD, 'caption': _('Re-examination 3rd period')},
    {'value': 'exm', 'filter': EXAMPERIOD_EXEMPTION, 'caption': _('School- / Central exam')}
    ]

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

# USER SETTING KEYS PR2018-12-19 PR2020-12-18
KEY_MENU_SELECTED = "menu_selected"
KEY_SELECTED_PK = 'selected_pk'
KEY_SEL_EXAMYEAR_PK = 'sel_examyear_pk'
KEY_SEL_SCHOOLBASE_PK = 'sel_schoolbase_pk'
KEY_SEL_DEPBASE_PK = 'sel_depbase_pk'
KEY_SEL_EXAMPERIOD_PK = 'sel_examperiod_pk'

# SCHOOL SETTING KEYS PR2018-12-03  PR2020-12-04

KEY_IMPORT_SUBJECT = 'import_subject'
KEY_IMPORT_STUDENT = 'import_student'

KEY_COLDEF = {
    KEY_IMPORT_SUBJECT:
         ({'awpColdef': 'code', 'caption': _('Subject abbreviation'), 'linkfield': True},
          {'awpColdef': 'name', 'caption': _('Subject name')},
          {'awpColdef': 'sequence', 'caption': _('Sequence')},
          {'awpColdef': 'depbases', 'caption': _('Departments, in which this subject occurs')}),
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
        {'awpColdef': 'sector', 'caption': _('Sector')})
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
                        'sector': _('Sector')}
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
                 'activated', 'locked', 'activatedat', 'lockedat', 'istemplate', 'modifiedby', 'modifiedat')

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
STRING_INDENT_5 = ' ' * 5
STRING_DOUBLELINE_80 = '=' * 80