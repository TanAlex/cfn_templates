#!/usr/bin/env python
## -*- coding: utf-8 -*-
# https://gist.githubusercontent.com/shanedroid/6dace799c4ccb31546d8f4e3eed5f0e4/raw/daa23c4637936104204d7eaf8164c53dcf84a7cd/nuke_sg.py
"""Nuke any Unused EC2 Security Groups"""
import argparse, boto3, pprint
from botocore.exceptions import ClientError
from itertools import chain

pprint = pprint.PrettyPrinter(indent=4).pprint

def parse_args():
    parser = argparse.ArgumentParser(description='Nuke any Unused EC2 Security Groups')
    parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='Run the script with debugging enabled. Defaults to FALSE')
    parser.add_argument('--delete', dest='delete_orphans', action='store_true', help='DELETE all Orphaned Security Groups, this is not the default, must be set with arg.')
    parser.add_argument('--no-delete', dest='delete_orphans', action='store_false', help='DO NOT DELETE all Orphaned Security Groups, this is the default.')
    parser.set_defaults(delete_orphans=False)
    parser.add_argument('-n','--nomads', nargs='+', default=['default'], help='List of Nomad Security Groups\' Names that should be kept even if they are orphaned. Defaults to the "default" SG in the VPC.')
    return parser.parse_args()

def purge_sgs(*sgs):
    ec2 = boto3.resource('ec2')
    for sg in list(chain.from_iterable(sgs)):
        security_group = ec2.SecurityGroup(sg)
        print "Deleting Security Group '%s' . . ." % sg
        try:
            response = security_group.delete(DryRun=False,GroupName=sg)
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                print "%s has been deleted." % sg
                if debug:
                    pprint(response)
            else:
                pprint(response)
        except ClientError as e:
            if e.response['Error'].get('Code') == 'DryRunOperation':
                print "'%s' would have been deleted" % sg
            else:
                print "Error: '%s' could not be deleted" % sg

def main():
    args = parse_args()
    global debug
    debug = args.debug

    # Known Orphaned SGs that we intend on keeping and not deleting
    nomad_sgs = set(args.nomads)

    ec2 = boto3.resource('ec2')
    ec2_instances = list(ec2.instances.all())

    # All VPC SGs
    all_sgs = list(ec2.security_groups.all())
    sgs_ids = set([sg.group_id for sg in all_sgs])
    if debug:
        print len(all_sgs), 'Security Groups Found:'
        pprint(set(ec2.SecurityGroup(sg).group_name for sg in sgs_ids))

    # SGs in use by EC2 instances
    ec2_used_sgs = set([sg['GroupId'] for inst in ec2_instances for sg in inst.security_groups])
    if debug:
        print len(ec2_used_sgs), 'Security Groups in use by EC2 instances:'
        pprint(set(ec2.SecurityGroup(sg).group_name for sg in ec2_used_sgs))

    rds = boto3.client('rds')
    rds_instances = list(rds.describe_db_instances()['DBInstances'])

    # SGs in use by RDS instances
    rds_used_sgs = set([sg['VpcSecurityGroupId'] for rds in rds_instances for sg in rds['VpcSecurityGroups']])
    if debug:
        print len(rds_used_sgs), 'Security Groups in use by RDS instances:'
        pprint(set(ec2.SecurityGroup(sg).group_name for sg in rds_used_sgs))


    elb = boto3.client('elbv2')
    elb_instances = list(elb.describe_load_balancers()['LoadBalancers'])

    # SGs in use by ELBv2 instances
    elb_used_sgs = set(sg for elb in elb_instances for sg in elb['SecurityGroups'])
    if debug:
        print len(elb_used_sgs), 'Security Groups in use by ELBv2 instances:'
        pprint(set(ec2.SecurityGroup(sg).group_name for sg in elb_used_sgs))

    # SGs associated with EC2, ELB, RDS
    used_sgs = ec2_used_sgs.union(rds_used_sgs, elb_used_sgs)

    # Orphaned SGs
    unused_sgs = set(ec2.SecurityGroup(sg).group_name for sg in (sgs_ids - used_sgs)) - nomad_sgs

    print 'Total SGs:', len(all_sgs)
    print 'SGS attached to instances:', len(used_sgs)
    print 'Orphaned SGs:', len(unused_sgs)
    if debug:
        print 'Orphaned SG names:'
        print(unused_sgs)

    if args.delete_orphans:
        print 'Deleting Orphaned Security Groups . . .'
        purge_sgs(unused_sgs)

if __name__ == "__main__":
    main()