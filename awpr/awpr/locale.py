# PR2020-09-17

from django.utils.translation import pgettext_lazy, ugettext_lazy as _
from awpr import constants as c

import logging
logger = logging.getLogger(__name__)


# === get_locale_dict ===================================== PR2019-11-12
def get_locale_dict(table_dict, user_lang):

    #TODO use user_lang etc from settings_dict
    dict = {'user_lang': user_lang}

    page_list = table_dict.get('page')

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
    dict['a_subject'] = _('a subject')
    dict['in_the_list'] = _(' in the list.')

    dict['Please_select__'] = pgettext_lazy('Please select ... first', 'Please select ')
    dict['__first'] = pgettext_lazy('Please select ... first.', ' first.')
    dict['an_item'] = _('an item')

    dict['Select_examyear'] = _('Select an exam year')
    dict['Select_school'] = _('Select a school')
    dict['Select_department'] = _('Select a department')
    dict['No_departments_found'] = _("No departments found")

    dict['There_is_no__'] = _('There is no ')
    dict['__selected'] = _(' selected.')

    dict['No_examyear_selected'] = _('No exam year selected')
    dict['No_school'] = _('No school')
    dict['No_department_selected'] = _('No department selected')

    dict['No_examyears'] = _('No exam years')
    dict['No_schools'] = _('No schools')
    dict['No_departments'] = _('No departments')
    dict['School_has_no_departments'] = _('School has no departments')
    dict['School_notfound_thisexamyear'] = _('School not found in this exam year')
    dict['Department_notfound_thisexamyear'] = _('Department not found in this exam year')

    dict['This_school_is_locked'] = _('This school is locked.')
    dict['This_school_is_activated'] = _('This school is activated.')

    # mod confirm
    dict['will_be_deleted'] = _(' will be deleted.')
    dict['will_be_made_inactive'] = _(' will be made inactive.')
    dict['will_be_made_active'] = _(' will be made active.')
    dict['will_be_printed'] = _(' will be printed.')
    dict['Do_you_want_to_continue'] = _('Do you want to continue?')
    dict['Yes_delete'] = _('Yes, delete')
    dict['Yes_make_inactive'] = _('Yes, make inactive')
    dict['Yes_make_active'] = _('Yes, make active')
    dict['Make_inactive'] = _('Make inactive')
    dict['No_cancel'] = _('No, cancel')
    dict['Cancel'] = _('Cancel')
    dict['OK'] = _('OK')

    dict['Examyear'] = _('Exam year')

    dict['School'] = _('School')
    dict['Schools'] = _('Schools')

    dict['Subject'] = _('Subject')
    dict['Subjects'] = _('Subjects')

    dict['Subject_schemes'] = _('Subject schemes')
    dict['Level'] = _('Level')
    dict['Levels'] = _('Levels')
    dict['Sector'] = _('Sector')

    dict['Profiel'] = _('Profiel')
    dict['SectorProfiel'] = _('Sector / Profiel')
    dict['SectorenProfielen'] = _('Sectoren / Profielen')
    dict['SectorProfiel_twolines'] = _('Sector /\nProfiel')
    dict['Leerweg'] = _('Leerweg')
    dict['Leerwegen'] = _('Leerwegen')
    dict['Leerweg_twolines'] = _('Leer-\nweg')
    dict['Sectors'] = _('Sectors')
    dict['Abbreviation'] = _('Abbreviation')

    dict['Candidate'] = _('Candidate')
    dict['Candidates'] = _('Candidates')
    dict['a_candidate'] = _('a candidate')

    dict['Name'] = _('Name')
    dict['Department'] = _('Department')
    dict['Departments'] = _('Departments')
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
    dict['err_msg_and'] = TXT__and_
    dict['err_msg_must_be_number_less_than_or_equal_to'] = _(' must be a number less than or equal to ')
    dict['err_msg_must_be_number_greater_than_or_equal_to'] = _(' must be a number greater than or equal to ')

    dict['An_error_occurred'] = _('An error occurred.')

    dict['No_item_selected'] = _('No item selected')

    dict['All'] = _('All ')

