"""awpr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home_url')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home_url')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib.auth import views as auth_views
# PR2018-08-31 see https://docs.djangoproject.com/en/2.0/ref/urls/#path
from django.urls import include, path
# PR2018-03-16; PR2018-03-31 don't add doubledot, gives error 'attempted relative import beyond top-level package'
from django.views.generic import RedirectView

from accounts import views as account_views

from awpr import downloads as awpr_downloads, excel as grade_excel
from awpr import menus as awpr_menus
from schools import views as school_views
from schools import imports as school_imports
from students import views as student_views
from students import results as student_results
from subjects import views as subject_views
from subjects import orderlists as subject_orderlists

from grades import views as grade_views
from grades import exfiles as grade_exfiles
from grades import calc_results as grade_calc_res

from reports import views as report_views
from upload import views as upload_views

from accounts.forms import SchoolbaseAuthenticationForm

def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [

# PR2022-04-26
    path('sentry-debug/', trigger_error),
# PR2018-03-20
    #url(r'^login/$', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
# PR2020-09-25 redirects to schools/views/Loggedin
    path('login', auth_views.LoginView.as_view(authentication_form=SchoolbaseAuthenticationForm), name='login'),
    # this problem is fixed:
    #  create custom message when user that is not is_active wants to login - PR2020-08-18
    #      now a 'username password not correct' message appears, that is confusing

    # PR2018-03-19
    url(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),


#$$$$$$$$$$$$$$$$$$$$$$$
    #path('reset',
    #     auth_views.PasswordResetView.as_view(
    #         form_class=account_views.EmailValidationOnForgotPassword),
    #     name='password_reset'),

#$$$$$$$$$$$$$$$$$$$$$$

# 1. AwpPasswordResetView shows form with input fields 'schoolcode' and 'email' PR2018-03-27 PR2021-07-15
   # url(r'^reset/$',
    path('reset',
        account_views.AwpPasswordResetView.as_view(
            template_name='password_reset.html',
            email_template_name='password_reset_email.html',
            subject_template_name='password_reset_subject.txt'
        ),
        name='password_reset'),

    # debug not solves see https://github.com/iMerica/dj-rest-auth/issues/118 PR2021-07-12
    # was:
    # url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
    #    auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
    #    name='password_reset_confirm'),
    # from https://www.ordinarycoders.com/blog/article/django-password-reset

# 2. after clicking the link the form AwpPasswordResetView opens.
    # It has the input fields 'password1 and 'password2' PR2021-07-15
    #path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
    #    name='password_reset_confirm'),
    path('reset/<uidb64>/<token>/',
         account_views.AwpPasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
         name='password_reset_confirm'),

# 3. Shows message "We hebben een e-mail verzonden naar je e-mail adres ... "
    url(r'^reset/done/$',
        auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),
        name='password_reset_done'),

# 4. Shows message "Je hebt met succes een nieuw wachtwoord aangemaakt"
    url(r'^reset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
        name='password_reset_complete'),

    url(r'^settings/password/$', auth_views.PasswordChangeView.as_view(template_name='password_change.html'),
        name='password_change'),
    url(r'^settings/password/done/$', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'),
        name='password_change_done'),

    url(r'^users/set-password$',
        account_views.AwpPasswordResetView.as_view(
            template_name='password_setpassword.html',
            email_template_name='password_reset_email.html',
            subject_template_name='password_reset_subject.txt'
        ),
        name='password_setpassword'),


# ++++ SIGN UP +++++++++++++++++++++++++++++++++++++++ PR2020-09-25

    # PR2021-03-24 debug. After upgrading to django 3 this error came up:
    # Reverse for 'signup_activate_url' not found.
    #  from https://www.reddit.com/r/django/comments/jgmbz7/trying_to_resolve_noreversematcherror_for/
    # solved with https://learndjango.com/tutorials/django-password-reset-tutorial
    # solved by changing 'url' with 'path'
    # was:
    # url(r'^signup_activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
    #    account_views.SignupActivateView, name='signup_activate_url'),
    path('signup_activate/<uidb64>/<token>/', account_views.SignupActivateView, name='signup_activate_url'),


# PR2018-04-24
    url(r'^account_activation_sent/$', account_views.account_activation_sent, name='account_activation_sent_url'),

    # PR2018-10-14
    #url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
    #    account_views.UserActivate, name='activate_url'),
    #url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
    #   account_views.UserActivateView.as_view(), name='activate_url'),

    #url(r'^users/(?P<pk>\d+)/activated$', account_views.UserActivatedSuccess.as_view(), name='account_activation_success_url'),

    # PR2018-03-09 path is new in django2.0 See: https://docs.djangoproject.com/en/2.0/releases/2.0/#whats-new-2-0
    # path('admin/', admin.site.urls, name='admin_url'),

# ===== USERS ==========================  PR2018-03-21 PR2020-09-17
    # PR2018-04-21 debug: don't forget the .as_view() with brackets in the urlpattern!!!
    path('users/', include([
        path('user', account_views.UserListView.as_view(), name='users_url'),
        path('user_upload', account_views.UserUploadView.as_view(), name='user_upload_url'),

        path('allowedsections_upload', account_views.UserAllowedSectionsUploadView.as_view(), name='url_user_allowedsections_upload'),

        path('userpermit_upload', account_views.UserpermitUploadView.as_view(), name='userpermit_upload_url'),
        path('usersetting_upload', account_views.UserSettingsUploadView.as_view(), name='url_usersetting_upload'),
        path('permits_download', account_views.UserDownloadPermitsView.as_view(), name='user_download_permits_url'),

        path('user_modmsg_hide', account_views.UserModMessageHideView.as_view(), name='url_user_modmsg_hide'),
        #url(r'^users/(?P<pk>\d+)/log$', account_views.UserLogView.as_view(), name='user_log_url'),

        path('download_userdata_xlsx', account_views.UserdataDownloadXlsxView.as_view(), name='url_download_userdata_xlsx'),

        path('corrector', account_views.CorrectorListView.as_view(), name='url_corrector'),
        path('usercompensation_upload', account_views.UserCompensationUploadView.as_view(), name='url_usercompensation_upload'),

    ])),

    url(r'session_security/', include('session_security.urls')),
# PR2018-05-11
    url(r'^users/language/(?P<lang>[A-Za-z]{2})/$', account_views.UserLanguageView.as_view(), name='language_set_url'),


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    path('datalist_download', awpr_downloads.DatalistDownloadView.as_view(), name='url_datalist_download'),
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

    # PR2019-02-25
    # PR2021-11-15 NIU: path('downloads/', report_views.download, name='downloads_url'),

    # PR2018-03-11
    url('^$', school_views.home,  name='home_url'),
    # path('',  auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('loggedin/', school_views.Loggedin, name='loggedin_url'),
    # url(r'^favicon\.ico$',RedirectView.as_view(url='/static/img/favicon.ico')),
    # path('favicon\.ico',RedirectView.as_view(url='/static/img/favicon.ico')),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/img/favicon.ico')),

# PR2018-03-14
    # PR2018-04-17 debug: don't forget the brackets at the end of as_view() !!\

# ===== MANUAL ==========================  PR2021-06-10
    path('manual/', include([
        path('<page>/<paragraph>/', awpr_menus.ManualListView.as_view(), name='manual_url')
    ])),

# ===== MAILBOX ==========================  PR2021-06-10
    path('mail/', include([
        path('mailbox/', school_views.MailListView.as_view(), name='page_mailbox_url'),
        path('mailmessage_upload', school_views.MailmessageUploadView.as_view(), name='url_mailmessage_upload'),
        path('mailbox_upload', school_views.MailboxUploadView.as_view(), name='url_mailbox_upload'),
        path('recipients_download', school_views.MailboxRecipientsDownloadView.as_view(), name='url_recipients_download'),
        path('mailattachment_upload', school_views.MailAttachmentUploadView.as_view(), name='url_mailattachment_upload'),
        path('mailinglist', school_views.MailinglistUploadView.as_view(), name='url_mailinglist_upload'),
    ])),

# ===== SCHOOLS ==========================  PR2018-08-23 PR2020-10-20 PR2021-04-26
    path('schools/', include([
        path('examyears', school_views.ExamyearListView.as_view(), name='examyears_url'),
        path('examyear_upload', school_views.ExamyearUploadView.as_view(), name='url_examyear_upload'),
        path('examyear_copytosxm', school_views.ExamyearCopyToSxmView.as_view(), name='url_examyear_copytosxm'),
        path('subjectscheme_copyfrom', school_views.CopySchemesFromExamyearView.as_view(), name='url_subjectscheme_copyfrom'),

        path('school', school_views.SchoolListView.as_view(), name='schools_url'),
        path('school_upload', school_views.SchoolUploadView.as_view(), name='url_school_upload'),
        path('school_import', school_views.SchoolImportView.as_view(), name='school_import_url'),

        path('uploadsetting', school_views.SchoolImportUploadSetting.as_view(), name='school_uploadsetting_url')
    ])),

# ===== SUBJECTS ==========================  PR2018-08-23 PR2020-10-20
    path('subjects/', include([
        path('subject', subject_views.SubjectListView.as_view(), name='subjects_url'),
        path('subject_upload', subject_views.SubjectUploadView.as_view(), name='url_subject_upload'),

        path('scheme_upload', subject_views.SchemeUploadView.as_view(), name='scheme_upload_url'),
        path('subjecttype_upload', subject_views.SubjecttypeUploadView.as_view(), name='subjecttype_upload_url'),
        path('subjecttypebase_upload', subject_views.SubjecttypebaseUploadView.as_view(), name='subjecttypebase_upload_url'),

        path('schemeitem_upload', subject_views.SchemeitemUploadView.as_view(), name='schemeitem_upload_url'),

        path('download_scheme_xlsx', grade_excel.SchemeDownloadXlsxView.as_view(), name='url_download_scheme_xlsx')
    ])),

# ===== STUDENTS ==========================
    path('students/', include([
        path('student', student_views.StudentListView.as_view(), name='students_url'),
        path('student_upload', student_views.StudentUploadView.as_view(), name='url_student_upload'),

        path('multiple_occurrences', student_views.StudentMultipleOccurrencesView.as_view(), name='url_student_multiple_occurrences'),
        path('link_student', student_views.StudentLinkStudentView.as_view(), name='url_student_linkstudent'),
        path('enter_exemptions', student_views.StudentEnterExemptionsView.as_view(), name='url_student_enter_exemptions'),

        path('download_student_xlsx', grade_excel.StudentDownloadXlsxView.as_view(), name='url_download_student_xlsx'),
    ])),

# ===== STUDENTSUBJECTS ==========================
    path('studsubj/', include([
        path('studentsubject', student_views.StudentsubjectListView.as_view(), name='studentsubjects_url'),
        path('studsubj_upload', student_views.StudentsubjectMultipleUploadView.as_view(), name='url_studsubj_upload'),
        path('studsubj_single_update', student_views.StudentsubjectSingleUpdateView.as_view(), name='url_studsubj_single_update'),

        path('studsubj_validate_scheme', student_views.StudentsubjectValidateSchemeView.as_view(), name='url_studsubj_validate_scheme'),
        path('studsubj_validate_test', student_views.StudentsubjectValidateTestView.as_view(), name='url_studsubj_validate_test'),
        path('validate_all', student_views.StudentsubjectValidateAllView.as_view(), name='url_studsubj_validate_all'),

        path('studsubj_approve', student_views.StudentsubjectApproveSingleView.as_view(), name='url_studsubj_approve'),
        path('approve_submit_multiple', student_views.StudentsubjectApproveOrSubmitEx1Ex4View.as_view(), name='url_studsubj_approve_submit_multiple'),
        path('send_email_verifcode', student_views.SendEmailVerifcodeView.as_view(), name='url_send_email_verifcode'),

        path('studentsubjectnote_upload', student_views.StudentsubjectnoteUploadView.as_view(), name='url_studentsubjectnote_upload'),
        path('studentsubjectnote_download', student_views.StudentsubjectnoteDownloadView.as_view(), name='studentsubjectnote_download_url'),
        path('noteattachment_download/<int:pk_int>/', student_views.NoteAttachmentDownloadView.as_view(), name='noteattachment_download_url'),
        path('validate_composition', student_views.ValidateCompositionView.as_view(), name='url_validate_subj_composition'),

        path('cluster_upload', student_views.ClusterUploadView.as_view(), name='url_cluster_upload')
    ])),

# ===== EX1 EX3 EX4 FORMS ==========================
    path('exforms/', include([
        path('download_ex1', grade_excel.StudsubjDownloadEx1View.as_view(), name='url_download_ex1'),
        path('download_ex4', grade_excel.StudsubjDownloadEx4View.as_view(), name='url_download_ex4'),

        path('ex3_getinfo/', grade_exfiles.GetEx3infoView.as_view(), name='url_ex3_getinfo'),
        path('download_ex3/<list>/', grade_exfiles.DownloadEx3View.as_view(), name='url_ex3_download'),
        path('ex3_backpage', grade_exfiles.DownloadEx3BackpageView.as_view(), name='url_ex3_backpage'),

    ])),

# ===== GRADES ========================== PR2018-09-02 PR2018-11-19 PR2020-12-16
    path('grades/', include([
        path('grade', grade_views.GradeListView.as_view(), name='grades_url'),
        path('upload', grade_views.GradeUploadView.as_view(), name='url_grade_upload'),

        path('approve', grade_views.GradeApproveView.as_view(), name='url_grade_approve'),
        path('block', grade_views.GradeBlockView.as_view(), name='url_grade_block'),

        path('submit_ex2', grade_views.GradeSubmitEx2Ex2aView.as_view(), name='url_grade_submit_ex2'),

        path('download_icons', grade_views.GradeDownloadGradeIconsView.as_view(), name='download_grade_icons_url'),
        path('download_ex2', grade_excel.GradeDownloadEx2View.as_view(), name='url_grade_download_ex2'),
        path('download_ex2a', grade_excel.GradeDownloadEx2aView.as_view(), name='url_grade_download_ex2a'),
        path('download/', grade_exfiles.DownloadPublishedFile.as_view(), name='grades_download_published_url'),
    ])),

# ===== RESULTS ========================== PR2021-11-15
    path('results/', include([
        path('result', student_results.ResultListView.as_view(), name='results_url'),

        path('get_auth', student_results.GetGradelistDiplomaAuthView.as_view(), name='url_get_auth'),
        path('calc_results/<list>/', grade_calc_res.CalcResultsView.as_view(), name='url_calc_results'),
        path('download_gradelist/<lst>/', student_results.DownloadGradelistDiplomaView.as_view(), name='url_download_gradelist'),
        path('download_pok/<lst>/', student_results.DownloadPokView.as_view(), name='url_download_pok'),

        path('submit_ex5', grade_views.GradeSubmitEx5View.as_view(), name='url_grade_submit_ex5'),

        path('download_short_gradelist', student_results.GradeDownloadShortGradelist.as_view(), name='url_result_download_short_gradelist'),
        path('result_download_ex5', grade_excel.GradeDownloadEx5View.as_view(), name='url_result_download_ex5'),
        path('result_download_overview', grade_excel.GradeDownloadResultOverviewView.as_view(), name='url_result_download_overview'),

        path('change_birthcountry', student_views.ChangeBirthcountryView.as_view(), name='url_change_birthcountry'),
    ])),

# ===== ARCHIVES ========================== PR2022-03-09
    path('archives/', include([
        path('archive', school_views.ArchivesListView.as_view(), name='url_archive'),
        path('archive_upload', school_views.ArchivesUploadView.as_view(), name='url_archive_upload'),

    ])),

# ===== ORDERLISTS ========================== PR2021-04-04
    path('orderlists/', include([
        path('orderlist', student_views.OrderlistsListView.as_view(), name='orderlists_url'),
        path('download_orderlist/<list>/', grade_excel.OrderlistDownloadView.as_view(), name='orderlist_download_url'),
        path('download_orderlist_per_school', grade_excel.OrderlistPerSchoolDownloadView.as_view(), name='orderlist_per_school_download_url'),
        path('orderlist_parameters', school_views.OrderlistsParametersView.as_view(), name='url_orderlist_parameters'),
        path('orderlist_request_verifcode', school_views.OrderlistRequestVerifcodeView.as_view(), name='url_orderlist_request_verifcode'),
        path('orderlist_publish', school_views.OrderlistsPublishView.as_view(), name='url_orderlist_publish'),

        path('envelopsubject_upload', subject_orderlists.EnvelopSubjectUploadView.as_view(), name='url_envelopsubject_upload'),
        path('envelopbundle_upload', subject_orderlists.EnvelopBundleUploadView.as_view(), name='url_envelopbundle_upload'),
        path('enveloplabel_upload', subject_orderlists.EnvelopLabelUploadView.as_view(), name='url_enveloplabel_upload'),
        path('envelopitem_upload', subject_orderlists.EnvelopItemUploadView.as_view(), name='url_envelopitem_upload'),

        path('envelop_print_check', subject_orderlists.EnvelopPrintCheckView.as_view(), name='url_envelop_print_check'),
        path('envelop_print/<lst>/', subject_orderlists.EnvelopPrintView.as_view(), name='url_envelop_print'),
    ])),

# ===== EXAMS ========================== PR2021-04-04
    path('exams/', include([
        path('exam', subject_views.ExamListView.as_view(), name='exams_url'),
        path('upload', subject_views.ExamUploadView.as_view(), name='url_exam_upload'),
        path('copy', subject_views.ExamCopyView.as_view(), name='url_exam_copy'),
        path('copy_ntermen', subject_views.ExamCopyNtermenView.as_view(), name='url_exam_copy_ntermen'),
        path('link_ete_duo_exam_to_grade', subject_views.ExamLinkExamToGradesView.as_view(), name='url_link_exam_to_grades'),

        path('duo_exam_upload', subject_views.ExamUploadDuoExamView.as_view(), name='url_duo_exam_upload'),
        path('approve_publish_exam', subject_views.ExamApproveOrPublishExamView.as_view(), name='url_approve_publish_exam'),
        path('approve_grade_exam', subject_views.ExamApproveOrSubmitGradeExamView.as_view(), name='url_approve_submit_grade_exam'),

        path('send_email_submit_exam', student_views.SendEmailVerifcodeView.as_view(), name='url_send_email_submit_exam'),

        path('download_exam_pdf/<list>/', subject_views.ExamDownloadExamView.as_view(), name='url_exam_download_exam_pdf'),
        path('download_grade_exam_pdf/<list>/', subject_views.ExamDownloadGradeExamView.as_view(), name='url_exam_download_grade_exam_pdf'),
        path('download_conversion_pdf/<list>/', subject_views.ExamDownloadConversionView.as_view(), name='url_exam_download_conversion_pdf'),
        path('download_exam_json', subject_views.ExamDownloadExamJsonView.as_view(), name='url_exam_download_exam_json'),
    ])),


# ===== WOLF ========================== PR2022-12-16
    path('wolf/', include([
        path('exam', subject_views.WolfListView.as_view(), name='wolf_url'),

    ])),
# ===== IMPORT ==========================
    path('import/', include([
        #path('import_student_load/', student_views.StudentImportUploadDataView.as_view(), name='import_student_load_url'),
        path('importsettings_upload/', school_imports.UploadImportSettingView.as_view(), name='url_import_settings_upload'),
        path('student_upload/', school_imports.UploadImportStudentView.as_view(), name='url_importstudent_upload'),
        path('studentsubject_upload/', school_imports.UploadImportStudentsubjectView.as_view(), name='url_importstudentsubject_upload'),

        path('grade_upload/', school_imports.UploadImportGradeView.as_view(), name='url_importgrade_upload'),
        path('dnt_upload/', school_imports.UploadImportNtermentableView.as_view(), name='url_importdnt_upload'),

        path('username_upload/', school_imports.UploadImportUsernameView.as_view(), name='url_importusername_upload'),
        path('importdata_upload/', school_imports.UploadImportDataView.as_view(), name='url_importdata_upload'),
        path('ajax_schemeitems_download/', subject_views.SchemeitemsDownloadView.as_view(), name='ajax_schemeitems_download_url'),

        path('old_awp_upload', upload_views.UploadOldAwpView.as_view(), name='url_old_awp_upload'),
    ])),
]

