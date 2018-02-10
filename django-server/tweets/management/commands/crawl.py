import os
import sys
import requests
import json
import time

from requests_oauthlib import OAuth1
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ...models import *
from .train import get_client, to_datum

def get_oauth():
    return OAuth1(
        os.environ.get('API_KEY'),
        os.environ.get('API_SECRET'),
        os.environ.get('ACCESS_TOKEN'),
        os.environ.get('ACCESS_SECRET'),
    )

# https://stream.twitter.com/1.1/statuses/sample.json?language=ja
def request_stream(uri, params=None):
    stream = requests.get(
        uri,
        auth=get_oauth(),
        stream=True,
        params=params
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
    if len(list(Tweet.objects.filter(uid=tweet_d['id']))) > 0:
        return None
        
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
    parser.add_argument('--stream', action='store_true')
    parser.add_argument('--train', action='store_true')

  def handle(self, *args, **options):

    label = options['label']
    is_streaming = options['stream'] or False
    train = options['train'] or False
    if train:
        client = get_client()
    if label == 1:
        if is_streaming:
            params = {
                'track': '#PPTP,#ポプテピピック',
                'lang': 'ja',
            }
        else:
            params = {
                'q': '#PPTP OR #ポプテピピック exclude:retweets',
                'lang': 'ja',
                'result_type': 'recent',
                'count': 100,
            }
    else:
        params = {
            'lang': 'ja',
        }
        
    if is_streaming:
        while True:
            try:
                if label == 1:
                    stream = request_stream('https://stream.twitter.com/1.1/statuses/filter.json?', params=params)
                else:
                    stream = request_stream('https://stream.twitter.com/1.1/statuses/sample.json?', params=params)
                for line in stream.iter_lines():
                    tweet_d = json.loads(line)
                    if 'lang' in tweet_d and tweet_d['lang'] == 'ja' and not tweet_d['text'].startswith('RT '):
                        tweet = save_tweet(tweet_d, label)
                        print(tweet.text)
                        if train:
                            datum = to_datum(tweet)
                            client.train([datum])
            except Exception as e:
                print(sys.exc_info())
    else:
        if label == 0:
            sys.stderr.write('We could not get tweets whose label are 0 with REST API')
            exit()
        try:
            while True:
                newest_uid = None
                newest_tweet = Tweet.objects.filter(label=1).order_by('-uid').first()
                if newest_tweet is not None:
                    newest_uid = newest_tweet.uid
                if newest_uid is not None:
                    params['since_id'] = newest_uid
                rest = request_rest('https://api.twitter.com/1.1/search/tweets.json?', params=params)
                tweets_d = json.loads(rest.text)['statuses']
                for tweet_d in tweets_d:
                    tweet = save_tweet(tweet_d, label)
                    if train:
                        datum = to_datum(tweet)
                        client.train([datum])
        except Exception as e:
            print(sys.exc_info())
