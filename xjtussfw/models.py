# coding=utf-8
import re

import requests
from django.db import models

from xjtucas.models import User as CasUser, Cas


class UseDeletedUserError(Exception):
    """尝试使用已删除用户"""

    def __init__(self, user):
        # type: (User) -> None
        self.user = user

    def __str__(self):
        return 'Attempted to use deleted user'


class SsfwLoginError(Exception):
    """用户登录师生服务失败，原因未知"""

    def __init__(self, user):
        # type: (User) -> None
        self.user = user

    def __str__(self):
        return 'CAS login failed'


class User(models.Model):
    user = models.OneToOneField(CasUser, related_name='ssfw_user_set')
    name = models.CharField(max_length=50, default='', blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True, null=True)
    delete_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.net_id

    @property
    def is_deleted(self):
        if self.delete_time is not None:
            return True
        elif self.user.is_deleted:
            Log(user=self, message='User invalid').save()
            self.delete_time = self.user.delete_time
            self.save()
            return True
        return False

    def login(self):
        """自动登录师生服务"""
        ssfw = Ssfw()
        if self.is_deleted:
            Log(user=self, message='Attempted to login deleted user').save()
            raise UseDeletedUserError(self)
        ssfw.login(self.user.login())
        return ssfw


class Log(models.Model):
    user = models.ForeignKey(User)
    message = models.CharField(max_length=200)
    content = models.TextField(default='', blank=True)
    create_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


class Ssfw:
    session = None  # type:requests.Session
    user = None  # type: User

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {'user-agent': 'PyXjtuSsfw/1.0.0'}
        self.session.verify = False
        self.user = None

    def to_dict(self):
        return {
            'cookies': requests.utils.dict_from_cookiejar(self.session.cookies),
            'user': self.user.id,
        }

    def from_dict(self, d):
        # type: (dict) -> None
        self.session.cookies = requests.utils.cookiejar_from_dict(d['cookies'])
        self.user = User.objects.get(id=d['user'])

    def login(self, cas):
        # type: (Cas) -> None
        """登录师生服务"""
        self.user, created = User.objects.get_or_create(user=cas.user)
        if created:
            Log(user=self.user, message='Create user').save()
            self.user.save()
        else:
            if self.user.is_deleted:
                Log(user=self.user, message='Active deleted user').save()
        Log(user=self.user, message='Teacher and student service login').save()
        r = self.session.get(cas.service(u'http://ssfw.xjtu.edu.cn/index.portal'))
        try:
            name = re.search(u'欢迎您：(.*?)</li>', r.text).group(1)
        except AttributeError:
            raise SsfwLoginError(self.user)
        if name != self.user.name:
            Log(user=self.user, message='Update student name', content=name).save()
            self.user.name = name
            self.user.save()
        Log(user=self.user, message='Teacher and student service login ok', content='Student name: %s' % name).save()
