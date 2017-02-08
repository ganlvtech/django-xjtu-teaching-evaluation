# coding=utf-8

from celery.task import task

from .models import User, Log


@task
def evaluate_all():
    for i in range(0, 2):
        users = User.objects.iterator()
        for user in users:
            if not user.is_deleted:
                try:
                    user.evaluate()
                except Exception as e:
                    Log(user=user, message='Auto evaluating error', content='Error message: %s' % e.message).save()
                    raise e


@task
def evaluate(id):
    for i in range(0, 2):
        user = User.objects.get(id=id)
        user.evaluate()
