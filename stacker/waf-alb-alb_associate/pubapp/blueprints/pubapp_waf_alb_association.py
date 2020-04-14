"""Associates resources with a WAF ACL."""
from os.path import dirname, realpath
import sys
import re

from troposphere import wafregional as waf

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import CFNString


def version():
    """Call version function from top of repo."""
    root_dir = dirname(dirname(realpath(__file__)))
    if root_dir not in sys.path:
        sys.path.append(root_dir)
    import module_version  # pylint: disable=import-error
    return module_version.version()


TEMPLATE_DESCRIPTION = 'ALB WAF Associations - {}'.format(
    version()
)


class BlueprintClass(Blueprint):
    """Extends Stacker Blueprint class."""

    VARIABLES = {
        'WafAcl': {
            'type': CFNString,
            'description': 'A unique identifier (ID) for the web ACL.',
            'default': ''
        },
        'Resources': {
            'type': list,
            'description': 'The Amazon Resource Name (ARN) of the '
                           'resource to protect with the web ACL.',
            'default': []
        }
    }

    def create_template(self):
        """Create template (main function called by Stacker)."""
        template = self.template
        variables = self.get_variables()

        self.template.set_version('2010-09-09')

        for resource in variables['Resources']:
            template.add_resource(waf.WebACLAssociation(
                re.sub(r'[\W+_]', '', resource),
                ResourceArn=resource,
                WebACLId=variables['WafAcl'].ref
            ))


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context

    print(BlueprintClass('test', Context({'namespace': 'test'})).to_json({
        'WafAcl': 'dummy-value',
        'Resources': ['aws:aws:dummy']
    }))
