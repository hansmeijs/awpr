# PR2020-09-17

from django.utils.translation import pgettext_lazy, ugettext_lazy as _
from awpr import constants as c

import logging
logger = logging.getLogger(__name__)


# === get_locale_dict ===================================== PR2019-11-12
def get_locale_dict(table_dict, user_lang, request):

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
    dict['No_department_found'] = _("No department found")
    dict['Select_level'] =  _("Select a learning path")
    dict['All_levels'] = _("All learning paths")
    dict['No_level_found'] = _("No learning paths found")
    dict['Select_sector'] = _("Select a sector")
    dict['All_sectors'] = _("All sectors")
    dict['No_sector_found'] = _("No sector found")
    dict['All_profielen'] = _("All 'profielen'")
    dict['No_profiel_found'] = _("No 'profiel' found")
    dict['All_sectors_profielen'] = _("All sectors / profielen")
    dict['All_sectors_profielen'] = _("All sectors / profielen")

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

    dict['This_examyear'] = _('This exam year')
    dict['This_school'] = _('This school')
    dict['is_locked'] = _(' is locked.')
    dict['is_activated'] = _(' is activated.')
    dict['You_cannot_make_changes'] = _('You cannot make changes.')

    dict['Hide_columns'] = _('Hide columns')

    # mod confirm
    dict['will_be_deleted'] = pgettext_lazy('singular', ' will be deleted.')
    dict['will_be_made_inactive'] = pgettext_lazy('singular', ' will be made inactive.')
    dict['will_be_made_active'] = pgettext_lazy('singular', ' will be made active.')
    dict['will_be_printed'] = pgettext_lazy('singular', ' will be printed.')
    dict['will_be_downloaded'] = pgettext_lazy('singular', ' will be downloaded.')
    dict['Copy_to_examyear'] = _('Copy to examyear')

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
    dict['Cluster'] = _('Cluster')

    dict['Total'] = _('Total')
    dict['Candidate'] = _('Candidate')
    dict['Candidates'] = _('Candidates')
    dict['a_candidate'] = _('a candidate')

    dict['Clusters'] = _('Clusters')

    dict['Name'] = _('Name')
    dict['Department'] = _('Department')
    dict['Departments'] = _('Departments')
    dict['Inactive'] = _('Inactive')
    dict['Last_modified_on'] = _('Last modified on ')
    dict['Last_modified'] = _('Last modified ')
    dict['on'] = _('on ')
    dict['by'] = _(' by ')

    dict['School_exam'] = _('School exam')
    dict['School_exam_2lines'] = _('School\nexam')
    dict['Central_exam'] = _('Central exam')
    dict['Exemption'] = _('Exemption')
    dict['Exemptions'] = _('Exemptions')
    dict['Re_exam_schoolexam_2lns'] = _('Re-exam\nschool exam')
    dict['Re_examination'] = _('Re-examination')
    dict['Re_examinations'] = _('Re-examinations')
    dict['Re_examination_3rd_period'] = _('Re-exam third period')
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
        dict['Upload_usernames'] = _('Upload usernames')
        dict['Upload_permissions'] = _('Upload permissions')
        dict['Upload_awpdata'] = _('Upload AWP data file')
        dict['Upload_subjects'] = _('Upload subjects')

        dict['Step'] = _('Step')
        dict['Select_grade_type'] = _('Select grade type')
        dict['Select_file'] = _('Select file')
        dict['Link_colums'] = _('Link colums')
        dict['Link_data'] = _('Link data')
        dict['Test_upload'] = _('Test upload')
        dict['Upload_data'] = _('Upload data')

        dict['Select_Excelfile_with_students'] = _('Select an Excel file with students')
        dict['Select_Excelfile_with_subjects'] = _('Select an Excel file with subjects')
        dict['Select_Excelfile_with_grades'] = _('Select an Excel file with grades')
        dict['Select_Excelfile_with_permits'] = _('Select an Excel file with permissions')
        dict['Select_Excelfile_with_usernames'] = _('Select an Excel file with usernames')
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
        dict['No_data_found'] = _('No data found.')

        dict['Link_sectors'] = _('Link sectors')
        dict['Link_profielen'] = _('Link profielen')
        dict['examgrade_options'] = c.EXAMGRADE_OPTIONS
        dict['No_examgradetypes_found'] = _('No exam grade types found')
        dict['Select_examgradetype'] = _('Please select an exam grade type')


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


        dict['Organization'] = TXT_Organization
        dict['Action'] = _('Action')
        dict['Page'] = _('Page')
        dict['on_page'] = _(' on page ')
        dict['Delete_permission'] = _('Delete permission')

        dict['President'] = TXT_President
        dict['Secretary'] = TXT_Secretary
        dict['Commissioner'] = TXT_Commissioner
        dict['Commissioner_2lines'] =  pgettext_lazy('2 lines', 'Commis-\nsioner')
        dict['Examinator'] = TXT_Examinator
        dict['Teacher'] =  _('Teacher')
        dict['Analyze'] = _('Analyze')
        dict['System_administrator'] = _('System administrator')
        dict['System_administrator_2lines'] = pgettext_lazy('2 lines', 'System\nadministrator')

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
        dict['Create_user_account'] = _('Create user account')
        dict['Inactive'] = TXT_Inactive

        dict['Sequence'] = TXT_Sequence
        dict['Sequence_2lines'] = TXT_Sequence_2lines

        dict['Add_permission'] = _('Add permission')
        dict['Delete_permission'] = _('Delete permission')
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
        dict['We_will_send_an_email_to_user'] = _('We will email an activation link to user')
        dict['Activation_email_not_sent'] = _('The activation email has not been sent.')

        dict['Send_activationlink'] = _('Click to send an email with an activation link.')
        dict['Activated'] = _('Activated')
        dict['Send_activation_email'] = _('Send activation email')

        dict['Yes_send_email'] = _('Yes, send email')

