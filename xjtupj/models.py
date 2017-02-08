# coding=utf-8
import datetime
import random
import re
import urllib

import requests
from django.db import models
from django.utils import timezone

from common.models import html_to_text
from xjtussfw.models import User as SsfwUser, Ssfw


class UseDeletedUserError(Exception):
    """尝试使用已删除用户"""

    def __init__(self, user):
        # type: (User) -> None
        self.user = user

    def __str__(self):
        return 'Attempted to use deleted user'


class SessionExpiredError(Exception):
    """会话过期，需要重新登录"""

    def __str__(self):
        return 'Session expired. Re-login needed'


class User(models.Model):
    user = models.OneToOneField(SsfwUser, related_name='pj_user_set')
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True, null=True)
    delete_time = models.DateTimeField(null=True, blank=True)
    lock_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.user.net_id

    def invalidate(self):
        """使用户无效"""
        if self.is_deleted:
            return False
        Log(user=self, message='User deleted').save()
        self.delete_time = timezone.now()
        self.save()
        return True

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
        """自动登录评教系统"""
        pj = Pj()
        if self.is_deleted:
            Log(user=self, message='Attempted to login deleted user').save()
            raise UseDeletedUserError(self)
        pj.login(self.user.login())
        return pj

    @property
    def is_locked(self):
        """lock_time为None表示没有锁，lock_time与现在的时间相差超过一小时也自动解锁"""
        if self.lock_time is None:
            return False
        elif timezone.now() - self.lock_time > datetime.timedelta(hours=1):
            self.unlock()
            return False
        return True

    def lock(self):
        """加锁"""
        Log(user=self, message='User locked').save()
        self.lock_time = timezone.now()
        self.save()

    def unlock(self):
        """解锁"""
        Log(user=self, message='User unlocked').save()
        self.lock_time = None
        self.save()

    def evaluate(self):
        """登录CAS、登录师生服务、列出课程信息、自动评教，一条龙服务"""
        if self.is_locked:
            return False
        pj = self.login()
        pj.evaluate()
        return True


class Log(models.Model):
    user = models.ForeignKey(User)
    message = models.CharField(max_length=200)
    content = models.TextField(default='', blank=True)
    create_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


class Course:
    def __init__(self, pj):
        # type: (Pj) -> None
        self.session = requests.Session()
        self.session.headers = {'user-agent': 'PyXjtuTeachingEvaluation/1.0.0'}
        self.session.verify = False
        self.session.cookies = pj.session.cookies
        self.user = pj.user  # type: User
        self.week = pj.week  # type: unicode
        self.school = ''  # type: unicode
        self.code = ''  # type: unicode
        self.name = ''  # type: unicode
        self.times = ''  # type: unicode
        self.teacher = ''  # type: unicode
        self.type = ''  # type: unicode
        self.status = ''  # type: unicode
        self.action = ''  # type: unicode
        self.url = ''  # type: unicode

    @property
    def is_finished(self):
        """是否已评教"""
        return self.status == u'已评教'

    def __str__(self):
        return self.name

    @property
    def text(self):
        """文字版课程详情"""
        return u'School: %s\nCode: %s\nName: %s\nTimes: %s\nTeacher: %s\nType: %s\nStatus: %s' % (self.school, self.code, self.name, self.times, self.teacher, self.type, self.status)

    def faker(self):
        """生成总体评价、评估意见"""
        return u'很好'

    def evaluate(self):
        """本门课程评教，返回是否评教"""
        Log(user=self.user, message='One course start evaluating', content=self.text).save()
        if self.is_finished:
            Log(user=self.user, message='One course already evaluated').save()
            return False
        if not self.url:
            Log(user=self.user, message='One course cannot evaluate').save()
            return False
        t = self.session.get(self.url).text
        Log(user=self.user, message='One course load page ok').save()
        try:
            post_url = 'http://ssfw.xjtu.edu.cn/index.portal' + re.search('post" action="(.*?)"', t).group(1)
            post_fields = urllib.urlencode({
                'wid_pgjxb': re.search('wid_pgjxb" value="(.*?)"', t).group(1),
                'wid_pgyj': re.search('wid_pgyj" value="(.*?)"', t).group(1),
                'type': 2,
                'sfytj': re.search('sfytj" value="(.*?)"', t).group(1),
                'pjType': re.search('pjType" value="(.*?)"', t).group(1),
                'wid_pjzts': re.search('wid_pjzts" value="(.*?)"', t).group(1),
                'status': re.search('status" value="(.*?)"', t).group(1),
                'ztpj': self.faker(),
                'sfmxpj': re.search('sfmxpj" value="(.*?)"', t).group(1)
            })
            trs = re.finditer(u'教师评价(.*?)</tr>', t, re.S)
            for tr in trs:
                t1 = tr.group(1)
                m_wid = re.search('(wid_.*?)" type="hidden" value="(.*?)"', t1)
                m_qz = re.search('(qz_.*?)" type="hidden" value="(.*?)"', t1)
                m_pfdj = list(re.finditer('(pfdj_.*?)"  value="(.*?)"', t1))[random.randint(0, 1)]
                post_fields += '&' + urllib.urlencode({
                    'zbbm': re.search('zbbm" type="hidden" value="(.*?)"', t1).group(1),
                    m_wid.group(1): m_wid.group(2),
                    m_qz.group(1): m_qz.group(2),
                    m_pfdj.group(1): m_pfdj.group(2),
                })
            post_fields += '&' + urllib.urlencode({
                'pgyj': self.faker(),
                'actionType': 2
            })
        except AttributeError:
            raise SessionExpiredError()
        Log(user=self.user, message='One course build form ok', content='POST url: %s\nPOST body: %s' % (post_url, post_fields)).save()
        self.session.post(post_url, data=post_fields)
        Log(user=self.user, message='One course evaluation ok').save()
        return True


