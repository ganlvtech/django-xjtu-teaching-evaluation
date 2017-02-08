# coding=utf-8
import HTMLParser
import re


def html_to_text(s):
    return re.sub(r'[\s\x0B\xC2\xA0]+', ' ', HTMLParser.HTMLParser().unescape(re.sub('<.*?>', ' ', s)), re.S).strip()


def shadow_username(s):
    if len(s) < 5:
        return '*' * len(s)
    return s[0] + '*' * (len(s) - 2) + s[-1]


def get_full_path(request):
    # RFC 3986 requires query string arguments to be in the ASCII range.
    # Rather than crash if this doesn't happen, we encode defensively.
    from django.utils.encoding import iri_to_uri, escape_uri_path
    return '%s%s' % (
        escape_uri_path(request.path),
        ('?' + iri_to_uri(request.META.get('QUERY_STRING', ''))) if request.META.get('QUERY_STRING', '') else ''
    )