# ====== PAGE EXAM YEAR ========================= PR2020-10-04
    if 'page_examyear' in page_list:
        dict['Created_at'] = _('Created at ')

        dict['Published'] = _('Published')
        dict['Not_published'] = _('Not published')
        dict['Published_at'] = _('Published at ')

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
        dict['Copy_examyear_to_SXM'] = _('Copy exam year to SXM')
        dict['Delete_subjects_from_SXM'] = _('Delete subjects from SXM')

        dict['_of_'] = TXT__of_

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

        dict['will_be_copid_to_sxm'] = pgettext_lazy('singular', ' will be copied to SXM.')
        dict['Yes_copy'] = _('Yes, copy')
        dict['Edit_examyear'] = _('Edit examyear')

        dict['Copy_subject_schemes'] = _('Copy subject schemes')
        dict['Subjectschemes_of_ey_willbe_copiedto_ey'] = _('Subject schemes of this exam year will be copied<br>to exam year')


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
        'nopermit': [
            str(_("You don't have permission to activate the examyear.")),
            str(_("You don't have permission to edit this exam year."))
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
        'edit': [
            str(_("You don't have permission to edit this exam year.")),
        ],
        }

# ====== PAGE MAILBOX ========================= PR2021-09-12
    if 'page_mailbox' in page_list:

        dict['Sender'] = _('Sender')
        dict['Organization'] = TXT_Organization
        dict['User'] = _('User')
        dict['Usergroup'] = _('Usergroup')
        dict['From'] = _('From')
        dict['Subject'] = pgettext_lazy('onderwerp', ' Subject')

        dict['Sent_to'] = _('Sent to')
        dict['Date_sent'] = _('Date sent')
        dict['Attn'] = _('Attn.')
        dict['Attachment'] = _('Attachment')

        dict['Status'] = _('Status')
        dict['Create_new_message'] = _('Create new message')
        dict['Mailing_list'] = _('Mailing list')
        dict['Mailing_lists'] = _('Mailing lists')
        dict['Name_of_the_mailinglist'] = _('The name of the mailing list')
        dict['For_general_use'] = _('For general use')
        dict['Mailinglist_canbe_used_byallusers'] = _('This mailing list is available to all users of your organization.')

        dict['There_are_no_'] = _('There are no ')

        dict['Create_new_mailing_list'] = _('Create new mailing list')
        dict['Delete_mailing_list'] = _('Delete mailing list')
        dict['is_general_mailinglist'] = _('is a general mailing list.')
        dict['canbe_usedby_allusers'] = _('It can be used by all users of your organization.')
        dict['Areyousure_youwantto_delete'] = _('Are you sure you want to delete this mailing list?')
        dict['Can_only_delete_by_sysadm'] = _('It can only be deleted by the system administrator.')

        dict['Message'] = _('Message')
        dict['Messages'] = _('Messages')

        dict['Select_a_user'] = _('Select a user')

        dict['Title_cannot_be_blank'] = _('The title of the message cannot be blank.')
        dict['Text_cannot_be_blank'] = _('The text of the message cannot be blank.')
        dict['Mesage_musthave_atleast_one_recipient'] = _('The message must have at least one recipient.')
        dict['Mailinglist_musthave_atleast_one_recipient'] = _('The mailing list must have at least one recipient.')

        dict['Upload_attachment'] = _('Upload attachment')
        dict['Attachment_too_large'] = _('The attachment is too large.')
        dict['Maximum_size_is'] = _('The maximum size is ')

        dict['Selected'] = _('Selected')
        dict['Available'] = _('Available')
        dict['Organizations'] = _('Organizations')
        dict['Users'] = _('Users')
        dict['Usergroups'] = _('User groups')

        dict['Include_users_of_'] = _('Include users of ')
        dict['Include'] = _('Include')

        dict['_of_'] = TXT__of_
        # dict['With_Kind_Regards'] = _('With Kind Regards')

        dict['Delete_this_message'] = _('Delete this message')
        dict['Undelete_this_message'] = _('Undelete this message')
        # Delete this message

