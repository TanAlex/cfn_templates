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
from io import BytesIO as StringIO
#from zipfile import ZipFile, ZIP_DEFLATED
import botocore
#import formic
from troposphere.awslambda import Code
from stacker.session_cache import get_session
from stacker.variables import Variable, VariableValueLookup
import json
from string import Template
import re

logger = logging.getLogger(__name__)

def upload_to_s3(provider, context,  **kwargs):
    custom_bucket = kwargs.get('bucket')
    if not custom_bucket:
        bucket_name = context.bucket_name
        logger.info("upload_to_s3: using default bucket from stacker: %s",
                    bucket_name)
    else:
        bucket_name = custom_bucket
        logger.info("upload_to_s3: using custom bucket: %s", bucket_name)
         
    # Always use the global client for s3
    session = get_session(provider.region)
    s3_cnn = session.client('s3')
    file_name = kwargs.get('file_name')



    key_name = kwargs.get('key_name')
    content = open(file_name, 'r').read()
    # replace possible variable placeholder in the file content to its value
    # for example: {{service_name}} will be replaced by the value in kwargs
    for k in kwargs:
        v = kwargs[k]
        regExp = "\{\{\s*%s\s*\}\}"%(k)
        content = re.sub(
            regExp, 
            v, 
            content
        )

    if(content is None):
        raise ValueError("Can't open {}".format(file_name))
    
    return _upload_code(s3_cnn, bucket_name, key_name, content )



def _upload_code(s3_conn, bucket, key_name, content):
    logger.info('upload_s3: uploading %s', key_name)
    s3_conn.put_object(Bucket=bucket, Key=key_name, Body=content)
    return Code(S3Bucket=bucket, S3Key=key_name)
