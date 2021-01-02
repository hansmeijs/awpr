# PR2020-09-17

from django.utils.translation import pgettext_lazy, ugettext_lazy as _
from awpr import constants as c

import logging
logger = logging.getLogger(__name__)


# === get_locale_dict ===================================== PR2019-11-12
def get_locale_dict(table_dict, user_lang):

    #TODO use user_lang etc from settings_dict
    dict = {'user_lang': user_lang}

    page = table_dict.get('page')

    dict['weekdays_abbrev'] = TXT_weekdays_abbrev
    dict['weekdays_long'] = TXT_weekdays_long
    dict['months_abbrev'] = TXT_months_abbrev
    dict['months_long'] = TXT_months_long

    # select examyear, school, department
    dict['Filter'] = _('Filter ')
    dict['Select'] = _('Select ')
    dict['Type_few_letters_and_select'] = _('Type a few letters and select ')
    dict['an_examyear'] = _('an exam year')
    dict['a_school'] = _('a school')
    dict['a_department'] = _('a department')
    dict['in_the_list'] = _(' in the list ...')

    dict['No__'] = pgettext_lazy('No ... selected', 'No ')
    dict['__selected'] = pgettext_lazy('No ... selected.', ' selected.')

    dict['Select_examyear'] = _('Select an exam year')
    dict['Select_school'] = _('Select a school')
    dict['Select_department'] = _('Select a department')

    dict['No_examyear_selected'] = _('No exam year selected')
    dict['No_school'] = _('No school')
    dict['No_department_selected'] = _('No department selected')

    dict['No_examyears'] = _('No exam years')
    dict['No_schools'] = _('No schools')
    dict['No_departments'] = _('No departments')
    dict['School_has_no_departments'] = _('School has no departments')
    dict['School_notfound_thisexamyear'] = _('School not found in this exam year')
    dict['Department_notfound_thisexamyear'] = _('Department not found in this exam year')

    # mod confirm
    dict['will_be_deleted'] = _(' will be deleted.')
    dict['will_be_made_inactive'] = _(' will be made inactive.')
    dict['will_be_made_active'] = _(' will be made active.')
    dict['Do_you_want_to_continue'] = _('Do you want to continue?')
    dict['Yes_delete'] = _('Yes, delete')
    dict['Yes_make_inactive'] = _('Yes, make inactive')
    dict['Yes_make_active'] = _('Yes, make active')
    dict['Make_inactive'] = _('Make inactive')
    dict['No_cancel'] = _('No, cancel')
    dict['Cancel'] = _('Cancel')
    dict['OK'] = _('OK')

    dict['Exam_year'] = _('Exam year')
    dict['Subject'] = _('Subject')
    dict['Subjects'] = _('Subjects')
    dict['Level'] = _('Level')
    dict['Levels'] = _('Levels')
    dict['Sector'] = _('Sector')
    dict['SectorProfiel'] = _('Sector/Profiel')
    dict['SectorProfiel_twolines'] = _('Sector/\nProfiel')
    dict['Leerweg'] = _('Leerweg')
    dict['Sectors'] = _('Sectors')
    dict['Abbreviation'] = _('Abbreviation')
    dict['Candidate'] = _('Candidate')
    dict['Candidates'] = _('Candidates')
    dict['Name'] = _('Name')
    dict['Department'] = _('Department')
    dict['Departments'] = _('Departments')
    dict['Sequence'] = _('Sequence')
    dict['Inactive'] = _('Inactive')
    dict['Last_modified_on'] = _('Last modified on ')
    dict['by'] = _(' by ')

    dict['Exemption'] = _('Exemption')
    dict['Exemptions'] = _('Exemptions')
    dict['Re_examination'] = _('Re-examination')
    dict['Re_examinations'] = _('Re-examinations')
    dict['Re_exam_3rd_2lns'] = _('Re-exam\n3rd period')
    dict['Proof_of_knowledge_2lns'] = _('Proof of\nknowledge')

    dict['Create'] = _('Create')
    dict['Publish'] = _('Publish')
    dict['Delete'] = _('Delete')
    dict['Save'] = _('Save')

    dict['Close_NL_afsluiten'] = pgettext_lazy('NL_afsluiten', 'Close')
    dict['Close'] = pgettext_lazy('NL_sluiten', 'Close')

    # error messages
    dict['This_field'] = _('This field ')
    dict['already_exists'] = _(' already exists.')
    dict['already_exists_but_inactive'] = _(' already exists, but is inactive.')
    dict['must_be_completed'] = _(' must be completed.')
    dict['cannot_be_blank'] = _(' cannot be blank.')

    dict['is_too_long_MAX10'] = _(' is too long. Maximum is 10 characters.')
    dict['is_too_long_MAX50'] = _(' is too long. Maximum is 50 characters.')

    dict['Number'] = _('Number')
    dict['err_msg_is_invalid_number'] = _(' is an invalid number.')
    dict['err_msg_must_be_integer'] = _(' must be an integer.')
    dict['err_msg_must_be_number_between'] =  _(' must be a number between ')
    dict['err_msg_and'] = _(' and ')
    dict['err_msg_must_be_number_less_than_or_equal_to'] = _(' must be a number less than or equal to ')
    dict['err_msg_must_be_number_greater_than_or_equal_to'] = _(' must be a number greater than or equal to ')

    dict['An_error_occurred'] = _('An error occurred.')

    dict['No_item_selected'] = _('No item selected')

    # mod select subject student
    dict['Type_afew_letters_candidate'] = _('Type a few letters of the name or exam number and select a candidate in the list.')
    dict['Type_afew_letters_subject'] = _('Type a few letters of the name or abbreviation and select a subject in the list.')
    dict['All'] = _('All ')

