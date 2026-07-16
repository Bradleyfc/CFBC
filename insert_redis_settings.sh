#!/bin/bash

# Find line number of DEFAULT_FROM_EMAIL setting
line_num=$(grep -n "DEFAULT_FROM_EMAIL = " cfbc/settings.py | cut -d: -f1)
if [ -z "$line_num" ]; then
    echo "Could not find DEFAULT_FROM_EMAIL line"
    exit 1
fi

# Insert Redis configuration after DEFAULT_FROM_EMAIL
sed -i "${line_num}a\\
# Redis Cache Configuration\\
CACHES = {\\
    'default': {\\
        'BACKEND': 'django_redis.cache.RedisCache',\\
        'LOCATION': 'redis://127.0.0.1:6379/1',  # Database 1 for general cache\\
        'OPTIONS': {\\
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',\\
            'PARSER_CLASS': 'redis.connection.HiredisParser',\\
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',\\
            'CONNECTION_POOL_KWARGS': {\\
                'max_connections': 50,\\
                'timeout': 20,\\
            },\\
            'MAX_CONNECTIONS': 1000,\\
            'PICKLE_VERSION': -1,  # Use latest pickle protocol\\
            'SOCKET_CONNECT_TIMEOUT': 5,  # seconds\\
            'SOCKET_TIMEOUT': 5,  # seconds\\
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',\\
            'IGNORE_EXCEPTIONS': True,  # Don't crash if Redis is down\\
        },\\
        'KEY_PREFIX': 'cfbc_cache',\\
        'TIMEOUT': 300,  # Default cache timeout in seconds (5 minutes)\\
    },\\
    'session': {\\
        'BACKEND': 'django_redis.cache.RedisCache',\\
        'LOCATION': 'redis://127.0.0.1:6379/2',  # Database 2 for sessions\\
        'OPTIONS': {\\
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',\\
            'PARSER_CLASS': 'redis.connection.HiredisParser',\\
            'IGNORE_EXCEPTIONS': True,\\
        },\\
        'KEY_PREFIX': 'cfbc_sessions',\\
    }\\
}\\
\\
# Session configuration to use Redis\\
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'\\
SESSION_CACHE_ALIAS = 'session'\\
SESSION_COOKIE_AGE = 1209600  # 2 weeks\\
SESSION_EXPIRE_AT_BROWSER_CLOSE = False" cfbc/settings.py
