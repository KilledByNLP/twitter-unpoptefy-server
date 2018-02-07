import json
import os
import traceback

from django.shortcuts import render
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import jubatus
from jubatus.common import Datum

# Create your views here.
@csrf_exempt
def index(request):
    client = jubatus.Classifier(
        os.environ.get('JUBATUS_HOST'),
        int(os.environ.get('JUBATUS_PORT')),
        os.environ.get('JUBATUS_NAME'),
    )
    try:
        tweets = json.loads(request.body.decode('utf-8'))
        tweet_datums = [Datum({
            'text_mecab': tweet['body'],
            'text_unigram': tweet['body'],
            'text_bigram': tweet['body'],
            'text_trigram': tweet['body']
        }) for tweet in tweets]
        results = client.classify(tweet_datums)
        tweet_labels = [max(result, key = lambda x: x.score).label for result in results]
        scores = [[label_result.score for label_result in result] for result in results]
        _ = [tweet.update({'label': int(label), 'score': score}) for tweet, label, score in zip(tweets, tweet_labels, scores)]

        return JsonResponse({
            'status': True,
            'data': tweets
        })
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({
            'status': False,
            'data': []
        })