# ====== PAGE UPLOAD =========================
    if page == 'upload':
        dict['Select_valid_Excelfile'] = _('Please select a valid Excel file.')
        dict['Not_valid_Excelfile'] = _('This is not a valid Excel file.')
        dict['Only'] = _('Only ')
        dict['and'] = _(' and ')
        dict['are_supported'] = _(' are supported.')
        dict['No_worksheets'] = _('There are no worksheets.')
        dict['No_worksheets_with_data'] = _('There are no worksheets with data.')
        dict['coldef_list'] = [
            {'awpKey': 'custcode', 'caption': _('Customer - Short name')},
            {'awpKey': 'custname', 'caption': _('Customer - Name')},
            {'awpKey': 'custidentifier', 'caption': _('Customer - Identifier')},
            # {'awpKey': 'custcontactname', 'caption': _('Customer - Contact name')},
            # {'awpKey': 'custaddress', 'caption': _('Customer - Address')},
            # {'awpKey': 'custzipcode', 'caption': _('Customer - Zipcode')},
            # {'awpKey': 'custcity', 'caption': _('Customer - City')},
            # {'awpKey': 'custcountry', 'caption': _('Customer - Country')},
            # {'awpKey': 'custemail', 'caption': _('Customer - Email address')},
            # {'awpKey': 'custtelephone', 'caption': _('Customer - Telephone')},

            {'awpKey': 'ordercode', 'caption': _('Order - Short name')},
            {'awpKey': 'ordername', 'caption': _('Order - Name')},
            {'awpKey': 'orderidentifier', 'caption': _('Order - Identifier')},
            # {'awpKey': 'ordercontactname', 'caption': _('Order - Contact name')},
            # {'awpKey': 'orderaddress', 'caption': _('Order - Address')},
            #  {'awpKey': 'orderzipcode', 'caption': _('Order - Zipcode')},
            #  {'awpKey': 'ordercity', 'caption': _('Order - City')},
            # {'awpKey': 'ordercountry', 'caption': _('Order - Country')},
            # {'awpKey': 'orderemail', 'caption': _('Order - Email address')},
            # {'awpKey': 'ordertelephone', 'caption': _('Order - Telephone')},
            {'awpKey': 'orderdatefirst', 'caption': _('Order - First date of order')},
            {'awpKey': 'orderdatelast', 'caption': _('Order - Last date of order')}]

        dict['The_subject_data_will_be_uploaded'] = _('The subject data will be uploaded.')
        dict['Upload_subjects'] = _('Upload subjects')