class Pj:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {'user-agent': 'PyXjtuTeachingEvaluation/1.0.0'}
        self.session.verify = False
        self.user = None  # type: User
        self.week = ''  # type: unicode
        self.courses = []  # type: list

    def to_dict(self):
        courses = []
        for course in self.courses:
            courses.append({
                'school': course.school,
                'code': course.code,
                'name': course.name,
                'times': course.times,
                'teacher': course.teacher,
                'type': course.type,
                'status': course.status,
                'action': course.action,
                'url': course.url,
            })
        return {
            'cookies': requests.utils.dict_from_cookiejar(self.session.cookies),
            'user': self.user.id,
            'week': self.week,
            'courses': courses,
        }

    def from_dict(self, d):
        # type: (dict) -> None
        self.session.cookies = requests.utils.cookiejar_from_dict(d['cookies'])
        self.user = User.objects.get(id=d['user'])
        self.week = d['week']  # type: unicode
        self.courses = []
        for course in d['courses']:
            c = Course(self)
            c.school = course['school']
            c.code = course['code']
            c.name = course['name']
            c.times = course['times']
            c.teacher = course['teacher']
            c.type = course['type']
            c.status = course['status']
            c.action = course['action']
            c.url = course['url']
            self.courses.append(c)

    def login(self, ssfw):
        # type: (Ssfw) -> None
        """登录，并列出所有课程"""
        self.user, created = User.objects.get_or_create(user=ssfw.user)
        if created:
            self.user.save()
            Log(user=self.user, message='Create user').save()
        else:
            if self.user.is_deleted:
                Log(user=self.user, message='Active deleted user').save()
                self.user.delete_time = None
                self.user.save()
        self.session.cookies = ssfw.session.cookies
        Log(user=self.user, message='Get teaching evaluation list').save()
        t = self.session.get('http://ssfw.xjtu.edu.cn/index.portal?.p=Znxjb20ud2lzY29tLnBvcnRhbC5zaXRlLmltcGwuRnJhZ21lbnRXaW5kb3d8ZjExNjF8dmlld3xub3JtYWx8YWN0aW9uPXF1ZXJ5').text
        try:
            self.week = html_to_text(re.search('pc_df".*value="(.*?)"', t).group(1))
            t = re.search('<tbody>(.*?)</tbody>', t, re.S).group(1)
            ms = re.finditer('<tr.*?>\s*?<td>(.*?)</td>\s*?<td>(.*?)</td>\s*?<td>(.*?)</td>\s*?<td>(.*?)</td>\s*?<td>(.*?)</td>\s*?<td>(.*?)</td>\s*?<td>(.*?)</td>\s*?<td>(.*?)</td>\s*?</tr>', t, re.S)
            self.courses = []
            for m in ms:
                c = Course(self)
                c.week = self.week
                c.school = html_to_text(m.group(1))
                c.code = html_to_text(m.group(2))
                c.name = html_to_text(m.group(3))
                c.times = html_to_text(m.group(4))
                c.teacher = html_to_text(m.group(5))
                c.type = html_to_text(m.group(6))
                c.status = html_to_text(m.group(7))
                c.action = html_to_text(m.group(8))
                try:
                    c.url = 'http://ssfw.xjtu.edu.cn/index.portal' + re.search('<a href="(.*?)">', m.group(8)).group(1)
                except AttributeError:
                    pass
                self.courses.append(c)
        except AttributeError:
            raise SessionExpiredError()
        Log(user=self.user, message='Get teaching evaluation list ok').save()

    def evaluate(self):
        """自动评教"""
        if self.user.is_locked:
            return False
        if not self.courses:
            return False
        Log(user=self.user, message='Auto teaching evaluate start').save()
        self.user.lock()
        for course in self.courses:
            course.evaluate()
        self.user.unlock()
        Log(user=self.user, message='Auto teaching evaluate finished').save()
        return True