# ====== PAGE SUBJECTS ========================= PR2020-09-30
    if 'page_subject' in page_list:

        dict['Add_subject'] = _('Add subject')
        dict['Add_department'] = _('Add department')
        dict['Add_level'] = _('Add level')
        dict['Add_sector'] = _('Add sector')
        dict['Add_subjecttype'] = _('Add character')
        dict['to_subject_scheme'] = _(' to subject scheme')

        dict['Subjecttypebase'] = _('Character base')
        dict['Add_subjecttypebase'] = _('Add character base')
        dict['Delete_characterbase'] = _('Delete character base')

        dict['Subject_scheme'] = _('Subject scheme')
        dict['Add_subject_scheme'] = _('Add subject scheme')
        dict['Change_subjects_of_subject_scheme'] = _('Change subjects of subject scheme')
        dict['Copy_subject_scheme'] = _('Copy subject scheme')

        dict['All_subject_schemes'] = _('All subject schemes')

        dict['Change_characters_of_subject_scheme'] = _('Change characters of subject scheme')
        dict['Delete_subject_scheme'] = _('Delete subject scheme')
        dict['Add_package'] = _('Add package')
        dict['Copy_from_previous_year'] = _('Copy from previous years')

        dict['Base_character'] = _("Base character")
        dict['Character_name'] = _("Character name")
        dict['Character'] = pgettext_lazy('karakter', 'Character')

        dict['Grade_type'] = _('Grade type')
        dict['Grade'] = _('Grade')

        dict['SE_weighing'] = _('SE weighing')
        dict['CE_weighing'] = _('CE weighing')
        dict['Counts_double'] = _('Counts double')
        dict['Mandatory'] = _('Mandatory')
        dict['Mandatory_if_subject'] = _("'Mandatory-if' subject")
        dict['Mandatory_if_subject_info'] = _("Subject is only mandatory if the candidate has this 'Mandatory-if' subject.")

        dict['Combination_subject'] = _('Combination subject')
        dict['Extra_count_allowed'] = _('Extra subject counts allowed')
        dict['Extra_nocount_allowed'] = _('Extra subject does not count allowed')
        dict['Has_practical_exam'] = _('Has practical exam')
        dict['Has_assignment'] = _('Has assignment')
        dict['Is_core_subject'] = _('Core subject')
        dict['Is_MVT_subject'] = _('MVT subject')
        dict['Is_wiskunde_subject'] = _('Wiskunde subject')

        # NIU: dict['Final_grade_rule_Vsbo'] = _('Final grade rule Vsbo')
        # NIU: dict['Final_grade_rule_HavoVwo'] = _('Final grade rule Havo Vwo')
        dict['Average_CE_grade_rule'] = _('Average CE grade rule')
        dict['Subject_must_be_sufficient'] = _('Subject must be sufficient')
        dict['Core_subject_rule'] = _('Core subject rule')


        dict['Not_at_evening_lex_school'] = _('Not at eveningschool or landsexamen')

        dict['Herkansing_SE_allowed'] = _('Herkansing SE allowed')
        dict['Maximum_reex'] = _('Maximum number of re-examinations')
        dict['No_third_period'] = _('Subject has no third period')
        dict['Exemption_without_CE_allowed'] = _('Exemption without CE allowed')

        dict['Delete_subject'] = _('Delete subject')
        dict['Delete_department'] = _('Delete department')
        dict['Delete_level'] = _('Delete level')
        dict['Delete_sector'] = _('Delete sector')
        dict['Delete_character'] = _('Delete character')
        dict['Delete_scheme'] = _('Delete scheme')
        dict['Delete_package'] = _('Delete package')

        dict['Character'] = _('Character')
        dict['Characters'] = _('Characters')
        dict['Character_name'] = _('Character name')

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
        dict['Minimum_Wisk_subjects'] = _('Minimum amount of Wiskunde subjects')
        dict['Maximum_Wisk_subjects'] = _('Maximum amount of Wiskunde subjects')
        dict['Minimum_combi_subjects'] = _('Minimum amount of combination subjects')
        dict['Maximum_combi_subjects'] = _('Maximum amount of combination subjects')

        dict['Minimum_extra_nocount'] = _("Minimum extra subject, doesn't count")
        dict['Maximum_extra_nocount'] = _("Maximum extra subject, doesn't count")
        dict['Minimum_extra_counts'] = _("Minimum extra subject, counts")
        dict['Maximum_extra_counts'] = _("Maximum extra subject, counts")

        dict['Scheme_doesnthave_subjecttypes'] = _('This subject scheme does not have characters yet.')
        dict['Close_window'] = _("Close this window, click the tab")
        dict['then_click'] = _("then click the menu button")
        dict['Enter_subject_types'] = _('and enter the subject types of this subject scheme.')

        dict['Sequence'] = TXT_Sequence
        dict['Other_languages'] = _('Other languages')
        dict['Papiamentu'] = _('Papiamentu')
        dict['English'] = _('English')
        dict['English_and_Papiamentu'] = _('English, Papiamentu')


        dict['this_subject'] = _('this subject')
        dict['this_level'] = _('this level')
        dict['this_sector'] = _('this sector')
        dict['this_subjecttype'] = _('this character')
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


        # options_role only used in mod_school PR2021-05-30 PR2021-08-05
        dict['options_role'] = c.get_role_options(request)
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
        dict['Not_on_DUOorderlist_2lines'] = _('Not on \nDUO-orderlist')

        #dict['Departments_of_this_school'] = _('Departments of this school')
        dict['All_departments'] = _('All departments')
        dict['School_code'] = TXT_School_code
        dict['is_too_long_max_schoolcode'] = _(" is too long. Maximum is %(max)s characters.") % {'max': c.MAX_LENGTH_SCHOOLCODE}
        dict['is_too_long_max_article'] = _(" is too long. Maximum is %(max)s characters.") % {'max': c.MAX_LENGTH_SCHOOLABBREV}
        dict['is_too_long_max_name'] = _(" is too long. Maximum is %(max)s characters.") % {'max': c.MAX_LENGTH_NAME}


