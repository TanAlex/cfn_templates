"""THIS TOOL IS TO GET THE SGS from the old setup.

This will add them to the new squid automation setup.

This needs to be run once after the solution is deployed in
order to find the IPS from the previous solutions and add those to DDB

To run simply sso into the yvr account and run with python
"""
import boto3

ec2_client = boto3.client('ec2', region_name='us-east-1')
custom_filter = [
    {
        'Name': 'tag:aws:cloudformation:stack-name',
        'Values': ['ProdSgsWhitelist']
    }
]

response = ec2_client.describe_security_groups(Filters=custom_filter)
all_ip_permissions = []
all_ip = []
for sg in response['SecurityGroups']:
    all_ip_permissions.extend(sg['IpPermissions'])
for permission in all_ip_permissions:
    all_ip.extend(permission['IpRanges'])

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('ip-whitelist')
all_ip.remove({'CidrIp': '162.246.226.179/32'})
all_ip.remove({'CidrIp': '45.21.92.161/32'})
with table.batch_writer() as batch:
    for ip in all_ip:
        batch.put_item(
            Item={'ip': ip['CidrIp'],
                  'description': ip.get('Description', ' ')})

print(all_ip)
# dynamo_client.batch_write_item(
#     RequestItmes={
#         'ip-whitelist': all_ip
#     }
# )


print(len(response['SecurityGroups']))
print(len(all_ip_permissions))
print(len(all_ip))

print(all_ip)
