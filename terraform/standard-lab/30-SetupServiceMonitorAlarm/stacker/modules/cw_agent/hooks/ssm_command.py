from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
#from past.builtins import basestring
import os
import os.path
import stat
import logging
import hashlib
import time
import json

from io import BytesIO as StringIO
#from zipfile import ZipFile, ZIP_DEFLATED
import botocore
#import formic
from troposphere.awslambda import Code
from stacker.session_cache import get_session
from stacker.lookups import extract_lookups
from stacker.lookups.registry import LOOKUP_HANDLERS
from stacker.variables import Variable, VariableValueLookup

logger = logging.getLogger(__name__)

def call_ssm_document(provider, context,  **kwargs):
    instance_ids = kwargs.get('instance_ids')
    if not instance_ids:
        raise ValueError("instance_ids can't be empty")
    # turn "i123, i39-22 ,i22-344" to ['i123', 'i39-22', 'i22-344']
    instances = [ins.strip() for ins in instance_ids.split(',')]
         
    # Always use the global client for s3
    session = get_session(provider.region)
    ssm_client = session.client('ssm')
    #document_name = extract_lookups(kwargs.get('document_name'))
    document_name = kwargs.get('document_name')
    var = Variable("document_name", document_name)
    var.resolve(context, provider)
    document_name = var.value
    logger.info("document_name:%s"%(document_name))
    if not document_name:
        raise ValueError("document_name can't be empty")
    response = ssm_client.send_command(
            InstanceIds=instances,
            DocumentName=document_name,)
            #Parameters={} )

    command_id = response['Command']['CommandId']
    # sleep for a few sec before checking result
    # otherwise you will get botocore.errorfactory.InvocationDoesNotExist: An error occurred (InvocationDoesNotExist) when calling the GetCommandInvocation operation:
    # https://stackoverflow.com/questions/50067035/retrieving-command-invocation-in-aws-ssm
    time.sleep(4)
    for instance in instances:
        output = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance,
            PluginName='InstallSendMetricCronJob'
            )
        try:
            output = json.loads(output)
            print("Instance (%s) %s Result: %s Detail:%s"%(instance,output.PluginName, output.Status,  output.StatusDetails))
        except:
            print(output)
    return True