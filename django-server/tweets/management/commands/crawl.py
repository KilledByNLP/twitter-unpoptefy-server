import os
import sys
import requests
import json
import time

from requests_oauthlib import OAuth1
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ...models import *

def get_oauth():
    return OAuth1(
        os.environ.get('API_KEY'),
        os.environ.get('API_SECRET'),
        os.environ.get('ACCESS_TOKEN'),
        os.environ.get('ACCESS_SECRET'),
    )

# https://stream.twitter.com/1.1/statuses/sample.json?language=ja
def request_stream(uri):
    stream = requests.get(
        uri,
        auth=get_oauth(),
        stream=True,
    )
    return stream

# https://api.twitter.com/1.1/search/tweets.json?
def request_rest(uri, params=None):
    response = requests.get(
        uri,
        auth=get_oauth(),
        params=params
    )
    return response

def now():
    return time.strftime('%Y-%m-%d %H:%M:%S')

def save_tweet(tweet_d, label):
    users = User.objects.filter(uid=tweet_d['user']['id'])

    if len(list(users)) == 0:
        user = User(
            uid=tweet_d['user']['id'],
            screen_name=tweet_d['user']['screen_name'],
            display_name=tweet_d['user']['name'],
        )
        user.save()
    else:
        user = list(users)[0]
    tweet = Tweet(
        uid=tweet_d['id'],
        text=tweet_d['text'],
        user=user,
        label=label,
        labeled_at=timezone.localtime(timezone.now()),
    )
    tweet.save()
    return tweet

class Command(BaseCommand):

  def add_arguments(self, parser):
    parser.add_argument('label', type=int)

  def handle(self, *args, **options):

    label = options['label']

    if label == 0:
        stream = request_stream('https://stream.twitter.com/1.1/statuses/sample.json?language=ja')
        for line in stream.iter_lines():
            try:
                tweet_d = json.loads(line)
                save_tweet(tweet_d, label)
            except Exception as e:
                print(sys.exc_info())

    if label == 1:
        try:
            while True:
                oldest_uid = None
                oldest_tweet = Tweet.objects.filter(label=1).order_by('uid').first()
                if oldest_tweet is not None:
                    oldest_uid = oldest_tweet.uid
                print(oldest_uid)
                params = {
                    'q': '#PPTP OR #ポプテピピック exclude:retweets',
                    'lang': 'ja',
                    'result_type': 'recent',
                    'count': 100,
                }
                if oldest_uid is not None:
                    params['max_id'] = oldest_uid
                rest = request_rest('https://api.twitter.com/1.1/search/tweets.json?', params=params)
                tweets_d = json.loads(rest.text)['statuses']
                for tweet_d in tweets_d:
                    save_tweet(tweet_d, label)
        except Exception as e:
            print(sys.exc_info())
