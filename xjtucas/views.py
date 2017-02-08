# coding=utf-8
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest
from django.shortcuts import render

from .models import Cas, CasLoginError


def login(request):
    if request.method == 'POST':
        if 'username' not in request.POST or 'password' not in request.POST:
            return HttpResponseBadRequest()

        username = request.POST['username']
        password = request.POST['password']

        err_msgs = []
        if not username:
            err_msgs.append(u'请输入您的用户名（NetID）。')
        if not password:
            err_msgs.append(u'请输入您的密码。')
        if err_msgs:
            return render(request, 'xjtucas/login.html', {'err_msgs': err_msgs, 'username': username})

        try:
            cas = Cas()
            cas.login(username, password)
        except CasLoginError:
            err_msgs.append(u'登录名（NetID）或密码错误，连续输入错误10次账号将冻结3分钟。')
            return render(request, 'xjtucas/login.html', {'err_msgs': err_msgs, 'username': username})

        request.session['cas'] = cas.to_dict()

    if 'cas' in request.session:
        redirect = request.GET.get('redirect', None)
        return render(request, 'xjtucas/login_ok.html', {'redirect': redirect})

    return render(request, 'xjtucas/login.html')


def logout(request):
    try:
        del request.session['cas']
    except KeyError:
        pass
    if 'redirect' in request.GET:
        return render(request, 'xjtucas/logout_ok.html', {'redirect': request.GET['redirect']})
    return render(request, 'xjtucas/logout_ok.html', {'redirect': reverse(login)})