# ====== PAGE UPLOAD =========================
    if 'upload' in page_list:

        dict['Upload_candidates'] = _('Upload candidates')
        dict['Upload_subjects'] = _('Upload subjects')
        dict['Upload_grades'] = _('Upload grades')
        dict['Select_Excelfile_with_students'] = _('Select an Excel file with students:')
        dict['Select_Excelfile_with_subjects'] = _('Select an Excel file with subjects:')
        dict['Select_Excelfile_with_grades'] = _('Select an Excel file with grades:')
        dict['Select_Excelfile_with_pemits'] = _('Select an Excel file with permissions:')
        dict['Select_valid_Excelfile'] = _('Please select a valid Excel file.')
        dict['Not_valid_Excelfile'] = _('This is not a valid Excel file.')
        dict['Only'] = _('Only ')
        dict['_and_'] = TXT__and_
        dict['are_supported'] = _(' are supported.')
        dict['No_worksheets'] = _('There are no worksheets.')
        dict['No_worksheets_with_data'] = _('There are no worksheets with data.')

        dict['First_select_valid_excelfile'] = _('You must select a valid Excel file before you can proceed.')

        dict['link_The_column'] = _("The AWP-column ")
        dict['link_The_columns'] = _("The AWP-columns ")
        dict['link_One_ofthe_columns'] = _("One of the columns ")
        dict['_or_'] = TXT__or_
        dict['link_mustbelinked_single_zijn'] =  pgettext_lazy('single zijn', ' must be linked.')
        dict['link_mustbelinked_plural_zijn'] =  pgettext_lazy('plural zijn', ' must be linked.')
        dict['link_mustbelinked_single_worden'] =  pgettext_lazy('single worden', ' must be linked.')
        dict['link_mustbelinked_plural_worden'] =  pgettext_lazy('plural worden', ' must be linked.')

        dict['Select_column'] = _("Select a column")
        dict['No_column_found'] = _("No column found")

        dict['Link_sectors'] = _('Link sectors')
        dict['Link_profielen'] = _('Link profielen')

# ====== PAGE USER ========================= PR2019-11-19
    if 'page_user' in page_list:

        dict['User_list'] = _('User list')
        dict['Permissions'] = _('Permissions')
        dict['Set_permissions'] = _('Set permissions')
        dict['User'] = _('User')
        dict['Read_only'] = _('Read only')
        dict['Read_only_2lines'] =  pgettext_lazy('2 lines', 'Read\nonly')
        dict['Edit'] = _('Edit')
        dict['pagelist'] = c.PAGE_LIST

        dict['President'] = TXT_President
        dict['Secretary'] = TXT_Secretary
        dict['Commissioner'] = TXT_Commissioner

        dict['Organization'] = TXT_Organization
        dict['Action'] = _('Action')
        dict['Page'] = _('Page')
        dict['on_page'] = _(' on page ')
        dict['Delete_permission'] = _('Delete permission')

        dict['Commissioner_2lines'] =  pgettext_lazy('2 lines', 'Commis-\nsioner')
        dict['Analyze'] = _('Analyze')
        dict['Administrator'] = _('Administrator')
        dict['Administrator_2lines'] =  pgettext_lazy('2 lines', 'Admini-\nstrator')
        dict['System_manager'] = _('System manager')
        dict['System_manager_2lines'] = pgettext_lazy('2 lines', 'System\nmanager')

        dict['Sysadm_cannot_delete_own_account'] = _("System administrators cannot delete their own account.")
        dict['Sysadm_cannot_remove_sysadm_perm'] = _("System administrators cannot remove their own 'system administrator' permission.")
        dict['Sysadm_cannot_set_inactive'] = _("System administrators cannot make their own account inactive.")

        dict['School_code'] = TXT_School_code
        dict['Username'] = _('Username')
        dict['Name'] = _('Name')
        dict['Email_address'] = TXT_Email_address
        dict['Linked_to_employee'] = _('Linked to employee')
        dict['Activated_on'] = _('Activated on')
        dict['Last_loggedin'] = _('Last logged in')
        dict['Add_user'] = _('Add user')
        dict['Add_user_to'] = _('Add user to ')
        dict['Delete_user'] = _('Delete user')
        dict['This_user'] = _('This user')
        dict['Submit_employee_as_user'] = _('Submit employee as user')
        dict['Submit'] = TXT_Submit
        dict['Inactive'] = TXT_Inactive

        dict['Sequence'] = TXT_Sequence
        dict['Sequence_2lines'] = TXT_Sequence_2lines

        dict['Add_permission'] = _('Add permission')
        dict['Delete_permission'] = _('Delete permission')
        dict['Upload_permissions'] = _('Upload permissions')
        dict['Download_permissions'] = _('Download permissions')

        dict['No_user_selected'] = _('Please select a user first.')
        dict['Make_user_inactive'] = _('Make user inactive')
        dict['Make_user_active'] = _('Make user active')
        dict['This_user_is_inactive'] = _('This user is inactive.')

        dict['role_caption'] = c.ROLE_DICT

        dict['msg_user_info'] = [
            str(_('Required, maximum %(max)s characters. Letters, digits and @/./+/-/_ only.') % {'max': c.USERNAME_SLICED_MAX_LENGTH}),
            str(_('Required, maximum %(max)s characters.') % {'max': c.USER_LASTNAME_MAX_LENGTH}),
            str(_('Required. It must be a valid email address.'))]

        dict['Click_to_register_new_user'] = _('Click the submit button to register the new user.')
        dict['We_will_send_an_email_to_the_new_user'] = _('We will send an email to the new user, with a link to create a password and activate the account.')

        dict['Activationlink_expired'] = _('The link to active the account is valid for 7 days and has expired.')
        dict['We_will_resend_an_email_to_user'] = _('We will email a new activation link to user')
        dict['Activation_email_not_sent'] = _('The activation email has not been sent.')

        dict['Resend_activationlink'] = _('Click to send an email with a new activation link.')
        dict['Activated'] = _('Activated')
        dict['Resend_activation_email'] = _('Resend activation email')

        dict['Yes_send_email'] = _('Yes, send email')

