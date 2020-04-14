# https://github.com/awslabs/aws-s3snapshot/blob/master/s3snapshot/s3snapshot.py

def send_sns_message(sns_topic, subject, msg, msg_sms=None, msg_email=None,
                     msg_apns=None, msg_gcm=None):
    """
    This function send SNS message to specific topic and can format different
    mesages to e-mail, SMS, Apple iOS and Android
    """
    client_sns = boto3.client('sns')
    sns_arn = sns_topic

    sns_body = dict()
    sns_body['default'] = msg
    sns_body['email'] = msg_email or msg
    sns_body['sms'] = msg_sms or msg
    sns_body['APNS'] = {'aps': {'alert': msg_apns or msg}}
    sns_body['GCM'] = {'data': {'message': msg_gcm or msg}}

    client_sns.publish(
        TargetArn=sns_arn,
        Subject=subject,
        MessageStructure='json',
        Message=json.dumps(sns_body)
    )