# ====== PAGE STUDENTS ========================= PR2020-10-27
    if 'page_student' in page_list:

        dict['Add_candidate'] = _('Add candidate')
        dict['Delete_candidate'] = _('Delete candidate')

        dict['Please_select_candidate_first'] = _('Please select a candidate first.')
        dict['This_candidate_has_nosubjects'] = TXT_This_candidate_has_no_subjects

        dict['Examnumber'] = TXT_Examnumber
        dict['Examnumber_twolines'] = TXT_Examnumber_twolines
        dict['Regnumber'] = TXT_Regnumber
        dict['Regnumber_twolines'] = TXT_Regnumber_twolines

        dict['Prefix'] = TXT_Prefix
        dict['Prefix_twolines'] = TXT_Prefix_twolines

        dict['Last_name'] = _('Last name')
        dict['First_name'] = _('First name')
        dict['Gender'] = _('Gender')
        dict['ID_number'] = _('ID number')

        dict['Abbrev'] = _('Abbrev.')

        dict['Class'] = _('Class')
        dict['Bis_candidate'] = _('Bis-candidate')
        dict['Partial_exam'] = _('Partial exam')
        dict['Additional_exam'] = _('Additional exam')

        dict['Schemes_of_candidates_willbe_validated'] = _('Schemes of candidates will be validated.')
        dict['Validate_candidate_schemes'] = _('Validate candidate schemes')
        dict['Correct_candidate_schemes'] = _('Correct candidate schemes')
        dict['Schemes_of_candidates_willbe_corrected'] = _('Schemes of candidates will be corrected.')

