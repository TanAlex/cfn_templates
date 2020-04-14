import threading
import requests
import json


def send(event, context, response_status, response_data, physical_resource_id,
         logger, reason=None):
    """This function sends status and response data to cloudformation.
    """
    responseUrl = event['ResponseURL']
    logger.debug("CFN response URL: " + responseUrl)

    responseBody = {}
    responseBody['Status'] = response_status
    msg = 'See details in CloudWatch Log Stream: ' + context.log_stream_name
    if not reason:
        responseBody['Reason'] = msg
    else:
        responseBody['Reason'] = str(reason)[0:255] + '... ' + msg
    responseBody['PhysicalResourceId'] =  \
        physical_resource_id or context.log_stream_name
    responseBody['StackId'] = event['StackId']
    responseBody['RequestId'] = event['RequestId']
    responseBody['LogicalResourceId'] = event['LogicalResourceId']
    if response_data and response_data != {} and response_data != []  \
       and isinstance(response_data, dict):
        responseBody['Data'] = response_data

    logger.debug("<<<<<<< Response body >>>>>>>>>>")
    logger.debug(responseBody)
    json_responseBody = json.dumps(responseBody)

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }

    try:
        if responseUrl == 'http://pre-signed-S3-url-for-response':
            logger.info("CloudFormation returned status code:"
                        " THIS IS A TEST OUTSIDE OF CLOUDFORMATION")
            pass
        else:
            response = requests.put(responseUrl,
                                    data=json_responseBody,
                                    headers=headers)
            logger.info("CloudFormation returned status code: "
                        + response.reason)
    except Exception as e:
        logger.error("send(..) failed executing requests.put(..): " + str(e))
        raise


def timeout(event, context, logger):
    """This function is executed just before lambda excecution time out
       to send out time out failure message.
    """
    logger.error("Execution is about to time out, sending failure message")
    send(event, context, "FAILED", None, None, reason="Execution timed out",
         logger=logger)


def cfn_handler(event, context, create, update, delete, logger, init_failed):
    """This handler function calls stack creation, update or deletion
       based on request type and also sends status and response data
       from any of the stack operations back to cloudformation,
       as applicable.
    """
    logger.info("Lambda RequestId: %s CloudFormation RequestId: %s" %
                (context.aws_request_id, event['RequestId']))

    # Define an object to place any response information you would like to send
    # back to CloudFormation (these keys can then be used by Fn::GetAttr)
    response_data = {}

    # Define a physicalId for the resource, if the event is an update and the
    # returned phyiscalid changes, cloudformation will then issue a delete
    # against the old id
    physical_resource_id = None

    logger.debug("EVENT: " + str(event))
    # handle init failures
    if init_failed:
        send(event, context, "FAILED", response_data, physical_resource_id,
             logger, reason="Initialization Failed")
        raise Exception("Initialization Failed")

    # Setup timer to catch timeouts
    t = threading.Timer((context.get_remaining_time_in_millis()/1000.00)-0.5,
                        timeout, args=[event, context, logger])
    t.start()

    try:
        # Execute custom resource handlers
        logger.info("Received a %s Request" % event['RequestType'])
        if event['RequestType'] == 'Create':
            physical_resource_id, response_data = create(event, context)
        elif event['RequestType'] == 'Update':
            physical_resource_id, response_data = update(event, context)
        elif event['RequestType'] == 'Delete':
            delete(event, context)

        # Send response back to CloudFormation
        logger.info("Completed successfully, sending response to cfn")
        send(event, context, "SUCCESS", response_data, physical_resource_id,
             logger=logger)

    # Catch any exceptions, log the stacktrace, send a failure back to
    # CloudFormation and then raise an exception
    except Exception as e:
        logger.error(e, exc_info=True)
        send(event, context, "FAILED", response_data, physical_resource_id,
             reason=e, logger=logger)
    finally:
        t.cancel()