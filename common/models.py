# coding=utf-8
import HTMLParser
import re


def html_to_text(s):
    return re.sub(r'[\s\x0B\xC2\xA0]+', ' ', HTMLParser.HTMLParser().unescape(re.sub('<.*?>', ' ', s)), re.S).strip()


def shadow_string(s, min_len=5):
    if len(s) < min_len:
        return '*' * len(s)
    return s[0] + '*' * (len(s) - 2) + s[-1]


def shadow_log(s, min_len=5):
    l = s.split(': ')
    if len(l) <= 1:
        return s
    return l[0] + ': ' + shadow_string(l[1], min_len)


def get_full_path(request):
    # RFC 3986 requires query string arguments to be in the ASCII range.
    # Rather than crash if this doesn't happen, we encode defensively.
    from django.utils.encoding import iri_to_uri, escape_uri_path
    return '%s%s' % (
        escape_uri_path(request.path),
        ('?' + iri_to_uri(request.META.get('QUERY_STRING', ''))) if request.META.get('QUERY_STRING', '') else ''
    )


def encoded_dict(in_dict):
    out_dict = {}
    for k, v in in_dict.iteritems():
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):
            # Must be encoded in UTF-8
            v.decode('utf8')
        out_dict[k] = v
    return out_dict
