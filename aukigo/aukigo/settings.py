"""
Django settings for aukigo project.

Generated by 'django-admin startproject' using Django 3.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os

from dotenv import read_dotenv

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = int(os.environ.get("DEBUG", default=1))

IN_DOCKER = int(os.environ.get("IN_DOCKER", default=0))

# Create .env file path.
env_file = os.path.join(os.path.dirname(__file__), '../../.env.local.dev')

# Load env file from the path in DEBUG mode.
if DEBUG and not IN_DOCKER:
    read_dotenv(env_file)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", default='v8bhs^1wcd)z7k!cf&#)2!pye_wt_4lq@^g-(ax%%z$5n0x&7u')

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", default='*').split(" ")

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    # Third party
    'rest_framework',
    'rest_framework_gis',
    'django_better_admin_arrayfield',
    'corsheaders',
    # Own apps
    'datahub.apps.DatahubConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'aukigo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': []
        ,
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

WSGI_APPLICATION = 'aukigo.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("SQL_DATABASE", os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": os.environ.get("SQL_USER", ""),
        "PASSWORD": os.environ.get("SQL_PASSWORD", ""),
        "HOST": os.environ.get("SQL_HOST", ""),
        "PORT": os.environ.get("SQL_PORT", ""),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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

REST_FRAMEWORK = {
    # TODO: Uncomment following to prevent the use of browsable api
    #
    # 'DEFAULT_RENDERER_CLASSES': (
    #     'rest_framework.renderers.JSONRenderer',
    # ),
    # 'DEFAULT_AUTHENTICATION_CLASSES': [
    #     'rest_framework.authentication.TokenAuthentication',
    # ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/minute' if not DEBUG else '60/minute',
        'user': '1000/day' if not DEBUG else '60/minute'
    },
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}

CORS_ORIGIN_ALLOW_ALL = True if DEBUG else bool(int(os.environ.get("CORS_ORIGIN_ALLOW_ALL", 0)))
CORS_ORIGIN_WHITELIST = os.environ.get("DJANGO_CORS_WHITELIST", default='http://localhost:8080').split(" ")

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Helsinki'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

'''
###################################
Application specific configurations
###################################
'''

# Default coordinate reference system id
SRID = 4326

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'djangofile': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, "logs", "django.log" if IN_DOCKER else "django_.log"),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 10,
            'formatter': 'standard'
        },
        'appfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, "logs", "aukigo.log" if IN_DOCKER else "aukigo_.log"),
            'maxBytes': 1024 * 1024,
            'backupCount': 10,
            'formatter': 'standard'
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['djangofile', 'console'] if DEBUG else ['djangofile'],
            'level': ('INFO' if DEBUG else 'INFO'),
            'propagate': True,
        },
        'datahub': {
            'handlers': ['appfile', 'console'] if DEBUG else ['appfile'],
            'level': ('DEBUG' if DEBUG else os.environ.get("LOGGING_LEVEL", "INFO")),
            'propagate': True,
        }
    },
}

# CELERY stuff
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_BEAT_SCHEDULE = {
    'load-osm-data': {
        'task': 'datahub.tasks.load_osm_data',
        'schedule': int(os.environ.get("OSM_SCHEDULE_MINUTES", "720")) * 60,
        'options': {'queue': 'main'}
    }
}

DEFAULT_BBOX = '60.260904,24.499405,60.352655,24.668588'

# Directories
DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')
TEST_DATA_DIR = os.path.join(DATA_DIR, 'testdata')
FIXTURE_DIRS = [
    os.path.join(DATA_DIR, 'fixtures'),
    os.path.join(TEST_DATA_DIR, 'fixtures')
]

# OSM API
OVERPASS_API_URL = 'http://overpass-api.de/api'
OSM_CONFIG = os.path.join(DATA_DIR, "osmconf.ini")

# pg_tileserv
PG_TILESERV_POSTFIX = os.environ.get("PG_TILESERV_POSTFIX", ":7800")

# misc
PG_VIEW_PREFIX = 'osm'
IN_INTEGRATION_TEST = False
