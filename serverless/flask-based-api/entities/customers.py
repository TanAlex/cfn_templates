import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ['DYNAMODB_TABLE']
table = dynamodb.Table(TABLE_NAME)


def create(body):
    customer_id = body['customer_id']
    profile_data = body['profile_data']
    item = {
        'pk': 'CUSTOMER#' + customer_id,
        'sk': 'PROFILE#' + customer_id,
        'profile_data': profile_data
    }
    table.put_item(Item=item)
    return json.dumps(item)


def get(customer_id):
    item = table.get_item(
        Key={
            'pk': 'CUSTOMER#' + customer_id,
            'sk': 'PROFILE#' + customer_id
        }
    )['Item']
    return json.dumps(item)