# ====== PAGE USER ========================= PR2019-11-19
    elif page == 'user':

        dict['User_list'] = _('User list')
        dict['Permissions'] = _('Permissions')
        dict['Set_permissions'] = _('Set permissions')
        dict['User'] = _('User')
        dict['Read_only'] = _('Read only')
        dict['Read_only_2lines'] =  pgettext_lazy('2 lines', 'Read\nonly')
        dict['Edit'] = _('Edit')
        dict['President'] = _('President')
        dict['Secretary'] = _('Secretary')
        dict['Analyze'] = _('Analyze')
        dict['Administrator'] = _('Administrator')
        dict['Administrator_2lines'] =  pgettext_lazy('2 lines', 'Admini-\nstrator')
        dict['System_manager'] = _('System manager')
        dict['System_manager_2lines'] = pgettext_lazy('2 lines', 'System\nmanager')

        dict['Sysadm_cannot_delete_own_account'] = _("System administrators cannot delete their own account.")
        dict['Sysadm_cannot_remove_sysadm_perm'] = _("System administrators cannot remove their own 'system administrator' permission.")
        dict['Sysadm_cannot_set_readonly'] = _("System administrators cannot set their own permission to 'read-only'.")
        dict['Sysadm_cannot_set_inactive'] = _("System administrators cannot make their own account inactive.")

        dict['Username'] = _('Username')
        dict['Name'] = _('Name')
        dict['Email_address'] = TXT_Email_address
        dict['Linked_to_employee'] = _('Linked to employee')
        dict['Activated_at'] = _('Activated at')
        dict['Last_loggedin'] = _('Last logged in')
        dict['Add_user'] = _('Add user')
        dict['Add_user_to'] = _('Add user to ')
        dict['Delete_user'] = _('Delete user')
        dict['This_user'] = _('This user')
        dict['Submit_employee_as_user'] = _('Submit employee as user')
        dict['Submit'] = _('Submit')
        dict['Inactive'] = TXT_Inactive

        dict['No_user_selected']  = _('There is no user selected.')
        dict['Make_user_inactive'] = _('Make user inactive')
        dict['Make_user_active'] = _('Make user active')
        dict['This_user_is_inactive'] = _('This user is inactive.')

        dict['msg_user_info'] = [
            str(_('Required, maximum %(max)s characters. Letters, digits and @/./+/-/_ only.') % {'max': c.USERNAME_SLICED_MAX_LENGTH}),
            str(_('Required, maximum %(max)s characters.') % {'max': c.USER_LASTNAME_MAX_LENGTH}),
            str(_('Required. It must be a valid email address.'))]

        dict['Click_to_register_new_user'] = _('Click the submit button to register the new user.')
        dict['We_will_send_an_email_to_the_new_user'] = _('We will send an email to the new user, with a link to create a password and activate the account.')
        dict['Activationlink_expired'] = _('The link to active the account is valid for 7 days and has expired.')
        dict['We_will_resend_an_email_to_user'] = _('We will email a new activation link to the user.')
        dict['Activation_email_not_sent'] = _('The activation email has not been sent.')

        dict['Resend_activationlink'] = _('Click to send an email with a new activation link.')
        dict['Activated'] = _('Activated')
        dict['Resend_activation_email'] = _('Resend activation email')

        dict['Yes_send_email'] = _('Yes, send email')

# ====== PAGE EXAM YEAR ========================= PR2020-10-04
    elif page == 'examyear':
        dict['Created_on'] = _('Created on ')

        dict['Published'] = _('Published')
        dict['Not_published'] = _('Not published')
        dict['Published_on'] = _('Published on ')

        dict['Locked'] = _('Locked')
        dict['Not_locked'] = _('Not locked')
        dict['Locked_on'] = _('Locked on ')

        dict['Closed'] = _('Closed')
        dict['Not_closed'] = _('Not closed')
        dict['Closed_on'] = _('Closed on ')

        dict['Examyear_successfully_created'] = _('The exam year is successfully created.')

        dict['Create_examyear'] = _('Create exam year')
        dict['Publish_examyear'] = _('Publish exam year')
        dict['Close_examyear'] = _('Close exam year')
        dict['Delete_examyear'] = _('Delete exam year')
        dict['Undo_publish_examyear'] = _('Undo publish exam year')
        dict['Undo_closure_examyear'] = _('Undo closure exam year')

        dict['msg_info'] = {
        'create': [
                str(_("The new exam year will be created now. The data of the schools and subjects will be copied from the previous exam year.")),
                str(_("Go to the pages 'Schools' and 'Subjects' to update the data if necessary.")),
                str(_("Then you can publish the new exam year.")),
                str(_("Schools will not be able to view the new exam year until you have published it."))
        ],
        'publish': [
            str(_("The exam year will be published now.")),
            str(_("When you have published the examyear, schools will be able to activate the new exam year and enter data.")),
            str(_("After a school has activated the new exam year, you can no longer undo the publication."))
        ],
        'close': [
            str(_("The exam year will be closed now.")),
            str(_("After you have closed the examyear, it it no longer possible to add, change or delete data.")),
            str(_("You can undo the closure of an examyear at any time."))
        ],
        'locked': [
            str(_("The exam year is closed.")),
            str(_("You can undo the closure of the examyear at any time.")),
            str(_("Click 'Undo closure exam year'."))
        ],
        }

