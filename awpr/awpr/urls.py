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
from django.contrib import admin
from django.contrib.auth import views as auth_views
# PR2018-08-31 see https://docs.djangoproject.com/en/2.0/ref/urls/#path
from django.urls import include, path, re_path
# PR2018-03-16; PR2018-03-31 don't add doubledot, gives error 'attempted relative import beyond top-level package'
from django.views.generic import RedirectView

from accounts import views as account_views

from awpr import downloads as awpr_downloads
from importing import views as import_views
from schools import views as school_views
from schools import imports as school_imports
from students import views as student_views
from subjects import views as subject_views
from grades import views as grade_views
from grades import exfiles as grade_exfiles
from reports import views as report_views

from accounts.forms import SchoolbaseAuthenticationForm

from awpr.decorators import user_examyear_is_correct

urlpatterns = [
# PR2018-03-20
    #url(r'^login/$', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
# PR2020-09-25 redirects to Loggedin
    path('login', auth_views.LoginView.as_view(authentication_form=SchoolbaseAuthenticationForm), name='login'),
    # TODO create custom message when user that is not is_active wants to login - PR2020-08-18
    #      now a 'username password not correct' message appears, that is confusing

    # PR2018-03-19
    url(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),
# PR2018-03-27
    url(r'^reset/$',
        auth_views.PasswordResetView.as_view(
            template_name='password_reset.html',
            email_template_name='password_reset_email.html',
            subject_template_name='password_reset_subject.txt'
        ),
        name='password_reset'),
    url(r'^reset/done/$',
        auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),
        name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
        name='password_reset_confirm'),
    url(r'^reset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
        name='password_reset_complete'),

    url(r'^settings/password/$', auth_views.PasswordChangeView.as_view(template_name='password_change.html'),
        name='password_change'),
    url(r'^settings/password/done/$', auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'),
        name='password_change_done'),

# ++++ SIGN UP +++++++++++++++++++++++++++++++++++++++ PR2020-09-25
    url(r'^signup_activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        account_views.SignupActivateView, name='signup_activate_url'),

# PR2018-04-24
    url(r'^account_activation_sent/$', account_views.account_activation_sent, name='account_activation_sent_url'),
    # PR2018-10-14
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        account_views.UserActivate, name='activate_url'),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
       account_views.UserActivateView.as_view(), name='activate_url'),
    #url(r'^users/(?P<pk>\d+)/activated$', account_views.UserActivatedSuccess.as_view(), name='account_activation_success_url'),

    url(r'^users/set-password$',
        auth_views.PasswordResetView.as_view(
            template_name='password_setpassword.html',
            email_template_name='password_reset_email.html',
            subject_template_name='password_reset_subject.txt'
        ),
        name='password_setpassword'),

    # PR2018-03-09 path is new in django2.0 See: https://docs.djangoproject.com/en/2.0/releases/2.0/#whats-new-2-0
    path('admin/', admin.site.urls, name='admin_url'),

# PR2018-03-21 PR2020-09-17
    # PR2018-04-21 debug: don't forget the .as_view() with brackets in the urlpattern!!!
    path('user/', include([
        path('users', account_views.UserListView.as_view(), name='users_url'),
        path('user_upload', account_views.UserUploadView.as_view(), name='user_upload_url'),
        path('settings_upload', account_views.UserSettingsUploadView.as_view(), name='settings_upload_url'),

        #url(r'^users/(?P<pk>\d+)/log$', account_views.UserLogView.as_view(), name='user_log_url'),
    ])),

    url(r'session_security/', include('session_security.urls')),
# PR2018-05-11
    url(r'^users/language/(?P<lang>[A-Za-z]{2})/$', account_views.UserLanguageView.as_view(), name='language_set_url'),

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    path('datalist_download', awpr_downloads.DatalistDownloadView.as_view(), name='datalist_download_url'),
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

    # PR2018-03-11
    url('^$', school_views.home,  name='home_url'),
    # path('',  auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('loggedin/', school_views.Loggedin, name='loggedin_url'),
    # url(r'^favicon\.ico$',RedirectView.as_view(url='/static/img/favicon.ico')),
    # path('favicon\.ico',RedirectView.as_view(url='/static/img/favicon.ico')),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/img/favicon.ico')),

