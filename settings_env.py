# -*- coding: utf-8 -*-
"""
腾讯蓝鲸普通无登录APP运行环境配置文件
在settings.py最后面加入以下一行即可
from settings_env import *
使用这一行把所有配置覆盖成测试环境或生产环境的配置
为了防止这行被IDE优化掉还可以在加一行
print(RUN_MODE)

蓝鲸云平台只是一个Django的云平台
你可以做自己想做的任何事
只要保证：
1. 你测试的时候没有任何问题
2. python manage.py migrate 可以成功运行
那么你的应用应该就可以成功部署了
默认引入的一堆模块只是用于方便记录使用者、发送邮件、发送短信、记录日志等等用途
通常一个单纯的网络服务不会使用到这些东西
所以可以省略很多无用的配置以及文件夹
而如果使用Django自带的模板引擎，并且不使用蓝鲸上面的页面布局模板
又可以省略很多全局变量
精简以后就是这个文件
使用这个文件即可在蓝鲸云平台上运行原生的Django应用
"""

import os

# 通过DJANGO_CONF_MODULE环境变量判断运行模式
# 并设置了一个无用的环境变量：RUN_MODE，共有3种取值DEVELOP, TEST, PRODUCT
WSGI_ENV = os.environ.get('DJANGO_CONF_MODULE', '')
if WSGI_ENV.endswith('production'):
    RUN_MODE = 'PRODUCT'
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': os.environ.get('BK_DB_HOST', 'appdb.bk.tencentyun.com'),
            'PORT': os.environ.get('BK_DB_PORT', '3337'),
            'USER': os.environ.get('BK_APP_CODE', ''),
            'PASSWORD': os.environ.get('BK_APP_PWD', ''),
            'NAME': os.environ.get('BK_APP_CODE', ''),
        },
    }
    DEBUG = False
    ALLOWED_HOSTS = ['*']
    STATIC_URL = os.environ.get('BK_STATIC_URL', '/static/')
    SECRET_KEY = os.environ.get('BK_SECRET_KEY', '')
elif WSGI_ENV.endswith('testing'):
    RUN_MODE = 'TEST'
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': os.environ.get('BK_DB_HOST', 'test.appdb.bk.tencentyun.com'),
            'PORT': os.environ.get('BK_DB_PORT', '3340'),
            'USER': os.environ.get('BK_APP_CODE', ''),
            'PASSWORD': os.environ.get('BK_APP_PWD', ''),
            'NAME': os.environ.get('BK_APP_CODE', ''),
        },
    }
    DEBUG = False
    ALLOWED_HOSTS = ['*']
    STATIC_URL = os.environ.get('BK_STATIC_URL', '/static/')
    SECRET_KEY = os.environ.get('BK_SECRET_KEY', '')
else:
    RUN_MODE = 'DEVELOP'
    STATICFILES_DIRS = (
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"),
    )
