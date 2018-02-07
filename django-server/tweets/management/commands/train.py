import os
import sys
import requests
import json
import time
import random

from requests_oauthlib import OAuth1
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ...models import *

import jubatus
from jubatus.common import Datum

def to_datum(tweet):
    text = tweet.text
    text = text.replace('#ポプテピピック', '')
    text = text.replace('#PPTP', '')
    tweet_datum = Datum({
        'text_mecab': text,
        'text_unigram': text,
        'text_bigram': text,
        'text_trigram': text,
    })
    return (str(tweet.label), tweet_datum)

def get_client():
    return jubatus.Classifier(
        os.environ.get('JUBATUS_HOST'),
        int(os.environ.get('JUBATUS_PORT')),
        os.environ.get('JUBATUS_NAME'),
    )

class Command(BaseCommand):
  def handle(self, *args, **options):
      def to_chunks(l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

      all_tweets = list(Tweet.objects.all())
      all_labelled_datumized_tweets = [to_datum(tweet) for tweet in all_tweets]
      client = get_client()
      random.shuffle(all_labelled_datumized_tweets)
      chunks = to_chunks(all_labelled_datumized_tweets, 100)
      for chunk in chunks:
          client.train(chunk)
      client.save()
