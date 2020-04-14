import boto3
import json
import logging
import os
from urllib2 import Request, urlopen, URLError, HTTPError
import requests
import pprint

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def publish_to_slack_handler(event, context):
    # The Slack hook to use
    SLACK_HOOK_URL = os.environ['SlackHookUrl']
    # The Slack channel to send a message to stored in the slackChannel environment variable
    SLACK_CHANNEL = os.environ['SlackChannel']
    for record in event['Records']:
      slack_message = {
          'channel': SLACK_CHANNEL,
          'text': json.loads(record['Sns']['Message'])['TextMessage']
      }
      req = Request(SLACK_HOOK_URL, json.dumps(slack_message))
      try:
          response = urlopen(req)
          response.read()
          logger.info('Message posted to % s ', slack_message['channel'])
      except HTTPError as e:
          logger.error('Unable to publish message:' + record['Sns']['Message'])['TextMessage']
          logger.error('Request failed: % d % s ', e.code, e.reason)
      except URLError as e:
          logger.error('Unable to publish message:' + record['Sns']['Message'])['TextMessage']
          logger.error('Server connection failed: % s ', e.reason)

def publish_to_chime_handler(event, context):
    # The Chime hook to use. This is specific to a room
    CHIME_HOOK_URL = os.environ['ChimeHookUrl']
    for record in event['Records']:
          requests.post(url=CHIME_HOOK_URL, json={ 'Content': json.loads(record['Sns']['Message'])['TextMessage'] })