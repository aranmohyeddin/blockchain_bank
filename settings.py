import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# example) SQLite
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

# example) MySQL
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': '',
#         'USER': '',
#         'PASSWORD': '',
#         'HOST': '',
#         'PORT': '',
#     }
# }

INSTALLED_APPS = (
    'banking',
    'blockchain',
)

SECRET_KEY = 'REPLACE_ME'
