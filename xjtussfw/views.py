# coding=utf-8
import urllib

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

import xjtucas.views
from common.models import get_full_path
from xjtucas.models import Cas, SessionExpiredError
from xjtussfw.models import Ssfw


def index(request):
    return HttpResponseRedirect('/')
    # return render(request, 'xjtussfw/index.html')


def login(request):
    if 'cas' not in request.session:
        return HttpResponseRedirect(reverse('xjtucas.views.login') + '?' + urllib.urlencode({'redirect': get_full_path(request)}))
    cas = Cas()
    cas.from_dict(request.session['cas'])
    ssfw = Ssfw()
    try:
        ssfw.login(cas)
    except SessionExpiredError:
        xjtucas.views.logout(request)
        return HttpResponseRedirect(reverse('xjtucas.views.login') + '?' + urllib.urlencode({'redirect': get_full_path(request)}))
    request.session['ssfw'] = ssfw.to_dict()
    if 'redirect' in request.GET:
        return HttpResponseRedirect(request.GET['redirect'])
    return HttpResponseRedirect(reverse('xjtupj.views.login'))


def logout(request):
    try:
        del request.session['ssfw']
    except KeyError:
        pass
    xjtucas.views.logout(request)
    if 'redirect' in request.GET:
        return HttpResponseRedirect(request.GET['redirect'])
    return HttpResponseRedirect(reverse(index))
