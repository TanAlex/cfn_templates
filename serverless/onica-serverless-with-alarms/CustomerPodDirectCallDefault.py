import boto3
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
import os

def hello(event, context):
    """Respond to incoming phone calls with a brief message."""
    stage = event['requestContext']['stage']
    print("Starting hello function...")
    # Start our TwiML response
    transmission = VoiceResponse()
    # Read a message aloud to the caller
    processPress1Action = "/" + stage + "/processPress1Action"
    print("processPinActionURI:", processPress1Action)
    Name = os.environ['Customer_Name']
    transmission.say("Welcome to On-a-ca. . . You have "
                     "reached the Cloud Ops Pilot telephone support "
                     "center for " + Name, voice='man')
    gather = Gather(numDigits=1, action=processPress1Action)
    gather.say("To be connected to your assigned on-call engineer,"
               " Please press one now. . . ", loop=1)
    transmission.append(gather)

    return {
    "statusCode": 200,
    "headers": {
    'Content-Type': 'application/xml'
        },
    "body": str(transmission)
    }
