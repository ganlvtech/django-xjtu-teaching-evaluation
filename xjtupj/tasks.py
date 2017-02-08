# coding=utf-8

from celery.task import task

from .models import User


@task
def evaluate_all():
    import django
    django.setup()
    users = User.objects.iterator()
    for user in users:
        if not user.is_deleted:
            user.evaluate()


@task
def evaluate(id):
    import django
    django.setup()
    user = User.objects.get(id=id)
    if not user.is_deleted:
        user.evaluate()