# ====== PAGE STUDENTSUBJECTS ========================= PR2020-12-21
    if 'page_studsubj' in page_list:
        dict['Character'] = _('Character')
        dict['Examnumber'] = TXT_Examnumber
        dict['Examnumber_twolines'] = TXT_Examnumber_twolines

        dict['Abbreviation_twolines'] = _('Abbre-\nviation')
        dict['Exemption_year'] = _('Exemption year')
        dict['Exemption_year_twolines'] = _('Exemption-\nyear')

        dict['This_candidate_has_nosubjects'] = TXT_This_candidate_has_no_subjects
        dict['No_subject_selected'] = _('No subject selected.')
        dict['validation_error'] = _('The composition of the subjects is not correct')

        dict['All_subjects'] = TXT_All_subjects
        dict['All_candidates'] = TXT_All_candidates

        dict['Notes'] = _('Notes')

        dict['mandatory_subject'] = _('mandatory subject')
        dict['combination_subject'] = _('combination subject')

        dict['Authorized_chairman'] = _('Authorized\nchairman')
        dict['Authorized_secretary'] = _('Authorized\nsecretary')
        dict['Submitted'] = _('Submitted')
        dict['Authorized_by'] = _('Authorized by')
        dict['Submitted_at'] = _('Submitted at')

        dict['President'] = TXT_President
        dict['Secretary'] = TXT_Secretary

        dict['Function'] = TXT_Function
        dict['at_'] = pgettext_lazy('at_date', 'at ')
        dict['_of_'] = TXT__of_
        dict['_or_'] = TXT__or_
        dict['_for_'] = TXT__for_

        dict['Approve_subjects'] = _('Approve subjects')
        dict['Apply_verificationcode'] = _('Apply verificationcode')
        dict['Submit_Ex1_form'] = _('Submit Ex1 form')

        dict['Preliminary_Ex1_form'] = _('Preliminary Ex1 form')
        dict['The_preliminary_Ex1_form'] = _('The preliminary Ex1 form')
        dict['Download_Ex_form'] = _('Download Ex form')
        dict['Approve'] = _('Approve')
        dict['Check_grades'] = _('Check grades')
        dict['Submit'] = TXT_Submit
        dict['Approved_by'] = TXT_Approved_by
        dict['_by_'] = TXT__by_

        dict['Approved'] = _('Approved')
        dict['Name_ex_form'] = TXT_Name_ex_form
        dict['Exam_period'] = TXT_Exam_period
        dict['examperiod_caption'] = c.EXAMPERIOD_CAPTION
        dict['Date_submitted'] = TXT_Date_submitted
        dict['Download_Exform'] = TXT_Download_Exform

        dict['Show_all_matching_candidates'] = _('Show all matching candidates')
        dict['Hide_linked_candidates'] = _('Hide linked candidates')

        dict['Delete_exemption'] = _('Delete exemption')
        dict['Delete_reex_schoolexam'] = _('Delete re-examination school exam')
        dict['Delete_reexamination'] = _('Delete re-examination ')
        dict['Delete_reexamination_3rd_period'] = _('Delete re-examination 3rd exam period')

        dict['This_subject'] = _('This subject')
        dict['This_exemption'] = _('This exemption')
        dict['This_reex_schoolexam'] = _('This re-examination school exam')
        dict['This_reexamination'] = _('This re-examination')
        dict['This_reexamination_3rd_period'] = _('This re-examination 3rd exam period')
        dict['This_proof_of_knowledge'] = _('This proof of knowledge')
        dict['This_item'] = _('This item')
        dict['is_already_published'] = _('is already published.')
        dict['You_cannot_change_approval'] = _('You cannot change the approval.')

        dict['This_subject_ismarked_fordeletion'] = _('This subject is marked for deletion.')
        dict['You_must_submit_additional_ex1form'] = _('You must submit an additional Ex-1 form to delete it.')

        dict['MASS_info'] = {
            'checking_studsubj': _('The subjects of the candidates are checked'),
            'subheader_approve': _('Selection of the subjects, that will be approved:'),
            'subheader_submit': _('An Ex1form with the following subjects will be submitted:'),
            'approve_0': _("Click 'Check subjects' to check the selected subjects before approving."),
            'approve_1': _('After the subjects are approved by the president and secretary,'),
            'approve_2': _('the Ex1 form can be submitted by the president or secretary.'),

            'submit_0': _("Click 'Check subjects' to check the selected subjects before submitting."),
            'submit_1': _("If the check is OK, click 'Submit Ex1 form' to submit the selected subjects."),
            'submit_2': _("After the subjects are submitted, you can change them by submitting an additional Ex1 form."),

            'approving_studsubj': _('AWP is approving the subjects of the candidates'),
            'requesting_verifcode': _('AWP is sending an email with the verification code'),
            'creating_Ex1_form': _("AWP is creating the Ex1 form"),
            'submit_ok_01': _("The Ex2A form is succesfully created."),
        }
        # Ex3 modal

        dict['Ex3'] = _('Ex3')
        dict['Ex3_form'] = _('Ex3 Proces Verbaal')
        dict['Proces_verbaal_van_Toezicht'] = _('Proces-verbaal van Toezicht')
        dict['No_studenst_with_subjects'] = _('There are no candidates with subjects.')
        dict['No_studenst_examperiod_02'] = _('There are no re-examination candidates.')
        dict['No_studenst_examperiod_03'] = _('There are no re-examination candidates in the third exam period.')
        dict['Please_select_one_or_more_subjects'] = _('Please select one or more subjects')
        dict['from_available_list'] = _('from the list of available subjects.')

        dict['No_permission'] = _("You don't have permission to edit this subject.")
        dict['Exemption_is_auth'] = _("This exemption has already been approved.")
        dict['needs_approvals_removed'] = _("You have to remove the approvals first.")
        dict['Then_you_can_change_it'] = _("Then you can change it.")
        dict['Then_you_can_change_it'] = _("Then you can change it.")
        dict['Exemption_submitted'] = _("This exemption has already been submitted.")
        dict['need_permission_inspection'] = _("You can only change it with permission of the Inspection.")

        dict['Examyear_not_valid'] = _("This exam year is not valid.")
        dict['Exemption_year'] = _("Exemption year")

