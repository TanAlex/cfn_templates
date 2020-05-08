import boto3
import os
import json
import uuid

from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')

TABLE_NAME = os.environ['DYNAMODB_TABLE']
table = dynamodb.Table(TABLE_NAME)


def create(body):
    survey_id = body['survey_id']
    response_id = str(uuid.uuid4())
    response_data = body['response_data']
    table.put_item(
        Item={
            'pk': 'RESPONSE#' + response_id,
            'sk': 'SURVEY#' + survey_id,
            'response_data': response_data
        }
    )
    return json.dumps({"response_id": response_id})


def get(response_id):
    index_pk = Key('pk').eq('RESPONSE#' + response_id)
    response = table.query(
        KeyConditionExpression=index_pk
    )
    return json.dumps(response['Items'][0])


def get_all(survey_id):
    index_pk = Key('sk').eq('SURVEY#' + survey_id)
    index_sk = Key('pk').begins_with('RESPONSE#')
    expression = index_pk & index_sk
    response = table.query(
        IndexName='sk-pk-index',
        KeyConditionExpression=expression
    )
    return json.dumps(response['Items'])