# ====== PAGE SUBJECTS ========================= PR2020-09-30
    elif page == 'subjects':

        dict['Add_subject'] = _('Add subject')
        dict['Add_department'] = _('Add department')
        dict['Add_level'] = _('Add level')
        dict['Add_sector'] = _('Add sector')
        dict['Add_subjecttype'] = _('Add subject type')
        dict['Add_scheme'] = _('Add scheme')
        dict['Add_package'] = _('Add package')

        dict['Delete_subject'] = _('Delete subject')
        dict['Delete_department'] = _('Delete department')
        dict['Delete_level'] = _('Delete level')
        dict['Delete_sector'] = _('Delete sector')
        dict['Delete_subjecttype'] = _('Delete subject type')
        dict['Delete_scheme'] = _('Delete scheme')
        dict['Delete_package'] = _('Delete package')
        dict['Upload_subjects'] = _('Upload subjects')

        dict['Subjecttype'] = _('Subject type')
        dict['Scheme'] = _('Scheme')
        dict['Schemeitem'] = _('Scheme item')
        dict['Package'] = _('Package')
        dict['Package_item'] = _('Package item')



        dict['this_subject'] = _('this subject')
        dict['this_level'] = _('this level')
        dict['this_sector'] = _('this sector')
        dict['this_subjecttype'] = _('this subject type')
        dict['this_scheme'] = _('this scheme')
        dict['this_package'] = _('this package')

        dict['Departments_where'] = _('Departments, in which ')
        dict['occurs'] = _(' occurs')
        dict['All_departments'] = _('All departments')
        dict['already_exists_in_departments'] = _(' already exists in one of the departments.')

# ====== PAGE SCHOOLS ========================= PR2020-09-30
    elif page == 'schools':

        dict['Article'] = _('Article')
        dict['Short_name'] = _('Short name')
        dict['Activated'] = _('Activated')
        dict['Locked'] = _('Locked')
        dict['School'] = _('School')
        dict['Add_school'] = _('Add school')
        dict['Delete_school'] = _('Delete school')
        dict['No_schools'] = _('No schools')

        dict['Departments_of_this_school'] = _('Departments of this school')
        dict['All_departments'] = _('All departments')
        dict['School_code'] = _('School code')
        dict['is_too_long_max_schoolcode'] = _(" is too long. Maximum is %(max)s characters.") % {'max': c.MAX_LENGTH_SCHOOLCODE}
        dict['is_too_long_max_article'] = _(" is too long. Maximum is %(max)s characters.") % {'max': c.MAX_LENGTH_SCHOOLABBREV}
        dict['is_too_long_max_name'] = _(" is too long. Maximum is %(max)s characters.") % {'max': c.MAX_LENGTH_NAME}

# ====== PAGE STUDENTS ========================= PR2020-10-27
    elif page == 'students':

        dict['Add_candidate'] = _('Add candidate')
        dict['Delete_candidate'] = _('Delete candidate')
        dict['Upload_candidates'] = _('Upload candidates')

        dict['No_candidate_selected'] = _('No candidate selected')
        dict['This_candidate_has_nosubjects_yet'] = _('This candidate has no subjects yet.')

        dict['Examnumber_twolines'] = _('Exam\nnumber')
        dict['Last_name'] = _('Last name')
        dict['First_name'] = _('First name')
        dict['Gender'] = _('Gender')
        dict['ID_number'] = _('ID number')

        dict['Abbrev'] = _('Abbrev.')
        dict['_of_'] = _(' of ')

        dict['No_subject_selected'] = _('No subject selected.')