# ====== PAGE EXAM ========================= PR2021-04-04
    if 'page_exams' in page_list:

        dict['Exam_period'] = TXT_Exam_period
        dict['Select_examperiod'] = TXT_Select_examperiod
        dict['No_examperiods_found'] = TXT_No_examperiods_found

        dict['Exam_type'] = TXT_Exam_type
        dict['Select_examtype'] = TXT_Select_examtype
        dict['No_examtypes_found'] = TXT_No_examtypes_found

        dict['Select_subject'] = _('Select subject')

        dict['options_examperiod_exam'] = c.EXAMPERIOD_OPTIONS_12ONLY
        dict['examperiod_caption'] = c.EXAMPERIOD_CAPTION
        dict['options_examtype_exam'] = c.EXAMTYPE_OPTIONS_EXAM
        dict['examtype_caption'] = c.EXAMTYPE_CAPTION

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
        dict['This_candidate_has_nosubjects'] = TXT_This_candidate_has_no_subjects


        dict['Please_select_one_or_more_subjects'] = _('Please select one or more subjects')
        dict['from_available_list'] = _('from the list of available subjects.')

        dict['Ex_nr'] = _('Ex.#')
        dict['Examnumber'] = TXT_Examnumber
        dict['Examnumber_twolines'] = TXT_Examnumber_twolines
        dict['Last_name'] = _('Last name')
        dict['First_name'] = _('First name')
        dict['Gender'] = _('Gender')
        dict['ID_number'] = _('ID number')

        dict['All_subjects'] = TXT_All_subjects
        dict['All_candidates'] = TXT_All_candidates
        dict['All_subjects_and_candidates'] = _('All subjects and candidates')

        dict['Abbrev'] = _('Abbrev.')

        dict['Character'] = pgettext_lazy('karakter', 'Character')

        dict['_of_'] = TXT__of_

        dict['Name_ex_form'] = TXT_Name_ex_form
        dict['Date_submitted'] = TXT_Date_submitted
        dict['Download_Exform'] = TXT_Download_Exform

        dict['examtype_caption'] = c.EXAMTYPE_CAPTION
        dict['examperiod_caption'] = c.EXAMPERIOD_CAPTION

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

        dict['Herkansing_SE_grade_2lines'] = _('Herkansing\nschool exam')
        dict['Re-examination_score'] = _('Re-examination\nscore')
        dict['Re-examination_grade'] = _('Re-examination\ngrade')
        dict['Third_period_score'] = _('Third period\nscore')
        dict['Third_period_grade'] = _('Third period\ngrade')

        dict['PE_score_twolines'] = _('PE-\nscore')
        dict['CE_score_twolines'] = _('CE-\nscore')
        dict['SE_grade_twolines'] = _('SE-\ngrade')
        dict['PE_grade_twolines'] = _('PE-\ngrade')
        dict['CE_grade_twolines'] = _('CE-\ngrade')
        dict['PECE_grade_twolines'] = _('PE-CE\ngrade')
        dict['SECE_weighing'] = _('SE-CE\nweighing')
        dict['Final_grade_twolines'] = _('Final\ngrade')

        dict['Abbreviation_subject'] = '\n'.join((str(_('Abbreviation')), str(_('subject'))))
        dict['Exemption_SE'] = ' '.join((str(_('Exemption')), str(_('SE-grade'))))
        dict['Exemption_CE'] = ' '.join((str(_('Exemption')), str(_('CE-grade'))))
        dict['Exemption_FINAL'] = ' '.join((str(_('Exemption')), str(_('Final grade'))))
        dict['Exem_SE_twolines'] = '\n'.join((str(_('Exemption')), str(_('SE-grade'))))
        dict['Exem_CE_twolines'] = '\n'.join((str(_('Exemption')), str(_('CE-grade'))))
        dict['Exem_FINAL_twolines'] = '\n'.join((str(_('Exemption')), str(_('Final grade'))))

        dict['Examnumber'] = TXT_Examnumber
        dict['Notes'] = _('Notes')

        dict['No_subject_selected'] = _('No subject selected.')

        dict['Exam_period'] = TXT_Exam_period
        dict['Select_examperiod'] = TXT_Select_examperiod
        dict['No_examperiods_found'] = TXT_No_examperiods_found

        dict['Exam_type'] = TXT_Exam_type
        dict['Select_examtype'] = TXT_Select_examtype
        dict['No_examtypes_found'] = TXT_No_examtypes_found

        dict['Attachment'] = _('Attachment')

        # options_examperiod PR2020-12-20
        dict['options_examperiod'] = c.EXAMPERIOD_OPTIONS
        dict['options_examtype'] = c.EXAMTYPE_OPTIONS

        dict['President'] = TXT_President
        dict['Secretary'] = TXT_Secretary
        dict['Commissioner'] = TXT_Commissioner
        dict['Examinator'] = TXT_Examinator
        dict['Approved_by'] = TXT_Approved_by
        dict['Submitted_by'] = TXT_Submitted_by

        dict['and'] = TXT__and_

        dict['grade_err_list'] = {
            'examyear_locked': _('The exam year is locked.'),
            'school_locked': _('The school data is locked.'),
            'candidate_locked': _('The candidate data is locked.'),
            'grade_locked': _('This grade is locked.'),
            'no_ce_this_ey': _('There are no central exams this exam year.'),
            'no_3rd_period': _('This exam year has no third period.'),
            'reex_combi_notallowed': _('Combination subject has no re-examination.'),
            'exemption_no_ce': _('Exemption has no central exam this exam year.'),
            'no_pe_examyear': _('There are no practical exams this exam year.'),
            'subject_no_pe': _('This subject has no practical exam.'),
            'notallowed_in_combi': _(' not allowed in combination subject.'),
            'reex_notallowed_in_combi': _('Re-examination grade not allowed in combination subject.'),
            'weightse_is_zero': _('The SE weighing of this subject is zero.'),
            'weightce_is_zero': _('This subject has no central exam.'),
            'cannot_enter_SE_grade': _('You cannot enter a SE grade.'),
            'cannot_enter_SR_grade': _("You cannot enter a 'herkansing' of the school exam."),
            'cannot_enter_PE_grade': _('You cannot enter a grade of the practical exam.'),
            'cannot_enter_CE_grade': _('You cannot enter a CE grade.'),
            'cannot_enter_PE_score': _('You cannot enter a score of the practical exam.'),
            'cannot_enter_CE_score': _('You cannot enter a CE score.'),

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
                               'cannot_submit': _('You cannot submit grades.'),
                               'This_grade_is_submitted': _('This grade is submitted.'),
                               'You_cannot_change_approval': _('You cannot change the approval.'),
                               'This_grade_has_no_value': _('This grade has no value.'),
                               'You_cannot_approve': _('You cannot approve this grade.'),
                               'Approved_different_function': _('You have approved this grade already in a different function.'),
                               'You_cannot_approve_again': _('You cannot approve this grade again.'),
        }

