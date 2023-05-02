# PR2018-05-25 PR2020-12-04

#PR2022-02-13 was ugettext as _, replaced by: gettext as _
from django.utils.translation import gettext as _

USERNAME_MAX_LENGTH = 30
USERNAME_SLICED_MAX_LENGTH = 24
USER_LASTNAME_MAX_LENGTH = 50
MAX_LENGTH_KEY = 24  # number is also hardcoded in _()
MAX_LENGTH_NAME = 50
MAX_LENGTH_EMAIL_ADDRESS = 254
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
#PR2022-05-08 Omega College could not upload Ex3, was 1,2 Mb. Max size set to 2 Mb
#PR2022-08-30 was: 2
MAX_ATTACHMENT_SIZE_Mb = 5

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
CHOICES_LOCKED = (
    (0, _('Unlocked')),
    (1, _('Locked'))
)
LOCKED_DICT = {
    0: _('Unlocked'),
    1: _('Locked')
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
SCHEMEFIELD_PRACTEXAM = 'prac'

SCHEMEFIELD_CHOICES = (
    (SCHEMEFIELD_MANDATORY, _('Mandatory')),
    (SCHEMEFIELD_COMBI, _('Combination subject')),
    (SCHEMEFIELD_PRACTEXAM, _('Practical exam')),
)

# translation not working in dict, error: 'must be str, not __proxy__'
# Solved by using 'ugettext' instead of 'ugettext_lazy'


# PR2019-02-15
SCORE = 1
GRADE = 2
PECE = 3
FINAL = 4


GRADE_IN_LETTERS = {
    '1': _('een'),
    '2': _('twee'),
    '3': _('drie'),
    '4': _('vier'),
    '5': _('vijf'),
    '6': _('zes'),
    '7': _('zeven'),
    '8': _('acht'),
    '9': _('negen'),
    '10': _('tien'),
    'o': _('onvoldoende'),
    'v': _('voldoende'),
    'g': _('goed'),
    'O': _('onvoldoende'),
    'V': _('voldoende'),
    'G': _('goed')
}



# PR2019-02-15 PR2020-12-14 PR2023-03-31
EXAMPERIOD_FIRST = 1
EXAMPERIOD_SECOND = 2
EXAMPERIOD_THIRD = 3
EXAMPERIOD_EXEMPTION = 4
EXAMPERIOD_ALL = -1
EXAMPERIOD_FIRST_PLUS_SECOND = 12

EXAMPERIOD_CAPTION = {
    EXAMPERIOD_FIRST: _('First exam period'),
    EXAMPERIOD_SECOND: _('Second exam period'),
    EXAMPERIOD_THIRD: _('Third exam period'),
    EXAMPERIOD_EXEMPTION: _('Exemption'),
    EXAMPERIOD_ALL: _('All exam periods'),
    EXAMPERIOD_FIRST_PLUS_SECOND: ' / '.join((str(_('First exam period')), str(_('Second exam period')) ))
}
EXAMPERIOD_OPTIONS = [{'value': EXAMPERIOD_FIRST, 'caption': _('First exam period')},
                        {'value': EXAMPERIOD_SECOND, 'caption': _('Second exam period')},
                        {'value': EXAMPERIOD_THIRD, 'caption': _('Third exam period')},
                        {'value': EXAMPERIOD_EXEMPTION, 'caption': _('Exemption')}]

EXAMPERIOD_OPTIONS_123ONLY = [{'value': EXAMPERIOD_ALL, 'caption': ''.join(('&#60', str(_('All exam periods')), '&#62'))},
                             {'value': EXAMPERIOD_FIRST, 'caption': _('First exam period')},
                            {'value': EXAMPERIOD_SECOND, 'caption': _('Second exam period')},
                            {'value': EXAMPERIOD_THIRD, 'caption': _('Third exam period')}]

# examgradetypes are: 'segrade', 'srgrade', 'pescore', 'pegrade', 'cescore', 'cegrade
EXAMGRADE_OPTIONS = [
    {'value': 'exemsegrade', 'caption': _('Exemption - school exam grade')},
    {'value': 'exemcegrade', 'caption': _('Exemption - central exam grade')},
    {'value': 'segrade', 'caption': _('School exam grade')},
    {'value': 'srgrade', 'caption': _('Re-examination school exam')},
    {'value': 'pescore', 'caption': _('Practical exam score')},
    {'value': 'pegrade', 'caption': _('Practical exam grade')},
    {'value': 'cescore', 'caption': _('Central exam score')},
    {'value': 'cegrade', 'caption': _('Central exam grade')},
    {'value': 'reexscore', 'caption': _('Re-examination score')},
    {'value': 'reexgrade', 'caption': _('Re-examination grade')},
    {'value': 'reex03score', 'caption': _('Re-examination 3rd period score')},
    {'value': 'reex03grade', 'caption': _('Re-examination 3rd period grade')},
]


def get_examperiod_caption(examperiod_int):
    return EXAMPERIOD_CAPTION.get(examperiod_int, '')


# options_examtype value = ecamtype, filter = examperiod PR2020-12-17
EXAMTYPE_OPTIONS = [
    {'value': 'se', 'caption': _('School exam')},
    {'value': 'sr', 'caption': _('Re-examination school exam')},
    {'value': 'pe', 'caption': _('Practical exam')},
    {'value': 'ce', 'caption': _('Central exam')},
    {'value': 'reex', 'caption': _('Re-examination')},
    {'value': 'reex03', 'caption': _('Re-examination 3rd period')},
    {'value': 'exem', 'caption': _('Exemption')},
    {'value': 'all', 'caption': _('All exams')}
    ]
# options_examtype value = ecamtype, filter = examperiod PR2021-05-07
# used in page exam, without SE and EXEMPTION
EXAMTYPE_OPTIONS_EXAM = [
    #{'value': 'se', 'filter': EXAMPERIOD_FIRST, 'caption': _('School exam')},
    #{'value': 'sere', 'filter': EXAMPERIOD_FIRST, 'caption': _('Re-examination school exam')},
    #{'value': 'pe', 'filter': EXAMPERIOD_FIRST, 'caption': _('Practical exam')},
    {'value': 'ce', 'filter': EXAMPERIOD_FIRST, 'caption': _('Central exam')},
    {'value': 'reex', 'filter': EXAMPERIOD_SECOND, 'caption': _('Re-examination')},
    #{'value': 'reex03', 'filter': EXAMPERIOD_THIRD, 'caption': _('Re-examination 3rd period')},
    #{'value': 'exem', 'filter': EXAMPERIOD_EXEMPTION, 'caption': _('School- / Central exam')}
    ]
EXAMTYPE_CAPTION = {
    'se': _('School exam'),
    'sere': _('Re-examination school exam'),
    'pe': _('Practical exam'),
    'ce': _('Central exam'),
    'reex': _('Re-examination'),
    'reex03': _('Re-examination 3rd period'),
    'exem': _('Exemption'),
}


def get_examtype_caption(examtype_str):
    return EXAMTYPE_CAPTION.get(examtype_str, '')

# PR2018-11-28
# se, pe ce, ce2, ce3, end
RESULT_NORESULT = 0
RESULT_PASSED = 1
RESULT_FAILED = 2
# RESULT_REEXAM is not in use
#   RESULT_REEXAM = 3
RESULT_WITHDRAWN = 4

RESULT_CAPTION = [
    _('No result'),
    _('Passed'),
    _('Failed'),
    _('Re-examination'),
    _('Withdrawn')
]

STATUS_NONE = 0
STATUS_00_CREATED = 1
STATUS_01_AUTH1 = 2
STATUS_02_AUTH2 = 4
STATUS_03_AUTH3 = 8
STATUS_04_AUTH4 = 16
STATUS_05_PUBLISHED = 32
STATUS_06_BLOCKED = 64

"""
STATUS_06_REQUEST = 64
STATUS_07_WARNING = 128
STATUS_08_REJECTED = 256
STATUS_09_REQUEST_ANSWERED = 512
# STATUS_09_WARNING_ANSWERED = 512
STATUS_10_REJECTED_ANSWERED = 1024
STATUS_11_EDIT = 2048
STATUS_12_EDIT_ANSWERED = 4096
STATUS_13_APPROVED = 8192
STATUS_14_LOCKED = 16384


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
KEY_SELECTED_PK = 'selected_pk'
KEY_SEL_EXAMPERIOD = 'sel_examperiod'
KEY_SEL_EXAMTYPE = 'sel_examtype'
KEY_SEL_EXAMYEAR_PK = 'sel_examyear_pk'
KEY_SEL_SCHOOLBASE_PK = 'sel_schoolbase_pk'
KEY_SEL_DEPBASE_PK = 'sel_depbase_pk'
KEY_SEL_LVLBASE_PK = 'sel_lvlbase_pk'
KEY_SEL_SCTBASE_PK = 'sel_sctbase_pk'
KEY_SEL_SUBJBASE_PK = 'sel_subjbase_pk'
KEY_SEL_STUDENT_PK = 'sel_student_pk'
KEY_SEL_CLUSTER_PK = 'sel_cluster_pk'
KEY_SEL_AUTH_INDEX = 'sel_auth_index'
#TODO to be deprecated
KEY_SEL_SUBJECT_PK = 'sel_subject_pk'

KEY_SEL_SCHEME_PK = 'sel_scheme_pk'
KEY_SEL_BTN = 'sel_btn'
KEY_SEL_PAGE = 'sel_page'
KEY_COLS_HIDDEN = 'cols_hidden'
KEY_VERIFICATIONCODE = 'verificationcode'
KEY_EX3 = 'ex3'
KEY_GRADELIST = 'gradelist'
KEY_OPENARGS = 'open_args'

# SCHOOL SETTING KEYS PR2018-12-03  PR2020-12-04

KEY_IMPORT_SUBJECT = 'import_subject'
KEY_IMPORT_STUDENT = 'import_student'
KEY_IMPORT_STUDENTSUBJECT = 'import_studsubj'
KEY_IMPORT_GRADE = 'import_grade'
KEY_IMPORT_PERMITS = 'import_permit'
KEY_IMPORT_USERNAME = 'import_username'

# PR2021-04-21
# when one_unique_identifier =  True: only 1 of the linkfields can be the identifier (either exnr or idnr of the candidate)
# when one_unique_identifier = False: all linkfields must be used to lookup recrds (permits: c_abbrev, page, role and action)

# don't use tuple, because department may be removed from list student
KEY_COLDEF = {
    KEY_IMPORT_SUBJECT:
        [{'awpColdef': 'code', 'caption': _('Subject abbreviation'), 'linkrequired': True, 'unique': True},
          {'awpColdef': 'name', 'caption': _('Subject name')},
          {'awpColdef': 'sequence', 'caption': _('Sequence')},
          {'awpColdef': 'depbases', 'caption': _('Departments, in which this subject occurs')}],

    KEY_IMPORT_STUDENTSUBJECT:
        [# PR2021-08-11 NOT IN USE: {  'awpColdef': 'examnumber', 'caption': _('Exam number')},
            {'awpColdef': 'idnumber', 'caption': _('ID-number'), 'linkrequired': True, 'unique': True},
            {'awpColdef': 'pws_title', 'caption': _('Title assignment')},
            {'awpColdef': 'pws_subjects', 'caption': _('Subjects assignment')},

            # PR2021-08-11 NOT IN USE:
            # to be used for tabular upload :
            #{'awpColdef': 'subject', 'caption': _('Subject'), 'tabularfield': True}
            # PR2021-08-11 NOT IN USE:
            #{'awpColdef': 'subjecttype', 'caption': _('Character'), 'tabularfield': True}
         ],

    KEY_IMPORT_GRADE:
        [ {'awpColdef': 'idnumber', 'caption': _('ID-number'), 'linkrequired': True, 'unique': True},
        ],

    KEY_IMPORT_STUDENT:
        [ {'awpColdef': 'idnumber', 'caption': _('ID-number'), 'linkrequired': True, 'unique': True},
        {'awpColdef': 'lastname', 'caption': _('Last name'), 'linkrequired': True},
        {'awpColdef': 'firstname', 'caption': _('First name'), 'linkrequired': True},
        {'awpColdef': 'prefix', 'caption': _('Prefix')},
        {'awpColdef': 'gender', 'caption': _('Gender')},
        {'awpColdef': 'examnumber', 'caption': _('Exam number')},
        {'awpColdef': 'birthdate', 'caption': _('Birthdate'), 'datefield': True},
        {'awpColdef': 'birthcountry', 'caption': _('Country of birth')},
        {'awpColdef': 'birthcity', 'caption': _('Place of birth')},
        {'awpColdef': 'classname', 'caption': _('Class name')},
        #{'awpColdef': 'iseveningstudent', 'caption': _('Evening student')},
        {'awpColdef': 'bis_exam', 'caption': _('Bis exam')},

        {'awpColdef': 'extrafacilities', 'caption': _('Extra facilities')},
        {'awpColdef': 'department', 'caption': _('Department')},

        {'awpColdef': 'level', 'caption': _('Level'), 'linkrequired': True},
        {'awpColdef': 'sector', 'caption': _('Sector'), 'linkrequired': True},
        {'awpColdef': 'profiel', 'caption': _('Profile'), 'linkrequired': True},
        {'awpColdef': 'diplomanumber', 'caption': _('Diploma number')},
        {'awpColdef': 'gradelistnumber', 'caption': _('Gradelist number')}
         ],

    KEY_IMPORT_PERMITS:
        [{'awpColdef': 'c_abbrev', 'caption': _('Country'), 'linkrequired': True},
         {'awpColdef': 'page', 'caption': _('Page'), 'linkrequired': True},
         {'awpColdef': 'role', 'caption': _('Organization'), 'linkrequired': True},
         {'awpColdef': 'action', 'caption': _('Action'), 'linkrequired': True},
         {'awpColdef': 'usergroups', 'caption': _('User groups')},
         {'awpColdef': 'sequence', 'caption': _('Sequence')}
         ],
    KEY_IMPORT_USERNAME:
        [{'awpColdef': 'schoolcode', 'caption': _('School code'), 'linkrequired': True},
         {'awpColdef': 'username', 'caption': _('Username'), 'linkrequired': True},
         {'awpColdef': 'last_name', 'caption': _('Name'), 'linkrequired': True},
         {'awpColdef': 'email', 'caption': 'Email', 'linkrequired': True},
         {'awpColdef': 'function', 'caption': _('Function')}
         ],
}

GRADELIST_PWS_TITLE_MAX_LENGTH_MM = 95  # = 269 points / 72 * 25.4 PR2022-06-25
GRADELIST_PWS_SUBJECTS_MAX_LENGTH_MM = 73  # = 208 points / 72 * 25.4 PR2022-06-25

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
                        'extrafacilities': _('Extra facilities'),
                        'iseveningstudent': _('Evening student'),
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
                  'classname', 'examnumber', 'regnumber', 'diplomanumber', 'gradelistnumber', 'iseveningstudent',
                  'locked', 'has_reex', 'bis_exam', 'withdrawn', 'modifiedby', 'modifiedat')
FIELDS_STUDENTSUBJECT = ('student', 'schemeitem', 'cluster', 'is_extra_nocount', 'is_extra_counts',
                'pws_title', 'pws_subjects', 'has_exemption', 'has_reex', 'has_reex03', 'exemption_year', 'pok_validthru',  'pex_validthru',
               'subj_auth1by', 'subj_auth2by', 'subj_published',
               'exem_auth1by', 'exem_auth2by', 'exem_published',
               'reex_auth1by', 'reex_auth2by', 'reex_published',
               'reex3_auth1by', 'reex3_auth2by', 'reex3_published',
               'pok_auth1by', 'pok_auth2by', 'pok_published',
               'deleted', 'modifiedby', 'modifiedat')
FIELDS_GRADE =('studentsubject', 'examperiod',
               'pescore', 'cescore',
               'segrade', 'srgrade', 'sesrgrade',
               'pegrade', 'cegrade', 'pecegrade', 'finalgrade',
               'se_auth1by', 'se_auth2by', 'se_published',
               'pe_auth1by', 'pe_auth2by', 'pe_published',
               'ce_auth1by', 'ce_auth2by', 'ce_published',
               'deleted', 'status', 'modifiedby', 'modifiedat')


STRING_SPACE_40 = ' ' * 40
STRING_SPACE_30 = ' ' * 30
STRING_SPACE_20 = ' ' * 20
STRING_SPACE_15 = ' ' * 15
STRING_SPACE_10 = ' ' * 10
STRING_SPACE_05 = ' ' * 5
STRING_DOUBLELINE_80 = '=' * 80
STRING_SINGLELINE_80 = '-' * 80

# ============================================================================
# ROLES AND PERMITS PR2021-02-23
# ============================================================================

# PR2018-05-07
#ROLE_000_NONE = 0
#ROLE_002_STUDENT = 2
#ROLE_004_TEACHER = 4
ROLE_008_SCHOOL = 8
ROLE_016_CORR = 16
ROLE_032_INSP = 32
ROLE_064_ADMIN = 64
ROLE_128_SYSTEM = 128

# PR2018-12-23 used in set_menu_items
ROLE_DICT = {
    ROLE_008_SCHOOL: 'school',
    ROLE_016_CORR: 'corr',
    ROLE_032_INSP: 'insp',
    ROLE_064_ADMIN: 'admin',
    ROLE_128_SYSTEM: 'system'
    }


def get_role_options(request):
    ETE_DEX = _('Division of Examinations') if request.user.country.abbrev.lower() == 'sxm' else 'ETE'
    _role_options = [
        {'value': ROLE_008_SCHOOL, 'caption': _('School')},
        {'value': ROLE_016_CORR, 'caption': _('Second correctors')},
        {'value': ROLE_032_INSP, 'caption': _('Inspectorate')},
        {'value': ROLE_064_ADMIN, 'caption': ETE_DEX},
        {'value': ROLE_128_SYSTEM, 'caption': _('System manager')}
    ]
    return _role_options


# PR2018-05-21 PR2021-04-23 PR2021-10-22 teacher added NIU 2022-02-22
USERGROUP_READ = 'read' # tobe deprecated PR2023-04-22
USERGROUP_EDIT = 'edit'
USERGROUP_WOLF = 'wolf' # added PR2023-04-22
#USERGROUP_TEACHER = 'teach'
USERGROUP_AUTH1_PRES = 'auth1'
USERGROUP_AUTH2_SECR = 'auth2'
USERGROUP_AUTH3_EXAM = 'auth3'
USERGROUP_AUTH4_CORR = 'auth4'
USERGROUP_ANALYZE = 'anlz'
USERGROUP_ADMIN = 'admin'
USERGROUP_MSGWRITE = 'msgsend'
USERGROUP_MSGRECEIVE = 'msgreceive'
USERGROUP_ARCHIVE = 'archive'
USERGROUP_DOWNLOAD = 'download'

USERGROUP_TUPLE = (
    USERGROUP_READ,
    USERGROUP_EDIT,
    USERGROUP_WOLF,
    #USERGROUP_TEACHER,
    USERGROUP_AUTH1_PRES,
    USERGROUP_AUTH2_SECR,
    USERGROUP_AUTH3_EXAM,
    USERGROUP_AUTH4_CORR,
    USERGROUP_DOWNLOAD,
    USERGROUP_ARCHIVE,
    USERGROUP_MSGWRITE,
    USERGROUP_MSGRECEIVE,
    USERGROUP_ANALYZE,
    USERGROUP_ADMIN
)

USERGROUP_CAPTION = {
    USERGROUP_READ: _('Read'),
    USERGROUP_EDIT: _('Edit'),
    USERGROUP_WOLF: _('Wolf'),
    #USERGROUP_TEACHER: _('Teacher'),
    USERGROUP_AUTH1_PRES: _('Chairperson'),
    USERGROUP_AUTH2_SECR: _('Secretary'),
    USERGROUP_AUTH3_EXAM: _('Examiner'),
    USERGROUP_AUTH4_CORR: _('Corrector'),
    USERGROUP_DOWNLOAD: _('Download'),
    USERGROUP_ARCHIVE: _('Access to archive'),
    USERGROUP_MSGWRITE: _('Send messages'),
    USERGROUP_MSGRECEIVE: _('Receive messages'),
    USERGROUP_ANALYZE: _('Analyze'),
    USERGROUP_ADMIN: _('System administrator')
}


MAILBOX_USERGROUPS = {
    USERGROUP_AUTH1_PRES: _('Chairperson'),
    USERGROUP_AUTH2_SECR: _('Secretary'),
    USERGROUP_AUTH3_EXAM: _('Examiner'),
    USERGROUP_AUTH4_CORR: _('Corrector'),
    USERGROUP_ADMIN: _('System administrator')
}
# PR2023-04-15 compensation for correctors
"""
Mail Shailini van Uytrecht Feb 9, 2023:
De tarieven zijn volgens de Landsbesluit van 1994 vastgelegd en veranderen niet.
Hieronder de tarieven die wij aan de gecommitteerden uitbetalen: 
Correctie van het eerste schriftelijke examenwerk is 25 gulden 
Correctie van de overige schriftelijke examenwerken is 10 gulden. 
Bijwonen vergadering is 30 gulden per vergadering (tot een max. van 2 verg. per vak) 

"""
CORRCOMP_FIRST_APPROVAL = 2500 # compensation of the first approved exam, in cents
CORRCOMP_OTHER_APPROVAL = 1000 # compensation of the following approved exams, in cents
CORRCOMP_MEETING_COMP = 3000 # compensation per meeting, in cents
CORRCOMP_MAX_MEETINGS = 2 # max number of meetings

COLOR_LIST = [
    ['black', ' '],
    ['red', _('red')],
    ['blue', _('blue')],
    ['green', _('green')],
    ['purple', _('purple')],
    ['orange', _('orange')],
    ['yellow', _('yellow')]
]
LABEL_COLOR = {
    'black': '#000000', # rgb 0 0 0  #000000
    'red': '#ff0000', # rgb 255 0 0  #ff0000
    'blue': '#0000ff', # rgb 0 0 255  #0000ff
    #'yellow': '#ffff00', # rgb 255 255 0 #ffff00
    'yellow': '#ffd700', # gold: rgb 255 215 0 #ffd700
    'green': '#538135',  # rgb 83 129 53  #538135
    'orange': '#ed7d31', # rgb 237 125 49  #ed7d31
    'purple': '#7030a0' # rgb 112 48 160  #7030a0
}

LABEL_WEEKDAYS = {
    'nl': {
        0: 'zondag',
        1: 'maandag',
        2: 'dinsdag',
        3: 'woensdag',
        4: 'donderdag',
        5: 'vrijdag',
        6: 'zaterdag'
    },
    'en': {
        0: 'Sunday',
        1: 'Monday',
        2: 'Tuesday',
        3: 'Wednesday',
        4: 'Thursday',
        5: 'Friday',
        6: 'Saturday'
    },
    'pa': {
        0: 'djadomingo',
        1: 'djaluna',
        2:  'djamars',
        3:  'djárason',
        4: 'djaweps',
        5: 'djabièrnè',
        6:  'djasabra'
    }
}

LABEL_MONTHS = {
    'nl': {
        1: 'januari',
        2: 'februari',
        3: 'maart',
        4: 'april',
        5: 'mei',
        6: 'juni',
        7: 'juli',
        8: 'augustus',
        9: 'september',
        10: 'oktober',
        11: 'november',
        12: 'december'
    },
    'en': {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December'
    },
    'pa': {
        1: 'yanüari',
        2: 'febrüari',
        3: 'mart',
        4: 'aprel',
        5: 'mei',
        6: 'yüni',
        7: 'yüli',
        8: 'ougùstùs',
        9: 'sèptèmber',
        10: 'òktober',
        11: 'novèmber',
        12: 'desèmber'
    }
}

LABEL_TEXT = {
    'nl': {
        'exam': 'EXAMEN',
        'ep': 'TIJDVAK',
        'cse': 'CSE',
        'cspe': 'CSPE',
        'date': 'Afnamedatum',
        'period': 'Afnameperiode',
        'time': 'Afnametijd',
        'duration': 'Afnameduur',
        'school': 'Schoolnaam',
        'numex': 'Aantal exemplaren',
        'numenv': 'Envelop',
        'content': 'INHOUD',
        'oclock': 'uur',
        'minutes': 'minuten',
        'of': 'van'
    },
    'en': {
        'exam': 'EXAM',
        'ep': 'PERIOD',
        'cse': 'CSE',
        'cspe': 'CWPE',
        'date': 'Examination date',
        'period': 'Examination period',
        'time': 'Time exam',
        'duration': 'Examination duration',
        'school': 'School name',
        'numex': 'Number of copys',
        'numenv': 'Envelope',
        'content': 'CONTENT',
        'oclock':  "hour",
        'minutes': 'minutes',
        'of':  "of"
    },
    'pa': {
        'exam': 'ÈKSAMEN',
        'ep': 'PERIODO',
        'cse': 'CSE',
        'cspe': 'ESPS',
        'date': 'Fecha di èksamen',
        'period': 'Periodo di èksamen',
        'time': 'Orario di èksamen',
        'duration': 'Durashon di èksamen',
        'school': 'Nòmber di Skol',
        'numex':'Kantidat di eksemplar',
        'numenv':'Ènvelòp',
        'content':'KONTENIDO',
        'oclock': 'or',
        'minutes': 'minüt',
        'of': 'di'
    }
}

# HTML classes
HTMLCLASS_border_bg_invalid = 'border_bg_invalid'
HTMLCLASS_border_bg_valid = 'border_bg_valid'
HTMLCLASS_border_bg_warning = 'border_bg_warning'
HTMLCLASS_border_bg_transparent = 'border_bg_transparent'

# XLSWRITER FORMATS
XF_BOLD = {'bold': True}
XF_BOLD_FCBLUE = {'font_color': 'blue', 'bold': True}
XF_FCBLUE = {'font_color': 'blue'}

XF_FOOTER_SIZE11_ALIGNCENTER_BLACK = {'font_size': 11, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter'}
XF_FOOTER_SIZE08_ALIGNCENTER_BLACK = {'font_size': 8, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter'}
XF_FOOTER_SIZE11_ALIGNLEFT_BLACK = {'font_size': 11, 'font_color': 'black', 'align': 'left', 'valign': 'vcenter'}
XF_FOOTER_SIZE08_ALIGNCENTER_BLUE = {'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter'}
XF_FOOTER_SIZE11_ALIGNLEFT_BLUE = {'font_size': 11, 'font_color': 'blue', 'align': 'left', 'valign': 'vcenter'}
XF_FOOTER_SIZE11_ALIGNCENTER_RED = {'font_size': 11, 'font_color': 'red', 'align': 'center', 'valign': 'vcenter'}

# row_align_left
XF_ROW_ALIGN_LEFT_BLUE = {'font_size': 8, 'font_color': 'blue', 'align': 'left', 'valign': 'vcenter', 'border': True}
# row_align_center
XF_ROW_ALIGN_CENTER_BLUE = {'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'border': True}

XF_ROW_ALIGN_CENTER_BLACK = {'font_size': 8, 'font_color': 'black', 'align': 'center', 'valign': 'vcenter', 'border': True}
# row_align_center_red
XF_ROW_ALIGN_CENTER_RED = {'font_size': 8, 'font_color': 'red', 'align': 'center', 'valign': 'vcenter', 'border': True}
# row_align_left_red
XF_ROW_ALIGN_LEFT_RED = {'font_size': 8, 'font_color': 'red', 'align': 'left', 'valign': 'vcenter', 'border': True}

#row_align_center_green
XF_ROW_ALIGN_CENTER_GREEN = {'font_size': 8, 'font_color': '#008000', 'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': True}
#row_align_left_green
XF_ROW_ALIGN_LEFT_GREEN = {'font_size': 8, 'font_color': '#008000', 'bold': True, 'align': 'left', 'valign': 'vcenter', 'border': True}

XF_ROW_BG_LIGHTGREY = {'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'border': True}

#  color #6c757d;  /* dark grey (awp tab grey) 108 117 125 100%
XF_HDR_BG_DARKGREY_ALC_BORDER = {'font_size': 8, 'border': True, 'bg_color': '#d8d8d8', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
#  color #d8d8d8;  /* light grey 218 218 218 100%
XF_HDR_BG_LIGHTGREY_ALC_BORDER = {'font_size': 8, 'border': True, 'bg_color': '#d8d8d8', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
#  color #f2f2f2;  /* light light grey 242 242 242 100%
XF_HDR_BG_LIGHTLIGHTGREY_ALC_BORDER = {'font_size': 8, 'border': True, 'bg_color': '#f2f2f2', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
# th_align_center #d8d8d8;  /* light grey 218 218 218 100%
XF_HDR_ALC_TOPBOTTOM = {'font_size': 8, 'border': True, 'bold': True, 'bg_color': '#d8d8d8', 'top': 1, 'bottom': 2, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
# th_align_left #d8d8d8;  /* light grey 218 218 218 100%
XF_HDR_ALL_TOPBOTTOM = {'font_size': 8, 'border': True, 'bold': True, 'bg_color': '#d8d8d8', 'top': 1, 'bottom': 2, 'align': 'left', 'valign': 'vcenter', 'text_wrap': True}

# color #a5a5a5; /* medium grey; 165 165 165 */
XF_TABLEHEADER = {'font_size': 10, 'bold': True, 'bottom': 1, 'top': 1, 'bg_color': '#d8d8d8', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
XF_TABLEHEADER_ALIGNLEFT = {'font_size': 10, 'bold': True, 'bottom': 1, 'top': 1, 'bg_color': '#d8d8d8', 'align': 'left', 'valign': 'vcenter', 'text_wrap': True}
XF_TABLEHEADER_BORDERLEFT = {'font_size': 10, 'bold': True, 'bottom': 1, 'top': 1, 'left': 1, 'bg_color': '#d8d8d8', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}

# color #a5a5a5; /* medium grey; 165 165 165 */
XF_HDR_GRANDTOTAL = {'font_size': 10, 'bold': True, 'bottom': 2, 'top': 1, 'bg_color': '#a5a5a5', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
XF_HDR_GRANDTOTAL_ALIGNLEFT = {'font_size': 10, 'bold': True, 'bottom': 2, 'top': 1, 'bg_color': '#a5a5a5', 'align': 'left', 'valign': 'vcenter', 'text_wrap': True}
XF_HDR_GRANDTOTAL_BORDERLEFT = {'font_size': 10, 'bold': True, 'bottom': 2, 'top': 1, 'left': 1, 'bg_color': '#a5a5a5', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
XF_HDR_GRANDTOTAL_PERCENTAGE = {'font_size': 10, 'bold': True, 'num_format': '0%', 'bottom': 2, 'top': 1, 'bg_color': '#a5a5a5', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
XF_HDR_GRANDTOTAL_PERCENTAGE_BORDERLEFT = {'font_size': 10, 'bold': True, 'num_format': '0%', 'bottom': 2, 'top': 1, 'left': 1, 'bg_color': '#a5a5a5', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}

#  color #d8d8d8;  /* light grey 218 218 218 100%
XF_HDR_SUBTOTAL = {'font_size': 10, 'bold': True, 'bottom': 2, 'top': 1, 'bg_color': '#d8d8d8', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
XF_HDR_SUBTOTAL_ALIGNLEFT = {'font_size': 10, 'bold': True, 'bottom': 2, 'top': 1, 'bg_color': '#d8d8d8', 'align': 'left', 'valign': 'vcenter', 'text_wrap': True}
XF_HDR_SUBTOTAL_BORDERLEFT = {'font_size': 10, 'bold': True, 'bottom': 2, 'top': 1, 'left': 1, 'bg_color': '#d8d8d8', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
XF_HDR_SUBTOTAL_PERCENTAGE = {'font_size': 10, 'bold': True, 'num_format': '0%', 'bottom': 2, 'top': 1, 'bg_color': '#d8d8d8', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
XF_HDR_SUBTOTAL_PERCENTAGE_BORDERLEFT = {'font_size': 10, 'bold': True, 'num_format': '0%', 'bottom': 2, 'top': 1, 'left': 1, 'bg_color': '#d8d8d8', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}

#  color #f2f2f2;  /* light light grey 242 242 242 100%
XF_HDR_SUBSUBTOTAL = {'font_size': 10, 'bold': True, 'bottom': 2, 'top': 1, 'bg_color': '#f2f2f2', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
XF_HDR_SUBSUBTOTAL_ALIGNLEFT = {'font_size': 10, 'bold': True, 'bottom': 2, 'top': 1, 'bg_color': '#f2f2f2', 'align': 'left', 'valign': 'vcenter', 'text_wrap': True}
XF_HDR_SUBSUBTOTAL_BORDERLEFT = {'font_size': 10, 'bold': True, 'bottom': 2, 'top': 1, 'left': 1, 'bg_color': '#f2f2f2', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
XF_HDR_SUBSUBTOTAL_PERCENTAGE = {'font_size': 10, 'bold': True, 'num_format': '0%', 'bottom': 2, 'top': 1, 'bg_color': '#f2f2f2', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}
XF_HDR_SUBSUBTOTAL_PERCENTAGE_BORDERLEFT = {'font_size': 10, 'bold': True, 'num_format': '0%', 'bottom': 2, 'top': 1, 'left': 1, 'bg_color': '#f2f2f2', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}

# row_align_left
XF_ROW_VALUE = {'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'bottom': 1, 'text_wrap': True}
XF_ROW_VALUE_ALIGNLEFT = {'font_size': 8, 'font_color': 'blue', 'align': 'left', 'valign': 'vcenter', 'bottom': 1, 'text_wrap': True}
XF_ROW_PERCENTAGE = {'font_size': 8, 'num_format': '0%', 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'bottom': 1, 'text_wrap': True}
XF_ROW_VALUE_BORDERLEFT = {'font_size': 8, 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'bottom': 1, 'left': 1,'text_wrap': True}
XF_ROW_PERCENTAGE_BORDERLEFT = {'font_size': 8, 'num_format': '0%', 'font_color': 'blue', 'align': 'center', 'valign': 'vcenter', 'bottom': 1, 'left': 1,'text_wrap': True}

