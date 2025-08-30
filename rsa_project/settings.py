from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- dotenv ---
env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Application definition

INSTALLED_APPS = [
    "jazzmin",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

JAZZMIN_SETTINGS = {
    "site_title": "NovaDomus Admin",
    "site_header": "NovaDomus — Gestione",
    "site_brand": "NovaDomus",
    "welcome_sign": "Benvenuto nella piattaforma RSA",
    "copyright": "Nova Domus",
    "search_model": ["core.Paziente", "core.Farmaco", "core.Somministrazione"],

    # Link rapidi in top menu
    "topmenu_links": [
        {"name": "Dashboard", "url": "dashboard", "permissions": ["auth.view_user"]},
        {"app": "core"},  # mostra tutte le app del progetto
    ],

    # Icone (FontAwesome)
    "icons": {
        "core.Paziente": "fas fa-user-injured",
        "core.ContattoEmergenza": "fas fa-phone",
        "core.Allergia": "fas fa-allergies",
        "core.Prescrizione": "fas fa-notes-medical",
        "core.Farmaco": "fas fa-pills",
        "core.Somministrazione": "fas fa-syringe",
        "core.ParametroVitale": "fas fa-heartbeat",
        "core.Igiene": "fas fa-soap",
        "core.DiarioIgiene": "fas fa-soap",
        "core.Documento": "fas fa-file-medical",
    },

    # Ordine app/modelli nella sidebar
    "order_with_respect_to": ["core.Paziente",
    "core.ContattoEmergenza",
    "core.Allergia",
    "core.Farmaco",
    "core.Prescrizione",
    "core.Somministrazione",
    "core.ParametroVitale",
    "core.DiarioIgiene"],
    
    "show_ui_builder": True,  # bottone per cambiare tema live
}

# Tweaks grafici (tema scuro/chiaro)
JAZZMIN_UI_TWEAKS = {
    "theme": "default",  # puoi cambiare: cosmo, flatly, lumen, etc.
    "dark_mode_theme": "darkly",
    "navbar": "navbar-dark bg-primary",
    "no_navbar_border": True,
    "body_small_text": False,
    "brand_colour": "navbar-dark bg-primary",
    "accent": "accent-info",
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "footer_fixed": False,
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rsa_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
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

WSGI_APPLICATION = 'rsa_project.wsgi.application'


DATABASES = {
    "default": env.db(
        "DATABASE_URL",  
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'it'
TIME_ZONE = 'Europe/Rome'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DATE_INPUT_FORMATS = ['%d/%m/%Y', '%Y-%m-%d']

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "core/static"]

# Dove verranno raccolti gli statici per la produzione
STATIC_ROOT = BASE_DIR / "staticfiles"

# Storage ottimizzato per produzione con WhiteNoise
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = "dashboard"   # dove atterrare dopo il login
LOGOUT_REDIRECT_URL = "login"      # dopo il logout
LOGIN_URL = "login"