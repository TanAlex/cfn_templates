import boto3
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Dial, Redirect
import random
from pynamodb.models import Model
from pynamodb.attributes import NumberAttribute
import os
from datetime import datetime, timedelta
from botocore.vendored import requests
from botocore.exceptions import ClientError
import time
import json

def hello(event, context):
    """Respond to incoming phone calls with a brief message."""
    stage = event['requestContext']['stage']
    # pulling in account_sid and auth_token from SSM
    ssm = boto3.client('ssm')
    account_sid_param = "/msp_phone_system/twilio_account_sid"
    parameter = ssm.get_parameter(Name=account_sid_param, WithDecryption=True)
    account_sid = parameter['Parameter']['Value']
    auth_token_param = "/msp_phone_system/twilio_auth_token"
    parameter = ssm.get_parameter(Name=auth_token_param, WithDecryption=True)
    auth_token = parameter['Parameter']['Value']
    # pulling in HTTP POST body from event list
    body = event['body']
    # creating python list of body elements
    postList = body.split('&')
    # Looking through list for "Digits" dialed,
    # and assigning to "digitsDialed" object
    i = 0
    while i < len(postList):
        #print(postList[i])  # add back in if you need to see what every item is
        a,b = postList[i].split('=', 1)
        if a == "Digits":
            digitsDialed = b
        i += 1
    print("Checking dialed digits:", digitsDialed)
    # Start our TwiML response
    transmission = VoiceResponse()
    # checking for pin, then compiling text to send
    if digitsDialed == "1":
        # Assigning room
        roomNumber = GetUnusedRoomNumber()
        dial = connectToConfRoom(str(roomNumber))
        transmission.say("Thank you!"
                         " . Please remain on the line while "
                         "we connect you to your on-call engineer."
                         ". Because we have to page an engineer, "
                         "There may be a few minute wait until you"
                         " are connected.")
        transmission.append(dial)
        # Trigger PagerDuty incident without a previously generated incident key
        # Uses Events V2 API - documentation:
        # https://v2.developer.pagerduty.com/docs/send-an-event-events-api-v2
        header = {
            "Content-Type": "application/json"
        }
        summary = ("EMERGENCY CALL ON HOLD - Caller Unverified, please "
                   "check Contacts list before performing work.")
        caanswercall = str(os.environ['CA_engineer_number'] + ",," + str(roomNumber))
        usanswercall = str(os.environ['US_engineer_number'] + ",," + str(roomNumber))
        routing_key = os.environ['routing_key']
        payload = {
            "routing_key": routing_key,
            "event_action": "trigger",
            "payload": {
                "summary": summary,
                "source": "msp-phone-system-{}-callrouter".format(stage),
                "severity": "critical",
                "custom_details": {
                    "Customer_Name": os.environ['Customer_Name'],
                    "CANADA_pickup_call_number": caanswercall,
                    "USA_pickup_call_number": usanswercall
                }
            }
        }
        response = requests.post('https://events.pagerduty.com/v2/enqueue',
                                 data=json.dumps(payload),
                                 headers=header)
    else:
        transmission.say("You Entered. " + digitsDialed + "I'm sorry,"
                         "I am unable to connect your call. Please try again.")
        CustomerPodDirectCallDefault = "/" + stage + "/CustomerPodDirectCallDefault"
        retryredirect = Redirect(CustomerPodDirectCallDefault, method='GET')
        transmission.append(retryredirect)
    return {
        "statusCode": 200,
        "headers": {
        'Content-Type': 'application/xml'
            },
        "body": str(transmission)
        }

def GetUnusedRoomNumber():
    """ 
    Avoid room confliects - all inbound customer calls get a new room 
    """
    roomNumber = random.randrange(1000, 9999, 2)
    print("Checking if conf room ",roomNumber, " exists..." )
    try:
        room = ActiveTwilioConfRooms.get(roomNumber)
        print("room checked already exists.. trying another")
        GetUnusedRoomNumber()
    except ActiveTwilioConfRooms.DoesNotExist:
        print("Room ", str(roomNumber), "does not exist yet, good...")
        currentTime = datetime.utcnow()
        tomorrowTime = currentTime + timedelta(days=1)
        room = ActiveTwilioConfRooms(roomNumber)
        room.ExpirationDay = tomorrowTime.day
        room.ExpirationMonth = tomorrowTime.month
        room.ExpirationYear = tomorrowTime.year
        room.ExpirationTime = expiration_time()
        room.save()
        return(roomNumber)

def expiration_time():
    return int(time.time()) + 86400

def connectToConfRoom(roomNumber):
    """Return TwiML for a moderated conference call."""
    roomName = "Room" + roomNumber
    with Dial() as dial:
        dial.conference(roomName, start_conference_on_enter=True,
            end_conference_on_exit=True)
    return (dial)  

class ActiveTwilioConfRooms(Model):
    """
    A DynamoDB ActiveTwilioConfRooms table
    """
    class Meta:
        table_name = os.environ['Dynamo_Table_Name']
        region = 'us-west-2'
    ConfID = NumberAttribute(hash_key=True)
    ExpirationDay = NumberAttribute(null=True)
    ExpirationMonth = NumberAttribute(null=True)
    ExpirationYear = NumberAttribute(null=True)
    ExpirationTime = NumberAttribute(null=True)
