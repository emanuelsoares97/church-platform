"""
Django settings for church_platform project.
"""

from pathlib import Path
import os

import cloudinary
import dj_database_url
from decouple import Csv, config


# diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent


# chave secreta da aplicação
# em produção deve existir apenas em variável de ambiente
SECRET_KEY = config("SECRET_KEY")


# ativa debug apenas em ambiente de desenvolvimento
DEBUG = config("DEBUG", default=False, cast=bool)


# hosts permitidos pela aplicação
# em desenvolvimento pode incluir localhost e 127.0.0.1
# em produção deve conter apenas os domínios reais
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="127.0.0.1,localhost",
    cast=Csv(),
)


# origens confiáveis para pedidos csrf
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://127.0.0.1:8000,http://localhost:8000,https://*.ngrok-free.app,https://*.ngrok-free.dev",
    cast=Csv(),
)


# apps instaladas no projeto
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cloudinary",
    "events",
    "core",
    "gallery",
    "management",
]


# middlewares globais da aplicação
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "church_platform.urls"


# configuração do sistema de templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "management.context_processors.management_access",
            ],
        },
    },
]


WSGI_APPLICATION = "church_platform.wsgi.application"


# base de dados principal
DATABASES = {
    "default": dj_database_url.config(
        default=config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
}


# validadores de password do django
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# idioma e fuso horário do projeto
LANGUAGE_CODE = "pt-pt"
TIME_ZONE = "Europe/Lisbon"
USE_I18N = True
USE_TZ = True


# ficheiros estáticos
STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# ficheiros media locais
# nota: os ficheiros media dinâmicos principais estão no cloudinary
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# tipo de chave primária por defeito
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# urls de autenticação
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "management:home"
LOGOUT_REDIRECT_URL = "login"


# url base do sistema
# usada para construir links absolutos em emails e qr codes
SITE_URL = config("SITE_URL", default="http://127.0.0.1:8000")


# configuração do resend
# esta chave é usada no serviço de envio de emails via api
RESEND_API_KEY = config("RESEND_API_KEY", default="")


# email de envio usado no resend
# em modo de teste sem domínio verificado usar onboarding@resend.dev
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="UCC Eventos <onboarding@resend.dev>",
)


# backend de email do django
# este backend não é usado no envio via resend
# fica apenas para testes locais ou outros usos futuros
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = BASE_DIR / "tmp_emails"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# segurança mínima para produção
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG


# cloudinary
cloudinary.config(
    cloud_name=config("CLOUDINARY_CLOUD_NAME"),
    api_key=config("CLOUDINARY_API_KEY"),
    api_secret=config("CLOUDINARY_API_SECRET"),
    secure=True,
)

APP_VERSION = "v2"