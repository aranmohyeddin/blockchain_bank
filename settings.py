import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'blockchain_bank',
        'USER': 'dns',
        'PASSWORD': '123qwe123',
        'HOST': 'localhost',
        'PORT': '',
    }
}


INSTALLED_APPS = (
    'banking',
    'blockchain',
)

SECRET_KEY = 'REPLACE_ME'