# ====== PAGE RESULTS ========================= PR2021-11-15
    if 'page_result' in page_list:
        dict['Results'] = _('Results')
        dict['Result'] = _('Result')
        dict['Preliminary_gradelist'] = _('Preliminary grade list')
        dict['Download_gradelist'] = _('Download grade list')

        dict['The_preliminary_gradelist_of'] = _('The preliminary grade list of')
        dict['The_final_gradelist_of'] = _('The final grade list of')
        dict['candidates'] = _(' candidates')

        dict['will_be_downloaded'] = _('will be downloaded.')
        dict['Select_a_president'] = _('Select a president')
        dict['Select_a_secretary'] = _('Select a secretary')
        dict['No_president'] = _('There is no president')
        dict['No_secretary'] = _('There is no secretary')

        dict['Calc_result'] = _('Calculate result')

# ====== PAGE ORDERLIST =========================
    if 'page_orderlist' in page_list:
        dict['School_code'] = TXT_School_code
        dict['School_name'] = _('School name')
        dict['Activated'] = _('Activated')
        dict['Number_of_candidates'] = _('Number of candidates')
        dict['Number_of_entered_subjects'] = _('Number of entered subjects')
        dict['Number_of_submitted_subjects'] = _('Number of submitted subjects')
        dict['Date_submitted'] = _('Date submitted')

        dict['Preliminary_orderlist'] = _('Preliminary orderlist')
        dict['The_preliminary_orderlist'] = _('The preliminary orderlist')
        dict['Downlaod_preliminary_orderlist'] = _('Download preliminary orderlist')
        dict['per_school'] = _(' per school')

        dict['Publish_orderlist'] = _('Publish orderlist')

        dict['Variables_for_extra_exams'] = _('Variables for extra exams')

        dict['Totals_only'] = _('Show totals per school only')
        dict['Extra_separate'] = _('Show extra per school separate')
        dict['Without_extra'] = _("Don't calculate extra exams")
        dict['File_per_school'] = _('Create Excelfile per school')
        dict['Language'] = _('Language')
        dict['Extra_exams'] = _('Extra exams')
        dict['the_exam_bureau'] = _('the exam bureau')

        dict['MPUBORD_info'] = {
            'request_verifcode_01': _("When you publish the orderlist, AWP will create an Excel file with the total exams, plus an Excel file for each school."),
            'request_verifcode_02': _("AWP will send an email to each 'voorzitter' and 'secretaris' with the orderlist of their school attached."),
            'request_verifcode_03': _("The orderlists will also be saved on the sever and can be found at the tab 'Published files'"),
            'request_verifcode_04': _("You need a 6 digit verification code to publish the orderlist."),
            'request_verifcode_05': _("Click 'Request verification code' and we will send you an email with the verification code."),
            'request_verifcode_06': _("The verification code expires in 30 minutes."),
            'requesting_verifcode': _('AWP is sending an email with the verification code'),
            'Publish_orderlist': _("Publish orderlist"),
            'Publishing_orderlist': _("AWP is publishing the orderlist"),
            'publish_ok': _("The orderlist is published succesfully."),
        }
    return dict


