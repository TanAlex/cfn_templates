#!/usr/bin/env python
## -*- coding: utf-8 -*-
# https://gist.githubusercontent.com/shanedroid/b43054f14b481995b4aeb78bbe821158/raw/ca0f9d0bfbd1c2e053fe8e33de32d55522625a85/find_sg.py
"""Find which Security Groups an IP address belongs to"""
#
import argparse, boto3, pprint, os

pprint = pprint.PrettyPrinter(indent=4).pprint

def parse_args():
    parser = argparse.ArgumentParser(description='Find which Security Groups an IP address belongs to')
    parser.add_argument('-I', '--ipaddress', required=True, dest='ip_address', help='The IP address to search for')
    parser.add_argument('-R', '--region', default='us-east-1', dest='region', help='The AWS region to search in, defaults to "us-east-1"')
    return parser.parse_args()

def main():
    args = parse_args()
    ip_address = args.ip_address + '/32'
    found_sg = set()
    ec2 = boto3.resource('ec2')
    all_sg = list(ec2.security_groups.all())

    print "Querying all ec2 Security Groups for %s :" % args.ip_address

    for sg in all_sg:
        for rule in sg.ip_permissions:
            for ip in rule['IpRanges']:
                if ip['CidrIp'] == ip_address:
                    print "Found '%s' in '%s' (%s):" % (args.ip_address, sg.group_name, sg.group_id)
                    pprint(sg.ip_permissions)
                    found_sg.add(sg.group_id)

    pprint(found_sg)


if __name__ == "__main__":
    main()
