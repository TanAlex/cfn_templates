
"""
os.environ.get
os.path.join(os.path.dirname(__file__), '../slack-message-schema.json')

"""
# https://github.com/ServerlessOpsIO/aws-sns-to-slack-publisher/blob/master/handlers/aws_sns_to_slack_publisher.py
'''Publish message from SNS to Slack'''

import json
import logging
import os
import sys

from boolean import boolean
import boto3
from botocore.exceptions import ClientError
import jsonschema
from slackclient import SlackClient
from tenacity import retry, retry_if_exception_type, stop_after_delay, wait_exponential

log_level = os.environ.get('LOG_LEVEL', 'INFO')
logging.root.setLevel(logging.getLevelName(log_level))  # type: ignore
_logger = logging.getLogger(__name__)

SLACK_API_TOKEN = os.environ.get('SLACK_API_TOKEN')
SLACK_DEFAULT_CHANNEL = os.environ.get('SLACK_DEFAULT_CHANNEL')
SLACK = SlackClient(SLACK_API_TOKEN)
SLACK_SCHEMA_FILE_PATH = os.path.join(os.path.dirname(__file__), '../slack-message-schema.json')
with open(SLACK_SCHEMA_FILE_PATH) as f:
    SLACK_MESSAGE_SCHEMA = json.load(f)

SNS_PUBLISH_RESPONSE = boolean(os.environ.get('SNS_PUBLISH_RESPONSE', 'false'))
RESPONSE_SNS_TOPIC_ARN = os.environ.get('RESPONSE_SNS_TOPIC_ARN')
SNS = boto3.client('sns')


class HandlerBaseError(Exception):
    '''Base error class'''


class SlackBaseError(HandlerBaseError):
    '''Base Slack Error'''

class SlackApiError(SlackBaseError):
    '''Slack API error class'''
    def __init__(self, response: dict):
        self.msg = 'Slack error - {}'.format(response.get('error'))
        super(HandlerBaseError, self).__init__(self.msg)


class SlackChannelListError(SlackApiError):
    '''Slack publish error'''