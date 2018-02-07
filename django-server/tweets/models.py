import json


from django.db import models
from django.db.models import *


def to_json(dic):
    return json.dumps(dic, ensure_ascii=True, indent=2)


class User(models.Model):
    uid = BigIntegerField()
    screen_name = models.CharField(max_length=64)
    display_name = models.CharField(max_length=128)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return to_json({
            'id': self.id,
            'uid': self.uid,
            'screen_name': self.screen_name,
            'display_name': self.display_name,
            'created_at': self.created_at,
        })


class Tweet(models.Model):
    uid = BigIntegerField()
    text = TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    label = models.IntegerField(null=True)
    labeled_at = models.DateTimeField(null=True)
    pred_label = models.IntegerField(null=True)
    pred_labeled_at = models.DateTimeField(null=True)

    def __str__(self):
        return to_json({
            'id': self.id,
            'uid': self.uid,
            'text': self.text,
            'user_id': self.user.id,
            'label': self.label,
            'labeled_at': self.labeled_at,
            'pred_label': self.pred_label,
            'pred_labeled_at': self.pred_labeled_at,
        })
