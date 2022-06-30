import os
from decouple import config, Csv  # PR2018-02-24

#PR2022-02-13 was ugettext_lazy as _, replaced by: gettext_lazy as _
from django.utils.translation import gettext_lazy as _  # PR2018-04-28

import dj_database_url  # PR2018-04-29
# PR2018-05-06 from https://simpleisbetterthancomplex.com/tips/2016/09/06/django-tip-14-messages-framework.html
from django.contrib.messages import constants as messages

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')  # PR2018-02-24

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool) # PR2018-02-24

# ALLOWED_HOSTS =
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())  # PR2018-02-24

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',  # PR2018-03-12

    # 'menu', # PR2018-05-08 simple_menu removed PR2018-10-07
    # 'sitetree',  # PR2018-10-07 removed PR2018-10-07
    'accounts',  # PR2018-03-16
    'awpr',  # PR2021-06-28
    'schools',   # PR2018-04-13
    'subjects',  # PR2018-07-20
    'students',  # PR2018-07-20
    'grades',  # PR2020-12-16
    'reports',  # PR2018-07-20
    'upload',  # PR2018-07-24

    'session_security', # PR2018-05-10
    'anymail', # PR2018-12-28

# PR2021-03-06 from https://www.digitalocean.com/community/tutorials/how-to-set-up-object-storage-with-django
# and from https://simpleisbetterthancomplex.com/tutorial/2017/08/01/how-to-setup-amazon-s3-in-a-django-project.html
    'storages'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # PR2018-05-10
    'session_security.middleware.SessionSecurityMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

#PR2020-10-12 from https://stackoverflow.com/questions/5401118/django-messages-being-displayed-twice/9121754
# to prevent messages to show multiple times - don't know yet if it works
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

ROOT_URLCONF = 'awpr.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
# PR2018-03-02
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'templates/accounts'),
            os.path.join(BASE_DIR, 'templates/emails'),
            os.path.join(BASE_DIR, 'templates/includes'),
            os.path.join(BASE_DIR, 'templates/reports'),
            os.path.join(BASE_DIR, 'templates/schools'),
            os.path.join(BASE_DIR, 'templates/students'),
            os.path.join(BASE_DIR, 'templates/subjects'),
            os.path.join(BASE_DIR, 'accounts/templates'),
            # os.path.join(BASE_DIR, 'templates/upload'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# PR2018-05-08 for django-simple-menu from http://django-simple-menu.readthedocs.io/en/latest/installation.html
TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.request",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
)

WSGI_APPLICATION = 'awpr.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

# PR2018-04-29 PostgresQL
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL')
    )
}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# PR2018-04-22
AUTH_USER_MODEL = 'accounts.User'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

# PR 2018-03-06 STATIC_ROOT is the folder where all static files will be stored after a manage.py collectstatic.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# PR2021-03-09 from https://stackabuse.com/serving-static-files-in-python-with-django-aws-s3-and-whitenoise/
# STATIC_URL is the URL used when referring to static files. It must end with /
STATIC_URL = '/static/'
# PR2018-03-06 This line tells Django to append static to the base url when searching for static files.

# PR2018-03-03 Error: the STATICFILES_DIRS setting should not contain the STATIC_ROOT setting.
# PR2018-03-06 The STATICFILES_DIRS tells Django where to look for static files that are not tied to a particular app.
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'),]

# PR2021-01-22 path to fonts dir in statis
# PR2021-02-07 debug: backslash + '\\' gives error on server, use / instead
# still error ... because font was name 'arial.ttf' and I looked for 'Arial.ttf'
STATICFILES_FONTS_DIR = os.path.join(BASE_DIR, 'static', 'fonts') + '/'
# 'static', 'media' goes wrong on server, becasue collectstatic puts all static file in one folder
# was: STATICFILES_MEDIA_DIR = os.path.join(BASE_DIR, 'static', 'media') + '/'
STATICFILES_MEDIA_DIR = os.path.join(BASE_DIR, 'media', 'private', 'published') + '/'

# PR2021-01-22 from https://www.caktusgroup.com/blog/2017/08/28/advanced-django-file-handling/
# how to handle DEFAULT_FILE_STORAGE ( i.e. MEDIAFILES_STORAGE)
# was: MEDIA_DIR = '/static/media/'
# used to create filepath in create_published_rows
MEDIA_DIR = '/published/'

# PR2021-03-07 https://www.ordinarycoders.com/blog/article/serve-django-static-and-media-files-in-production
# Note: must comment out the original STATIC_URL and STATICFILES_DIRS.

# PR2021-03-06 from https://www.digitalocean.com/community/tutorials/how-to-set-up-object-storage-with-django
# SECURITY WARNING: keep the access key used in production secret!
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL')
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400',}
# AWS_LOCATION = config('AWS_LOCATION')

# from Vitor de Freitas, used in storage_backends.py
# AWS_STATIC_LOCATION = config('AWS_STATIC_LOCATION')
# AWS_PUBLIC_MEDIA_LOCATION = config('AWS_PUBLIC_MEDIA_LOCATION')
AWS_PRIVATE_MEDIA_LOCATION = config('AWS_PRIVATE_MEDIA_LOCATION')

#STATIC_URL = 'https://%s/%s/' % (AWS_S3_ENDPOINT_URL, AWS_LOCATION)
# PR2021-03-08 from https://simpleisbetterthancomplex.com/tutorial/2017/08/01/how-to-setup-amazon-s3-in-a-django-project.html
# from Vitor de Freitas: STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# DEFAULT_FILE_STORAGE = 'awpr.storage_backends.MediaStorage'  # <-- here is where we reference it