# PR2018-03-14
    # PR2018-04-17 debug: don't forget the brackets at the end of as_view() !!\

# department PR2018-08-11 PR2019-02-27
    path('department/', include([
        path('', school_views.DepartmentListView.as_view(), name='department_list_url'),
        path('<int:pk>/', include([
            path('select', school_views.DepartmentSelectView.as_view(), name='department_select_url'),
            path('log', school_views.DepartmentLogView.as_view(), name='department_log_url'),
        ])),
    ])),

# school  PR2018-08-25 PR2018-12-20
    path('schools/', include([
        path('examyears', school_views.ExamyearListView.as_view(), name='examyears_url'),
        path('examyear_upload', school_views.ExamyearUploadView.as_view(), name='examyear_upload_url'),

        path('school', school_views.SchoolListView.as_view(), name='school_list_url'),
        path('school_upload', school_views.SchoolUploadView.as_view(), name='school_upload_url'),
        path('school_import', school_views.SchoolImportView.as_view(), name='school_import_url'),
        path('uploadsetting', school_views.SchoolImportUploadSetting.as_view(), name='school_uploadsetting_url'),
        path('uploaddata', school_views.SchoolImportUploadData.as_view(), name='school_uploaddata_url'),


        path('<int:pk>/', include([
            path('select/', school_views.SchoolSelectView.as_view(), name='school_selected_url'),
            path('log', school_views.SchoolLogView.as_view(), name='school_log_url'),
        ])),
    ])),

    # PR 2018-08-31 from https://simpleisbetterthancomplex.com/tutorial/2018/01/29/how-to-implement-dependent-or-chained-dropdown-list-with-django.html
    # re_path(r'^ajax/load-levels/$', subject_views.load_levels, name='ajax_load_levels'),


# level PR2018-11-10
    url(r'^subjecttype/$', subject_views.SubjecttypeListView.as_view(), name='subjecttype_list_url'),
    url(r'^subjecttype/add/$', subject_views.SubjecttypeAddView.as_view(), name='subjecttype_add_url'),
    url(r'^subjecttype/(?P<pk>\d+)/edit$', subject_views.SubjecttypeEditView.as_view(), name='subjecttype_edit_url'),
    url(r'^subjecttype/(?P<pk>\d+)/delete/$', subject_views.SubjecttypeDeleteView.as_view(), name='subjecttype_delete_url'),
    url(r'^subjecttype/(?P<pk>\d+)/log$', subject_views.SubjecttypeLogView.as_view(), name='subjecttype_log_url'),

# scheme PR2018-08-23
    url(r'^scheme/$', subject_views.SchemeListView.as_view(), name='scheme_list_url'),
    url(r'^scheme/add/$', subject_views.SchemeAddView.as_view(), name='scheme_add_url'),
    url(r'^scheme/(?P<pk>\d+)/edit$', subject_views.SchemeEditView.as_view(), name='scheme_edit_url'),
    url(r'^scheme/(?P<pk>\d+)/delete/$', subject_views.SchemeDeleteView.as_view(), name='scheme_delete_url'),
    url(r'^scheme/(?P<pk>\d+)/log$', subject_views.SchemeLogView.as_view(), name='scheme_log_url'),

    path('scheme/load_levels/', subject_views.load_levels, name='load_levels_url'),  # PR2018-10-03
    path('scheme/load_sectors/', subject_views.load_sectors, name='load_sectors_url'),  # PR2018-10-03