# ====== PAGE EXAM YEAR ========================= PR2020-10-04
    if 'page_examyear' in page_list:
        dict['Created_on'] = _('Created on ')

        dict['Published'] = _('Published')
        dict['Not_published'] = _('Not published')
        dict['Published_on'] = _('Published on ')

        dict['Activated'] = _('Activated')
        dict['Activated_on'] = _('Activated on')

        dict['Locked'] = _('Locked')
        dict['Not_locked'] = _('Not locked')
        dict['Locked_on'] = _('Locked on ')

        dict['Closed'] = _('Closed')
        dict['Not_closed'] = _('Not closed')
        dict['Closed_on'] = _('Closed on ')

        dict['Examyear_successfully_created'] = _('The exam year is successfully created.')

        dict['Create_new_examyear'] = _('Create new exam year')
        dict['Publish_examyear'] = _('Publish exam year')
        dict['Activate_examyear'] = _('Activate exam year')
        dict['Close_examyear'] = _('Close exam year')
        dict['Delete_examyear'] = _('Delete exam year')

        dict['Create_examyear_part1'] = pgettext_lazy('NL_Examenjaar', 'Create exam year ')
        dict['Create_examyear_part2'] = pgettext_lazy('NL_aanmaken', ' ')

        dict['Publish_examyear_part1'] = pgettext_lazy('NL_Examenjaar', 'Publish exam year ')
        dict['Publish_examyear_part2'] = pgettext_lazy('NL_publiceren', ' ')

        dict['Activate_examyear_part1'] = pgettext_lazy('NL_Examenjaar', 'Activate exam year ')
        dict['Activate_examyear_part2'] = pgettext_lazy('NL_activeren', ' ')

        dict['Close_examyear_part1'] = pgettext_lazy('NL_Examenjaar', 'Close exam year ')
        dict['Close_examyear_part2'] = pgettext_lazy('NL_afsluiten', ' ')

        dict['Delete_examyear_part1'] = pgettext_lazy('NL_Examenjaar', 'Delete exam year ')
        dict['Delete_examyear_part2'] = pgettext_lazy('NL_wissen', ' ')

        dict['Undo_publish_examyear'] = _('Undo publish exam year')
        dict['Undo_closure_examyear'] = _('Undo closure exam year')

        dict['msg_info'] = {
        'create': [
                str(_("The new exam year will be created now. The data of the schools and subjects will be copied from the previous exam year.")),
                str(_("WHen the new exam year is created, you can go to the pages 'Schools' and 'Subjects' to update the data if necessary.")),
                str(_("Then you can publish the new exam year by clicking the 'Publish' button.")),
                str(_("Schools will not be able to view the new exam year until you have published it."))
        ],
        'publish': [
            str(_("The exam year will be published now.")),
            str(_("When you have published the examyear, schools will be able to activate the new exam year and enter data.")),
            str(_("After a school has activated the new exam year, you can no longer undo the publication."))
        ],
        'activate': [
            str(_("The exam year will be activated now.")),
            str(_("After you have activated the examyear, you will be able to enter data."))
        ],
        'activate_nopermit': [
            str(_("You don't have permission to activate the examyear."))
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
    if 'page_subject' in page_list:

        dict['Show_hide_columns'] = _('Show or hide columns')
        dict['Add_subject'] = _('Add subject')
        dict['Add_department'] = _('Add department')
        dict['Add_level'] = _('Add level')
        dict['Add_sector'] = _('Add sector')
        dict['Add_subjecttype'] = _('Add subject type')
        dict['to_subject_scheme'] = _(' to subject scheme')

        dict['Subjecttypebase'] = _('Subject type base')
        dict['Add_subjecttypebase'] = _('Add subject type base')
        dict['Delete_subjecttypebase'] = _('Delete subject type base')

        dict['Subject_scheme'] = _('Subject scheme')
        dict['Add_subject_scheme'] = _('Add subject scheme')
        dict['Change_subjects_of_subject_scheme'] = _('Change subjects of subject scheme')
        dict['Copy_subject_scheme'] = _('Copy subject scheme')

        dict['All_subject_schemes'] = _('All subject schemes')

        dict['Change_subjecttypes_of_subject_scheme'] = _('Change subject types of subject scheme')
        dict['Delete_subject_scheme'] = _('Delete subject scheme')
        dict['Add_package'] = _('Add package')
        dict['Copy_from_previous_year'] = _('Copy from previous years')

        dict['Select_level'] = _("Select level")
        dict['No_levels_found'] = _("No levels found")
        dict['Select_sector'] = _("Select sector")
        dict['No_sectors_found'] = _("No sectors found")

        dict['Base_character'] = _("Base character")
        dict['Character_name'] = _("Character name")
        dict['Character'] = pgettext_lazy('karakter', 'Character')

        dict['Grade_type'] = _('Grade type')
        dict['Grade'] = _('Grade')

        dict['SE_weighing'] = _('SE weighing')
        dict['CE_weighing'] = _('CE weighing')
        dict['Mandatory'] = _('Mandatory')
        dict['Combination_subject'] = _('Combination subject')
        dict['Extra_count_allowed'] = _('Extra subject counts allowed')
        dict['Extra_nocount_allowed'] = _('Extra subject does not count allowed')
        dict['Elective_combi_allowed'] = _('Elective combi subject allowed')
        dict['Has_practical_exam'] = _('Has practical exam')
        dict['Has_assignment'] = _('Has assignment')
        dict['Is_core_subject'] = _('Core subject')
        dict['Is_MVT_subject'] = _('MVT subject')
        dict['Herkansing_SE_allowed'] = _('Herkansing SE allowed')
        dict['Maximum_reex'] = _('Maximum number of re-examinations')
        dict['No_third_period'] = _('Subject has no third period')
        dict['Exemption_without_CE_allowed'] = _('Exemption without CE allowed')

        dict['Delete_subject'] = _('Delete subject')
        dict['Delete_department'] = _('Delete department')
        dict['Delete_level'] = _('Delete level')
        dict['Delete_sector'] = _('Delete sector')
        dict['Delete_subjecttype'] = _('Delete subject type')
        dict['Delete_scheme'] = _('Delete scheme')
        dict['Delete_package'] = _('Delete package')
        dict['Upload_subjects'] = _('Upload subjects')

        dict['Subjecttype'] = _('Subject type')
        dict['Subjecttypes'] = _('Subject types')
        dict['Subjecttype_name'] = _('Subject type name')

        dict['Subject_scheme_name'] = _('Subject scheme name')
        dict['Download_subject_scheme'] = _('Download subject scheme')

        dict['Schemeitem'] = _('Scheme item')
        dict['Package'] = _('Package')
        dict['Package_item'] = _('Package item')
        dict['ETE_exam'] = _('ETE exam')
        dict['Added_by_school'] = _('Added by school')
        dict['Minimum_subjects'] = _('Minimum amount of subjects')
        dict['Maximum_subjects'] = _('Maximum amount of subjects')

        dict['Minimum_MVT_subjects'] = _('Minimum amount of MVT subjects')
        dict['Maximum_MVT_subjects'] = _('Maximum amount of MVT subjects')
        dict['Minimum_combi_subjects'] = _('Minimum amount of combination subjects')
        dict['Maximum_combi_subjects'] = _('Maximum amount of combination subjects')

        dict['Minimum_extra_nocount'] = _("Minimum extra subject, doesn't count")
        dict['Maximum_extra_nocount'] = _("Maximum extra subject, doesn't count")
        dict['Minimum_extra_counts'] = _("Minimum extra subject, counts")
        dict['Maximum_extra_counts'] = _("Maximum extra subject, counts")
        dict['Minimum_elective_combi'] = _("Minimum elective combi subject")
        dict['Maximum_elective_combi'] = _("Maximum elective combi subject")

        dict['Scheme_doesnthave_subjecttypes'] = _('This subject scheme does not have subject types yet.')
        dict['Close_window'] = _("Close this window, click the tab")
        dict['then_click'] = _("then click the menu button")
        dict['Enter_subject_types'] = _('and enter the subject types of this subject scheme.')

        dict['Sequence'] = TXT_Sequence
        dict['Other_languages'] = _('Other languages')
        dict['Papiamentu'] = _('Papiamentu')
        dict['English'] = _('English')
        dict['English_and_Papiamentu'] = _('English, Papiamentu')

        dict['Upload_subjects'] = _('Upload subjects')

        dict['this_subject'] = _('this subject')
        dict['this_level'] = _('this level')
        dict['this_sector'] = _('this sector')
        dict['this_subjecttype'] = _('this subject type')
        dict['this_scheme'] = _('this scheme')
        dict['this_package'] = _('this package')

        dict['Departments_with'] = _('Departments with ')
        dict['All_departments'] = _('All departments')

        dict['already_exists_in_departments'] = _(' already exists in one of the departments.')

# ====== PAGE SCHOOL ========================= PR2020-09-30
    if 'page_school' in page_list:

        dict['Article'] = _('Article')
        dict['Short_name'] = _('Short name')
        dict['Activated'] = _('Activated')
        dict['Locked'] = _('Locked')

        dict['Add_school'] = _('Add school')
        dict['Delete_school'] = _('Delete school')
        dict['No_schools'] = _('No schools')


        # options_role only used in mod_school PR2201-05-30
        dict['options_role'] = c.ROLE_OPTIONS
        dict['Organization'] = TXT_Organization
        dict['Select_organization'] = _('Select organization')
        dict['No_organizations_found'] = _('No organizations found')

        dict['Day_Evening_LEXschool'] = _('Day- / Evening- / LEX school')
        dict['Day_Eveningschool'] = _('Day- Evening school')
        dict['Day_school'] = _('Day school')
        dict['Evening_school'] = _('Evening school')
        dict['Landsexamen'] = _('Landsexamen')

        dict['Other_language'] = _('Other language')
        dict['Papiamentu'] = _('Papiamentu')
        dict['English'] = _('English')

        #dict['Departments_of_this_school'] = _('Departments of this school')
        dict['All_departments'] = _('All departments')
        dict['School_code'] = TXT_School_code
        dict['is_too_long_max_schoolcode'] = _(" is too long. Maximum is %(max)s characters.") % {'max': c.MAX_LENGTH_SCHOOLCODE}
        dict['is_too_long_max_article'] = _(" is too long. Maximum is %(max)s characters.") % {'max': c.MAX_LENGTH_SCHOOLABBREV}
        dict['is_too_long_max_name'] = _(" is too long. Maximum is %(max)s characters.") % {'max': c.MAX_LENGTH_NAME}

        dict['Upload_awpdata'] = _('Upload AWP data file')

# ====== PAGE STUDENTS ========================= PR2020-10-27
    if 'page_student' in page_list:

        dict['Add_candidate'] = _('Add candidate')
        dict['Delete_candidate'] = _('Delete candidate')
        dict['Upload_candidates'] = _('Upload candidates')

        dict['Please_select_candidate_first'] = _('Please select a candidate first.')
        dict['This_candidate_has_nosubjects_yet'] = _('This candidate has no subjects yet.')

        dict['Examnumber_twolines'] = TXT_Examnumber_twolines

        dict['Last_name'] = _('Last name')
        dict['First_name'] = _('First name')
        dict['Gender'] = _('Gender')
        dict['ID_number'] = _('ID number')

        dict['Abbrev'] = _('Abbrev.')

        dict['Class'] = _('Class')
        dict['Bis_candidate'] = _('Bis-candidate')

# ====== PAGE STUDENTSUBJECTS ========================= PR2020-12-21
    if 'page_studsubj' in page_list:
        dict['Character'] = _('Character')
        dict['Examnumber_twolines'] = TXT_Examnumber_twolines
        dict['This_candidate_has_nosubjects_yet'] = _('This candidate has no subjects yet.')
        dict['No_subject_selected'] = _('No subject selected.')

        dict['Authorized_chairman'] = _('Authorized\nchairman')
        dict['Authorized_secretary'] = _('Authorized\nsecretary')
        dict['Submitted'] = _('Submitted')
        dict['Authorized_by'] = _('Authorized by')

        dict['at_'] = pgettext_lazy('at_date', 'at ')
        dict['_of_'] = TXT__of_
        dict['_or_'] = TXT__or_

        dict['Submit_Ex1_form'] = _('Submit Ex2A form')
        dict['Approve_grades'] = _('Approve grades')
        dict['Submit_Ex1_form'] = _('Submit Ex2A form')
        dict['Preliminary_Ex1_form'] = _('Preliminary Ex1 form')
        dict['Approve'] = _('Approve')
        dict['Check_grades'] = _('Check grades')
        dict['Submit'] = TXT_Submit

        dict['MAG_info'] = {
            'subheader_approve': _('The following grades will be approved:'),
            'subheader_submit': _('An Ex2A form with the following grades will be submitted:'),
            'approve_0': _("Click 'Check grades' to check the selected grades before approving."),
            'approve_1': _('After the grades are approved by the president, secretary and commissioner,'),
            'approve_2': _('the Ex2A form can be submitted by the president or secretary.'),

            'submit_0': _("Click 'Check grades' to check the selected grades before submitting."),
            'submit_1': _("If the check is OK, click 'Submit Ex2A form' to submit the selected grades."),
            'submit_2': _("After the grades are submitted, you can only change them with permission of the Inpsection."),

            'submit_ok_01': _("The Ex2A form is succesfully created."),
        }

# ====== PAGE EXAM ========================= PR2021-04-04
    if 'page_exams' in page_list:

        dict['Exam_period'] = TXT_Exam_period
        dict['Select_examperiod'] = TXT_Select_examperiod
        dict['No_examperiods_found'] = TXT_No_examperiods_found

        dict['Exam_type'] = TXT_Exam_type
        dict['Select_examtype'] = TXT_Select_examtype
        dict['No_examtypes_found'] = TXT_No_examtypes_found

        dict['Select_subject'] = _('Select subject')
        #dict['All_levels'] = _("All 'leerwegen'")
        #dict['All_sectors'] = _("All sectors")
        #dict['All_profielen'] = _("All 'profielen'")

        dict['Select_leerweg'] = TXT_Select_leerweg
        dict['No_leerwegen_found'] = TXT_No_leerwegen_found

        dict['options_examperiod_exam'] = c.EXAMPERIOD_OPTIONS_12ONLY
        dict['examperiod_caption'] = c.EXAMPERIOD_CAPTION
        dict['options_examtype_exam'] = c.EXAMTYPE_OPTIONS_EXAM
        dict['examtype_caption'] = c.EXAMTYPE_CAPTION

        dict['All_leerwegen'] = _("All 'leerwegen'")

        dict['Exam'] = _("Exam")
        dict['Add_exam'] = _("Add exam")
        dict['Delete_exam'] = _("Delete exam")
        dict['Publish_exam'] = _("Publish exam")
        dict['Submit_exam'] = _("Submit exam")

        dict['Print_exam'] = _("Print exam")
        dict['Blanks'] = _("Blanks")
        dict['Download_PDF'] = _("Download PDF")
        dict['Download_JSON'] = _("Download JSON")

        dict['Key'] = _("Key")
        dict['Version'] = _("Version")
        dict['Quest'] = _('Quest.')
        dict['Number_of_questions'] = _('Number of questions')

        dict['Maximum_score'] = _('Maximum score')
        dict['Maximum_score_2lines'] = pgettext_lazy('2 lines', 'Maximum\nscore')
        dict['Sequence_2lines'] = TXT_Sequence_2lines

        dict['No_exam_for_this_subject'] = _("There is no exam for this subject.")

        dict['err_list'] = {
            'Amount': _("Amount"),
            'not_allowed': _(" is not allowed."),
            'Amount_cannot_be_blank': _("The amount cannot be blank."),
            'amount_mustbe_between': _('The amount must be a whole number between 1 and %(max)s.') % {'max': 100},
            'Minimum_score': _('Minimum score'),
            'Minimum_score_mustbe_lessthan_or_equalto': _('Minimum score must be less than or equal to'),
            'This_isa_multiplechoice_question': _('This is a multiple choice question.'),
            'This_isnota_multiplechoice_question': _('This is not a multiple choice question.'),
            'must_enter_whole_number_between_0_and_': _('You must enter a whole number between 0 and '),
            'must_enter_letter_between_a_and_': _("You must enter a letter between 'a' and '"),
            'or_an_x_if_blank': _("or an 'x' if the answer is blank."),
            'Character': pgettext_lazy('Teken', 'Character'),
            'already_exists': _('already exists.'),
            'exists_multiple_times': _('exists multiple times.'),
            'character_mustbe_between': _('The character must be between B and Z or between b and z.'),
            'maxscore_mustbe_between': _('The maximum score must be a whole number between 1 and 99.'),

            'key_mustbe_between_and_': _("The key must be one or more letters between 'a' and '"),
            'Exam_assignment_does_notexist': _('This exam assignment does not exist.'),
            'Contact_divison_of_exams': _('Please contact the Division of Exams.')
        }

# ====== PAGE GRADES ========================= PR2020-10-27
    if 'page_grade' in page_list:

        dict['No_candidate_selected'] = _('No candidate selected')
        dict['This_candidate_has_nosubjects_yet'] = _('This candidate has no subjects yet.')

        dict['Ex_nr'] = _('Ex.#')
        dict['Examnumber_twolines'] = TXT_Examnumber_twolines
        dict['Last_name'] = _('Last name')
        dict['First_name'] = _('First name')
        dict['Gender'] = _('Gender')
        dict['ID_number'] = _('ID number')

        dict['All_subjects'] = _('All subjects')
        dict['All_candidates'] = _('All candidates')
        dict['All_leerwegen'] = _("All 'leerwegen'")
        dict['All_subjects_and_candidates'] = _('All subjects and candidates')

        dict['Abbrev'] = _('Abbrev.')

        dict['Character'] = pgettext_lazy('karakter', 'Character')

        dict['_of_'] = TXT__of_

        dict['Name_ex_form'] = _('Name Ex form')
        dict['Date_submitted'] = _('Date submitted')
        dict['Download_Exform'] = _('Download Ex form')

        dict['examtype_caption'] = c.EXAMTYPE_CAPTION
        dict['examperiod_caption'] = c.EXAMPERIOD_CAPTION

        dict['Re_examination'] = _('Re-examination')
        dict['Re_examination_3rd_period'] = _('Re-exam third period')

        dict['Submit_Ex2A_form'] = _('Submit Ex2A form')
        dict['Approve_grades'] = _('Approve grades')
        dict['Submit_Ex2A_form'] = _('Submit Ex2A form')
        dict['Preliminary_Ex2A_form'] = _('Preliminary Ex2A form')
        dict['Approve'] = _('Approve')
        dict['Check_grades'] = _('Check grades')
        dict['Submit'] = TXT_Submit

        dict['MAG_info'] = {
            'subheader_approve': _('The following grades will be approved:'),
            'subheader_submit': _('An Ex2A form with the following grades will be submitted:'),
            'approve_0': _("Click 'Check grades' to check the selected grades before approving."),
            'approve_1': _('After the grades are approved by the president, secretary and commissioner,'),
            'approve_2': _('the Ex2A form can be submitted by the president or secretary.'),

            'submit_0': _("Click 'Check grades' to check the selected grades before submitting."),
            'submit_1': _("If the check is OK, click 'Submit Ex2A form' to submit the selected grades."),
            'submit_2': _("After the grades are submitted, you can only change them with permission of the Inpsection."),

            'submit_ok_01': _("The Ex2A form is succesfully created."),

        }

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
        dict['SECE_weighing'] = _('SE-CE\nweighing')

        dict['Final_grade_twolines'] = _('Final\ngrade')

        dict['No_subject_selected'] = _('No subject selected.')

        dict['Exam_period'] = TXT_Exam_period
        dict['Select_examperiod'] = TXT_Select_examperiod
        dict['No_examperiods_found'] = TXT_No_examperiods_found

        dict['Exam_type'] = TXT_Exam_type
        dict['Select_examtype'] = TXT_Select_examtype
        dict['No_examtypes_found'] = TXT_No_examtypes_found
        dict['All_levels'] = _("All 'leerwegen'")
        dict['All_sectors'] = _("All sectors")
        dict['All_profielen'] = _("All 'profielen'")
        dict['Attachment'] = _('Attachment')

        # options_examperiod PR2020-12-20
        dict['options_examperiod'] = c.EXAMPERIOD_OPTIONS
        dict['options_examtype'] = c.EXAMTYPE_OPTIONS

        dict['President'] = TXT_President
        dict['Secretary'] = TXT_Secretary
        dict['Commissioner'] = TXT_Commissioner
        dict['Approved_by'] = TXT_Approved_by
        dict['Submitted_by'] = TXT_Submitted_by

        dict['and'] = TXT__and_

        dict['grade_err_list'] = {
            'examyear_locked': _('The exam year is locked.'),
            'school_locked': _('The school data is locked.'),
            'candidate_locked': _('The candidate data is locked.'),
            'grade_locked': _('This grade is locked.'),
            'no_ce_this_ey': _('There are no central exams this exam year.'),
            'no_3rd_period': _('There is this exam year no third exam period.'),
            'reex_combi_notallowed': _('Combination subject has no re-examination.'),
            'exemption_no_ce': _('Exemption has no central exam this exam year.'),
            'no_pe_examyear': _('There are no practical exams this exam year.'),
            'subject_no_pe': _('This subject has no practical exam.'),
            'notallowed_in_combi': _(' not allowed in combination subject.'),
            'reex_notallowed_in_combi': _('Re-examination grade not allowed in combination subject.'),
            'weightse_is_zero': _('The SE weighing of this subject is zero.'),
            'weightce_is_zero': _('The CE weighing of this subject is zero.'),
            'cannot_enter_score': _('You cannot enter a score.'),
            'cannot_enter_grade': _('You cannot enter a grade.'),
            'score_mustbe_number': _('The score must be a number.'),
            'score_mustbe_gt0': _('The score must be a number greater than zero.'),
            'score_mustbe_wholenumber': _('The score must be a whole number.'),
            #  strMsgText = "Cijfertype 'Geen cijfer'. Er kan geen cijfer ingevuld worden." 'PR2016-02-14
            'gradetype_no_value': _('The grade type has no value.'),
            # //"Het cijfer kan alleen g, v of o zijn."
            'gradetype_ovg': _("Grade can only be 'g', 'v' or 'o'."),

            'is_not_allowed': _(' is not allowed.'),
            'Grade_mustbe_between_1_10': _('The grade must be a number between 1 and 10.'),
            'Grade_may_only_have_1_decimal': _('The grade may only have one digit after the dot.'),
            'Score_mustbe_between_0_and': _('The score must be a number between 0 and '),

            'no_permission': _("You don't have permission to enter grades."),
            'grade_approved': _('This grade has already been approved.'),
            'needs_approvals_removed': _('You have to remove the approvals first.'),
            'Then_you_can_change_it': _('Then you can change it.'),
            'grade_submitted': _('This grade has already been submitted.'),
            'need_permission_inspection': _('You can only change it with permission of the Inspection.')
        }

    dict['approve_err_list'] = {'You_have_functions': _('You have the functions of '),
                                'Only_1_allowed': _('Only 1 function is allowed. '),
                               'cannot_approve': _('You cannot approve grades.'),
                               'cannot_submit': _('You cannot approve grades.'),
                               'This_grade_is_submitted': _('This grade is submitted.'),
                               'You_cannot_remove_approval': _('You cannot remove the approval.'),
                               'This_grade_has_no_value': _('This grade has no value.'),
                               'You_cannot_approve': _('You cannot approve this grade.'),
                               'Approved_different_function': _('You have approved this grade already in a different function.'),
                               'You_cannot_approve_again': _('You cannot approve this grade again.'),


                                }

    if 'page_orderlist' in page_list:
        dict['School_code'] = TXT_School_code
        dict['School_name'] = _('School name')
        dict['Subject'] = _('Subject')
        dict['Amount'] = _('Amount')
        dict['Submitted'] = _('Submitted')
        dict['Download_orderlist_ETE'] = _('Download ETE orderlist')
        dict['Download_orderlist_DUO'] = _('Download DUO orderlist')

        dict['Language'] = _('Language')

    return dict


TXT_School_code = _('School code')
TXT_Organization = _('Organization')

TXT_Examnumber_twolines = _('Exam\nnumber')

TXT_Exam_period = _('Exam period')
TXT_Select_examperiod = _('Select exam period')
TXT_No_examperiods_found = _('No exam periods found')

TXT_Exam_type = _('Exam type')
TXT_Select_examtype = _('Select exam type')
TXT_No_examtypes_found = _('No exam types found')

TXT_Select_leerweg = _("Select a 'leerweg'")
TXT_No_leerwegen_found = _("No 'leerwegen' found")

TXT_Email_address = _('Email address')

TXT_Inactive = _("Inactive")

TXT_President = _('President')
TXT_Secretary = _('Secretary')
TXT_Commissioner = _('Commissioner')
TXT__of_ = _(' of ')
TXT_Submit = _('Submit')

TXT_Approved_by = _('Approved by')
TXT_Submitted_by = _('Submitted by')

TXT__and_ = _(' and ')
TXT__or_ = _(" or ")

TXT_Sequence = _('Sequence')
TXT_Sequence_2lines =  pgettext_lazy('2 lines', 'Sequence')

# get weekdays translated
TXT_weekdays_abbrev = ('', _('Mon'), _('Tue'), _('Wed'), _('Thu'), _('Fri'), _('Sat'), _('Sun'))
TXT_weekdays_long= ('', _('Monday'), _('Tuesday'), _('Wednesday'),
                       _('Thursday'), _('Friday'), _('Saturday'), _('Sunday'))
TXT_months_abbrev = ('', _('Jan'), _('Feb'), _('Mar'), _('Apr'), _('May'), _( 'Jun'),
                           _('Jul'), _('Aug'), _('Sep'), _('Oct'), _('Nov'), _('Dec'))
TXT_months_long = ('', _('January'), _( 'February'), _( 'March'), _('April'), _('May'), _('June'), _(
                         'July'), _('August'), _('September'), _('October'), _('November'), _('December'))