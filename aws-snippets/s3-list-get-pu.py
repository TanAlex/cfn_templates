s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

for region in all_region_list:
    template_bucket_name = template_bucket_name_prefix + '-' + region
    default_template_obj = s3.Object(template_bucket_name, default_template_name)
    default_template = json.loads(default_template_obj.get()['Body'].read().decode('utf-8'))

    contents = s3_client.list_objects(Bucket=template_bucket_name)['Contents']
    list_of_account_to_review = []

    for s3_object in contents:
        #Assumes S3 template keys are of the form <12-digit-account-id>.json
        key = s3_object["Key"]

        if not re.match('^[0-9]{12}\.json$', key):
            #Skip this one
            print("Skipping " + key)
            continue

        remote_account_id = key.split(".")[0]

        obj = s3.Object(template_bucket_name, key)
        template = obj.get()['Body'].read().decode('utf-8')

        #Check if the remote Rule template is empty.  If it is, use the default Rule template.
        #template_key = key
        if not template:
            default_obj = s3.Object(template_bucket_name, default_template_name)
            template = default_obj.get()['Body'].read().decode('utf-8')