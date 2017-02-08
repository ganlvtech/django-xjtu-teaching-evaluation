# coding=utf-8
import re

import requests
from django.db import models
from django.utils import timezone


class UseDeletedUserError(Exception):
    """尝试使用已删除用户"""

    def __init__(self, user):
        # type: (User) -> None
        self.user = user

    def __str__(self):
        return 'Attempted to use deleted user'


class CasLoginError(Exception):
    """用户登录CAS失败，最可能的原因是用户名或密码错误"""

    def __init__(self, user):
        # type: (User) -> None
        self.user = user

    def __str__(self):
        return 'CAS login failed'


class SessionExpiredError(Exception):
    """会话过期，需要重新登录"""

    def __str__(self):
        return 'Session expired. Re-login needed'


class User(models.Model):
    net_id = models.CharField(max_length=32, unique=True)
    password = models.CharField(max_length=50)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True, null=True)
    delete_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.net_id

    @property
    def is_deleted(self):
        # type: () -> bool
        """是否已被标记为删除，被标记为删除的原因之一就是密码错误或者已更改"""
        return self.delete_time is not None

    def login(self):
        """查询用户并登录CAS，返回Cas对象，如果用户不存在，抛出DoesNotExist"""
        if self.is_deleted:
            Log(user=self, message='Attempted to login deleted user').save()
            raise UseDeletedUserError(self)
        Log(user=self, message='Non-password login').save()
        cas = Cas()
        cas.login(self.net_id, self.password)
        return cas


class Log(models.Model):
    user = models.ForeignKey(User)
    message = models.CharField(max_length=200)
    content = models.TextField(default='', blank=True)
    create_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


class Cas:
    session = None  # type: requests.Session
    user = None  # type: User

    def __init__(self):
        """登录CAS并保存session"""
        self.session = requests.Session()
        self.session.headers = {'user-agent': 'PyXjtuCas/1.0.0'}
        self.session.verify = False

    def to_dict(self):
        return {
            'cookies': requests.utils.dict_from_cookiejar(self.session.cookies),
            'user': self.user.id,
        }

    def from_dict(self, d):
        # type: (dict) -> None
        self.session.cookies = requests.utils.cookiejar_from_dict(d['cookies'])
        self.user = User.objects.get(id=d['user'])

    def login(self, net_id, password):
        # type: (unicode, unicode) -> None
        """使用NetID和密码登录CAS"""
        self.user, created = User.objects.get_or_create(net_id=net_id)
        if created:
            Log(user=self.user, message='Create user', content='Password: %s' % password).save()
            self.user.password = password
            self.user.save()
        else:
            if self.user.is_deleted:
                Log(user=self.user, message='Active deleted user').save()
        Log(user=self.user, message='CAS login', content='Using password: %s' % password).save()
        r = self.session.get('https://cas.xjtu.edu.cn/login')
        m = re.search('name="lt" value="(.*?)".*?name="execution" value="(.*?)".*?name="_eventId" value="(.*?)"', r.text, re.S)
        r = self.session.post('https://cas.xjtu.edu.cn/login', data={
            'username': net_id,
            'password': password,
            'code': '',
            'lt': m.group(1),
            'execution': m.group(2),
            '_eventId': m.group(3),
            'submit': '登录'
        })
        if u'成功登录' not in r.text:
            Log(user=self.user, message='CAS login failed').save()
            if self.user.password == password:
                Log(user=self.user, message='User invalid').save()
                self.user.delete_time = timezone.now()
                self.user.save()
            raise CasLoginError(self.user)
        Log(user=self.user, message='CAS login ok').save()
        if self.user.password != password:
            Log(user=self.user, message='Update password', content='New password: %s' % password).save()
            self.user.password = password
            self.user.save()

    def service(self, service):
        # type: (unicode) -> unicode
        """登录CAS的某个服务，返回跳转的链接"""
        Log(user=self.user, message='CAS service login', content="Service's url: %s" % service).save()
        r = self.session.get('https://cas.xjtu.edu.cn/login', params={'service': service})
        try:
            return re.search('url=(.*?)"', r.text).group(1)
        except AttributeError as e:
            raise SessionExpiredError()