# - mod upload
        dict['Upload_candidates'] = _('Upload candidates')
        dict['Select_Excelfile_with_students'] = _('Select an Excel file with students:')
        dict['Select_valid_Excelfile'] = _('Please select a valid Excel file.')
        dict['Not_valid_Excelfile'] = _('This is not a valid Excel file.')
        dict['Only'] = _('Only ')
        dict['and'] = _(' and ')
        dict['are_supported'] = _(' are supported.')
        dict['No_worksheets'] = _('There are no worksheets.')
        dict['No_worksheets_with_data'] = _('There are no worksheets with data.')
        dict['coldef_list'] = [
            {'awpKey': 'custcode', 'caption': _('Customer - Short name')},
            {'awpKey': 'custname', 'caption': _('Customer - Name')},
            {'awpKey': 'custidentifier', 'caption': _('Customer - Identifier')},
            # {'awpKey': 'custcontactname', 'caption': _('Customer - Contact name')},
            # {'awpKey': 'custaddress', 'caption': _('Customer - Address')},
            # {'awpKey': 'custzipcode', 'caption': _('Customer - Zipcode')},
            # {'awpKey': 'custcity', 'caption': _('Customer - City')},
            # {'awpKey': 'custcountry', 'caption': _('Customer - Country')},
            # {'awpKey': 'custemail', 'caption': _('Customer - Email address')},
            # {'awpKey': 'custtelephone', 'caption': _('Customer - Telephone')},

            {'awpKey': 'ordercode', 'caption': _('Order - Short name')},
            {'awpKey': 'ordername', 'caption': _('Order - Name')},
            {'awpKey': 'orderidentifier', 'caption': _('Order - Identifier')},
            # {'awpKey': 'ordercontactname', 'caption': _('Order - Contact name')},
            # {'awpKey': 'orderaddress', 'caption': _('Order - Address')},
            #  {'awpKey': 'orderzipcode', 'caption': _('Order - Zipcode')},
            #  {'awpKey': 'ordercity', 'caption': _('Order - City')},
            # {'awpKey': 'ordercountry', 'caption': _('Order - Country')},
            # {'awpKey': 'orderemail', 'caption': _('Order - Email address')},
            # {'awpKey': 'ordertelephone', 'caption': _('Order - Telephone')},
            {'awpKey': 'orderdatefirst', 'caption': _('Order - First date of order')},
            {'awpKey': 'orderdatelast', 'caption': _('Order - Last date of order')}]

        #dict['The_cancicate_data_will_be_uploaded'] = _('The candidate data will be uploaded.')
        #dict['Upload_subjects'] = _('Upload subjects')
        dict['linkunique_The_field'] = _("The field ")
        dict['linkunique_One_ofthe_fields'] = _("One of the fields ")
        dict['_or_'] = _(" or ")
        dict['linkunique_mustbelinked_and_unique'] = _(" must be linked and contain unique values.")

# ====== PAGE STUDENTSUBJECTS ========================= PR2020-12-21
    elif page == 'studentsubjects':
        dict['Character'] = _('Character')
        dict['Examnumber_twolines'] = _('Exam\nnumber')
        dict['This_candidate_has_nosubjects_yet'] = _('This candidate has no subjects yet.')
        dict['No_subject_selected'] = _('No subject selected.')

        dict['Authorized_chairman'] = _('Authorized\nchairman')
        dict['Authorized_secretary'] = _('Authorized\nsecretary')
        dict['Submitted'] = _('Submitted')
        dict['Authorized_by'] = _('Authorized by')

        dict['at_'] = pgettext_lazy('at_date', 'at ')