TXT_School_code = _('School code')
TXT_Organization = _('Organization')

TXT_Examnumber = _('Exam number')
TXT_Examnumber_twolines = _('Exam\nnumber')

TXT_Regnumber = _('Registration number')
TXT_Regnumber_twolines = _('Registration\nnumber')

TXT_Prefix = _('Prefix')
TXT_Prefix_twolines = pgettext_lazy('two lines ', 'Prefix')


TXT_Exam_period = _('Exam period')
TXT_Select_examperiod = _('Select exam period')
TXT_No_examperiods_found = _('No exam periods found')

TXT_Exam_type = _('Exam type')
TXT_Select_examtype = _('Select exam type')
TXT_No_examtypes_found = _('No exam types found')

TXT_All_candidates = _('All candidates')
TXT_All_subjects = _('All subjects')
TXT_Attachment = _('Attachment')

TXT_Email_address = _('Email address')

TXT_Inactive = _("Inactive")

TXT_This_candidate_has_no_subjects = _('This candidate has no subjects.')

TXT_Function = _('Function')
TXT_President = _('President')
TXT_Secretary = _('Secretary')
TXT_Commissioner = _('Commissioner')
TXT_Examinator = _('Examinator')

TXT__of_ = _(' of ')
TXT_Submit = _('Submit')

TXT_Approved_by = _('Approved by')
TXT_Submitted_by = _('Submitted by')

TXT__and_ = _(' and ')
TXT__or_ = _(" or ")
TXT__by_ = _(" by ")
TXT__for_ = _(" for ")

TXT_Name_ex_form = _('Name Ex form')
TXT_Date_submitted = _('Date submitted')
TXT_Download_Exform = _('Download Ex form')

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