# PR2021-03-08 from the docs https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
#STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
AWS_S3_REGION_NAME = 'nyc3'

# PR 2018-03-27
LOGIN_URL = 'login'
# PR 2018-03-20
# LOGIN_REDIRECT_URL = 'home_url'
LOGIN_REDIRECT_URL = 'loggedin_url' # PR 2018-12-23

# PR 2018-03-19
LOGOUT_REDIRECT_URL = 'home_url'

# was: PR 2018-03-27  EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# PR 2018-12-28
EMAIL_BACKEND = config('EMAIL_BACKEND', default='')
ANYMAIL = {
    'MAILGUN_API_KEY': config('MAILGUN_API_KEY', default=''),
    'MAILGUN_SENDER_DOMAIN': config('MAILGUN_SENDER_DOMAIN', default=''),
}
DEFAULT_FROM_EMAIL = 'AWP online <noreply@awponline.net>'


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/
TIME_ZONE = 'America/Curacao'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# PR 2018-04-28 from https://medium.com/@nolanphillips/a-short-intro-to-translating-your-site-with-django-1-8-343ea839c89b
# Add LocaleMiddleware to MIDDLEWARE, it checks the incoming request for the user's preferred language settings.
# Add the LocaleMiddleware after SessionMiddleware and CacheMiddleware, and before the CommonMiddleware.
# Provide a lists of languages which your site supports.
LANGUAGES = (
    ('en', _('English')),
    ('nl', _('Dutch')),
)

# Set the default language for your site.
LANGUAGE_CODE = 'nl'

# Tell Django where the project's translation files should be.
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)
# PR2022-04-26 Sentry added

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    #dsn="https://f43a36019f0c4c26bed725e977e3a6d9@o999826.ingest.sentry.io/6364571",
    dsn=config('SENTRY_DSN', default=''),
    integrations=[DjangoIntegration()],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    # traces_sample_rate=1.0,
    traces_sample_rate=config('SENTRY_SAMPLE_RATE', default=0.1, cast=float),


    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    # send_default_pii=True
    send_default_pii=False
)


SENTRY_SRC = config('SENTRY_SRC', default=None)

# PR2022-01-11
IS_TESTSITE = config('IS_TESTSITE', default=False, cast=bool)

# PR2021-03-26
LOGGING_ON = config('LOGGING_ON', default=False, cast=bool)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    #'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    # PR2022-06-27 write accounts_log also in production - to check password reset attempts, formatter: simple
    'handlers': {
        'accounts_log': {
            'level': 'DEBUG',
            'filters': [], # was: 'filters': ['require_debug_true']
            'class': 'logging.FileHandler',
            'filename': config('LOGGER_BASEDIR') + 'accounts.log',
            'formatter': 'simple'  # was: 'formatter': 'verbose'
        },
        'awpr_log': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.FileHandler',
            'filename': config('LOGGER_BASEDIR') + 'awpr.log',
            'formatter': 'verbose'
        },
        'schools_log': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.FileHandler',
            'filename': config('LOGGER_BASEDIR') + 'schools.log',
            'formatter': 'verbose'
        },
        'students_log': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.FileHandler',
            'filename': config('LOGGER_BASEDIR') + 'students.log',
            'formatter': 'verbose'
        },
        'grades_log': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.FileHandler',
            'filename': config('LOGGER_BASEDIR') + 'grades.log',
            'formatter': 'verbose'
        },
        'subjects_log': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.FileHandler',
            'filename': config('LOGGER_BASEDIR') + 'subjects.log',
            'formatter': 'verbose'
        },
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.db.backends': {'level': 'DEBUG',},
        'django': {'handlers': ['console'],},
        'django.request': {'handlers': ['mail_admins'], 'level': 'ERROR', 'propagate': False,},
        'django.security': {'handlers': ['mail_admins'], 'level': 'ERROR', 'propagate': False,},
        'py.warnings': {'handlers': ['console'],},
        'accounts': {'handlers': ['accounts_log'], 'level': 'DEBUG', 'propagate': True,},
        'awpr': {'handlers': ['awpr_log'], 'level': 'DEBUG', 'propagate': True,},
        'upload': {'handlers': ['awpr_log'], 'level': 'DEBUG', 'propagate': True,},
        'schools': {'handlers': ['schools_log'], 'level': 'DEBUG', 'propagate': True,},
        'students': {'handlers': ['students_log'], 'level': 'DEBUG', 'propagate': True,},
        'subjects': {'handlers': ['subjects_log'], 'level': 'DEBUG', 'propagate': True,},
        'grades': {'handlers': ['grades_log'], 'level': 'DEBUG', 'propagate': True,},
    }
}

# PR2018-05-06 from https://simpleisbetterthancomplex.com/tips/2016/09/06/django-tip-14-messages-framework.html
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# PR2018-05-10 PR2021-07-23: changed to 30 minutes PR2022-02-15: changed to 60 minutes
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SECURITY_WARN_AFTER = 3420 # PR2022-02-15. Time (in seconds) before the user should be warned. Default 540.
SESSION_SECURITY_EXPIRE_AFTER = 3600 # PR2022-02-15. Time (in seconds) before the user should be logged out. Default is 600.

# In global.settings.py: PR2018-07-30
# The number of days a password reset link is valid for
# The PASSWORD_RESET_TIMEOUT_DAYS setting is deprecated. Use 'PASSWORD_RESET_TIMEOUT instead.' PR2021-07-28
# Default: 259200 (3 days, in seconds)
# was: PASSWORD_RESET_TIMEOUT_DAYS = 7
PASSWORD_RESET_TIMEOUT = 604800  #  7 days = 604.800 seconds