# ====== PAGE GRADES ========================= PR2020-10-27
    elif page == 'grades':

        dict['No_candidate_selected'] = _('No candidate selected')
        dict['This_candidate_has_nosubjects_yet'] = _('This candidate has no subjects yet.')

        dict['Ex_nr'] = _('Ex.#')
        dict['Examnumber_twolines'] = _('Exam\nnumber')
        dict['Last_name'] = _('Last name')
        dict['First_name'] = _('First name')
        dict['Gender'] = _('Gender')
        dict['ID_number'] = _('ID number')

        dict['Abbrev'] = _('Abbrev.')

        dict['Character'] = _('Character')
        dict['_of_'] = _(' of ')

        dict['Score'] = _('Score')
        dict['Grade'] = _('Grade')
        dict['PE_score'] = _('PE score')
        dict['CE_score'] = _('CE score')
        dict['SE_grade'] = _('SE grade')
        dict['PE_grade'] = _('PE grade')
        dict['CE_grade'] = _('CE grade')
        dict['PECE_grade'] = _('PE-CE grade')
        dict['Final_grade'] = _('Final grade')

        dict['PE_score_twolines'] = _('PE-\nscore')
        dict['CE_score_twolines'] = _('CE-\nscore')
        dict['SE_grade_twolines'] = _('SE-\ngrade')
        dict['PE_grade_twolines'] = _('PE-\ngrade')
        dict['CE_grade_twolines'] = _('CE-\ngrade')
        dict['PECE_grade_twolines'] = _('PE-CE\ngrade')
        dict['Final_grade_twolines'] = _('Final\ngrade')

        dict['No_subject_selected'] = _('No subject selected.')

        dict['Select_examperiod'] = _('Select exam period')
        dict['No_examperiods_found'] = _('No exam periods found')
        dict['Select_examtype'] = _('Select exam type')
        dict['No_examtypes_found'] = _('No exam types found')

        # options_examperiod PR2020-12-20
        dict['options_examperiod'] = c.EXAMPERIOD_OPTIONS
        dict['options_examtype'] = c.EXAMTYPE_OPTIONS

        dict['grade_err_list'] = {
            'examyear_locked': _('The exam year is locked.'),
            'school_locked': _('The school data is locked.'),
            'candidate_locked': _('The candidate data is locked.'),
            'no_ce_this_ey': _('There are no central exams this exam year.'),
            'no_3rd_period': _('There is this exam year no third exam period.'),
            'reex_combi_notallowed': _('Combination subject has no re-examination.'),
            'exemption_no_ce': _('Exemption has no central exam this exam year.'),
            'no_pe_examyear': _('There are no practical exams this exam year.'),
            'subject_no_pe': _('This subject has no practical exam.'),
            'notallowed_in_combi': _(' not allowed in combination subject.'),
            'reex_notallowed_in_combi': _('Re-examination grade not allowed in combination subject.'),
            'weightse_is_0': _('The SE weighing of this subject is zero.\nYou cannot enter a grade.'),
            'weightce_0_noscore': _('The CE weighing of this subject is zero.\nYou cannot enter a score.'),
            'weightce_0_nograde': _('The CE weighing of this subject is zero.\nYou cannot enter a grade.'),
            'score_mustbe_number': _('The score must be a number.'),
            'score_mustbe_gt0': _('The score must be a number greater than zero.'),
            'score_mustbe_wholenumber': _('The score must be a whole number.'),
            #  strMsgText = "Cijfertype 'Geen cijfer'. Er kan geen cijfer ingevuld worden." 'PR2016-02-14
            'gradetype_none': _("Grade type has no value.\nGrades cannot be entered."),
            # //"Het cijfer kan alleen g, v of o zijn."
            'gradetype_ovg': _("Grade can only be 'g', 'v' or 'o'."),

            'is_not_allowed': _(' is not allowed.'),
            'Grade_mustbe_between_1_10': _('The grade must be a number between 1 and 10.'),
            'Grade_may_only_have_1_decimal': _('The grade may only have one digit after the dot.'),
            'Score_mustbe_between_0_and': _('The score must be a number between 0 and ')
        }
        # - mod upload


    return dict

TXT_Email_address = _('Email address')

TXT_Inactive = _("Inactive")

# get weekdays translated
TXT_weekdays_abbrev = ('', _('Mon'), _('Tue'), _('Wed'), _('Thu'), _('Fri'), _('Sat'), _('Sun'))
TXT_weekdays_long= ('', _('Monday'), _('Tuesday'), _('Wednesday'),
                       _('Thursday'), _('Friday'), _('Saturday'), _('Sunday'))
TXT_months_abbrev = ('', _('Jan'), _('Feb'), _('Mar'), _('Apr'), _('May'), _( 'Jun'),
                           _('Jul'), _('Aug'), _('Sep'), _('Oct'), _('Nov'), _('Dec'))
TXT_months_long = ('', _('January'), _( 'February'), _( 'March'), _('April'), _('May'), _('June'), _(
                         'July'), _('August'), _('September'), _('October'), _('November'), _('December'))