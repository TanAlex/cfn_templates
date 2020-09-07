#!/usr/bin/env python
"""Module with Elastic IP for VPN server."""
from __future__ import print_function
from os.path import dirname, realpath
import sys

from troposphere import Export, GetAtt, Output, Ref, Sub, ec2

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import CFNString


class VpnEip(Blueprint):
    """Blueprint for setting up the VPN server EIP."""

    VARIABLES = {
        'CustomerName': {'type': CFNString,
                         'description': 'The nickname for the new customer. '
                                        'Must be all lowercase letters, '
                                        'should not contain spaces or special '
                                        'characters, nor should it include '
                                        'any part of EnvironmentName.',
                         'allowed_pattern': '[-_ a-z]*',
                         'default': ''},
        'EnvironmentName': {'type': CFNString,
                            'description': 'Name of Environment',
                            'default': 'common'}
    }

    def add_resources(self):
        """Add resources to template."""
        template = self.template

        # Elastic IPs
        vpnelasticip = template.add_resource(
            ec2.EIP(
                'VPNElasticIP',
                Domain='vpc'
            )
        )
        template.add_output([
            Output(
                'VpnEipPublicIp',
                Description='VPN instance public IP',
                Export=Export(Sub('${AWS::StackName}-VpnEipPublicIp')),
                Value=Ref(vpnelasticip)
            ),
            Output(
                'VpnEipAllocationId',
                Description='AllocationId of the VPN instance public IP',
                Export=Export(Sub('${AWS::StackName}-VpnEipAllocationId')),
                Value=GetAtt(vpnelasticip, 'AllocationId')
            )
        ])

    def create_template(self):
        """Create template (main function called by Stacker)."""
        self.template.add_version('2010-09-09')
        self.template.add_description("Sturdy Platform - Core - VPN Elastic "
                                      "IP - {0}".format(version()))
        self.add_resources()


def version():
    """Call version function from top of repo."""
    root_dir = dirname(dirname(dirname(dirname(realpath(__file__)))))
    if root_dir not in sys.path:
        sys.path.append(root_dir)
    import platform_version  # pylint: disable=import-error
    return platform_version.version()


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context

    print(VpnEip('test',
                 Context({'namespace': 'test'}),
                 None).to_json())