# schemeitem PR2018-11-09
    url(r'^schemeitem/$', subject_views.SchemeitemListView.as_view(), name='schemeitem_list_url'),
    url(r'^schemeitem/add/$', subject_views.SchemeitemAddView.as_view(), name='schemeitem_add_url'),
    url(r'^schemeitem/(?P<pk>\d+)/edit$', subject_views.SchemeitemEditView.as_view(), name='schemeitem_edit_url'),
    url(r'^schemeitem/(?P<pk>\d+)/delete/$', subject_views.SchemeitemDeleteView.as_view(), name='schemeitem_delete_url'),
    url(r'^schemeitem/(?P<pk>\d+)/log$', subject_views.SchemeitemLogView.as_view(), name='schemeitem_log_url'),

# package PR2019-02-27
   # url(r'^package/$', subject_views.PackageView.as_view(), name='scheme_list_url'),

# ===== SUBJECTS ==========================  PR2018-08-23 PR2020-10-20
    path('subjects/', include([
        path('subject', subject_views.SubjectListView.as_view(), name='subjects_url'),
        path('subject_upload', subject_views.SubjectUploadView.as_view(), name='subject_upload_url'),
        path('subject_import', subject_views.SubjectImportView.as_view(), name='subject_import_url'),
        path('uploadsetting', subject_views.SubjectImportUploadSetting.as_view(), name='subject_uploadsetting_url'),
        path('uploaddata', subject_views.SubjectImportUploadData.as_view(), name='subject_uploaddata_url'),
    ])),

# ===== STUDENTS ========================== PR2018-09-02 PR2018-11-19 PR2020-12-16
    path('students/', include([
        path('student', student_views.StudentListView.as_view(), name='students_url'),

        path('student_upload', student_views.StudentUploadView.as_view(), name='student_upload_url'),
        #path('student_import', student_views.StudentImportView.as_view(), name='student_import_url'),
        #path('uploaddata', student_views.StudentImportUploadData.as_view(), name='student_uploaddata_url'),

        path('studentsubject', student_views.StudentsubjectListView.as_view(), name='studentsubjects_url'),
        path('studentsubject_upload', student_views.StudentsubjectUploadView.as_view(), name='studsubj_upload_url'),

        path('studentsubjectnote_upload', student_views.StudentsubjectnoteUploadView.as_view(), name='studentsubjectnote_upload_url'),

        path('grades', grade_views.GradeListView.as_view(), name='grades_url'),
        path('grade_upload', grade_views.GradeUploadView.as_view(), name='grade_upload_url'),
        path('grade_approve', grade_views.GradeApproveView.as_view(), name='grade_approve_url'),
        #path('download_published_file', grade_exfiles.DownloadPublishedFile.as_view(), name='download_published_file_url'),
        path('grade_download_ex2a', grade_exfiles.GradeDownloadEx2aView.as_view(), name='grade_download_ex2a_url'),

        path('load_cities/', student_views.load_cities, name='load_cities_url'),  # PR2018-09-03

        path('uploadsetting', student_views.StudentImportUploadSetting.as_view(), name='student_uploadsetting_url'),

# department PR2018-08-11 PR2019-02-27
        path('exfiles/', include([
            path('<filename>/', grade_exfiles.DownloadPublishedFile.as_view(), name='download_published_file_url'),
        ])),
    ])),

    # PR2018-05-06 debug: don't forget the brackets at the end of as_view() !!
    path('import/all/', import_views.ImportAllView.as_view(), name='import_all_url'),

    # PR2019-02-25
    path('downloads/', report_views.download, name='downloads_url'),


# ajax PR2018-12-02
    path('ajax/', include([
        #path('import_student_load/', student_views.StudentImportUploadDataView.as_view(), name='import_student_load_url'),
        path('importsettings_upload/', school_imports.UploadImportSettingView.as_view(), name='importsettings_upload_url'),
        path('importdata_upload/', school_imports.UploadImportDataView.as_view(), name='importdata_upload_url'),
        path('ajax_schemeitems_download/', subject_views.SchemeitemsDownloadView.as_view(), name='ajax_schemeitems_download_url'),
        path('ajax_ssi_upload/', subject_views.SchemeitemUploadView.as_view(), name='ajax_ssi_upload_url'),
    ])),
]