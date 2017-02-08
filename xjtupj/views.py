# coding=utf-8
import urllib

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render

import xjtussfw.views
from common.models import shadow_string, get_full_path, shadow_log
from xjtupj.tasks import evaluate
from xjtussfw.models import Ssfw
from .models import Pj, Log, SessionExpiredError


def log_objects_to_dict(log_objects):
    logs = []
    for l in log_objects:
        logs.append({
            'id': l.id,
            'user': l.user.user.user.net_id,
            'message': l.message,
            'create_time': l.create_time,
        })
    return logs


def index(request):
    if 'pj' not in request.session:
        log_objects = reversed(Log.objects.all().order_by('-id')[:25])
        logs = log_objects_to_dict(log_objects)
        for l in logs:
            l['user'] = shadow_string(l['user'])
            l['message'] = shadow_log(l['message'])
        return render(request, 'xjtupj/index.html', {'login': False, 'logs': logs})
    pj = Pj()
    pj.from_dict(request.session['pj'])
    log_objects = reversed(Log.objects.filter(user=pj.user).order_by('-id')[:25])
    logs = log_objects_to_dict(log_objects)
    return render(request, 'xjtupj/index.html', {'login': True, 'pj': pj, 'logs': logs})


def login(request):
    if 'ssfw' not in request.session:
        return HttpResponseRedirect(reverse('xjtussfw.views.login') + '?' + urllib.urlencode({'redirect': get_full_path(request)}))
    ssfw = Ssfw()
    ssfw.from_dict(request.session['ssfw'])
    pj = Pj()
    try:
        pj.login(ssfw)
    except SessionExpiredError:
        return HttpResponseRedirect(reverse('xjtussfw.views.login') + '?' + urllib.urlencode({'redirect': get_full_path(request)}))
    request.session['pj'] = pj.to_dict()
    evaluate.delay(pj.user.id)
    return HttpResponseRedirect(reverse(index))


def logout(request):
    try:
        del request.session['pj']
    except KeyError:
        pass
    xjtussfw.views.logout(request)
    return render(request, 'xjtupj/logout_ok.html', {'login': False, 'message': u'退出登录成功', 'redirect': reverse(index)})


def invalidate(request):
    pj = Pj()
    pj.from_dict(request.session['pj'])
    pj.user.invalidate()
    logout(request)
    return render(request, 'xjtupj/logout_ok.html', {'login': False, 'message': u'退出登录并停止自动评教成功', 'redirect': reverse(index)})
