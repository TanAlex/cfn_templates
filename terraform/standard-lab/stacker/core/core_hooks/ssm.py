"""Handles tasks related to SSM."""
from builtins import input
import logging
import random
import string

from distutils.version import LooseVersion

from stacker.session_cache import get_session
import stacker
LEGACY_STACKER = LooseVersion(stacker.__version__) < LooseVersion('1.6.0')
if LEGACY_STACKER:
    from stacker.lookups.handlers.output import handler as output_handler  # noqa pylint: disable=no-name-in-module,line-too-long
else:
    from stacker.lookups.handlers.output import OutputLookup  # noqa pylint: disable=no-name-in-module,line-too-long
    output_handler = OutputLookup.handle  # noqa

LOGGER = logging.getLogger(__name__)


def set_parameter(provider, context, **kwargs):  # pylint: disable=W0613
    """Ensure a SSM parameter is set.

    Args:
        provider (:class:`stacker.providers.base.BaseProvider`): provider
            instance
        context (:class:`stacker.context.Context`): context instance

    Returns: boolean for whether or not the hook succeeded.

    """
    parameter_name = kwargs.get('parameter')
    parameter_type = kwargs.get('type', 'String')
    parameter_key_id = kwargs.get('key_id', False)
    parameter_overwrite = kwargs.get('overwrite', False)

    session = get_session(provider.region)
    client = session.client('ssm')

    if parameter_overwrite is False:
        response = client.describe_parameters(
            Filters=[{'Key': 'Name', 'Values': [parameter_name]}]
        )
        if len(response['Parameters']) == 1:
            LOGGER.info('SSM parameter %s already present on AWS; skipping...',
                        parameter_name)
            return True

    if kwargs.get('value', False):
        parameter_value = kwargs['value']
    elif kwargs.get('value_output', False):
        parameter_value = output_handler(
            kwargs.get('value_output'),
            provider=provider,
            context=context
        )
    elif kwargs.get('random', False):
        chars = string.ascii_letters + string.digits
        parameter_value = ''.join(random.choice(chars) for _ in range(25))
    else:
        LOGGER.info('')  # line break to better visually separate next request
        LOGGER.info('Please enter value for SSM parameter %s : ',
                    parameter_name)
        parameter_value = input()
    if parameter_key_id is not False:
        client.put_parameter(
            Name=parameter_name,
            Value=parameter_value,
            Type=parameter_type,
            KeyId=parameter_key_id,
            Overwrite=parameter_overwrite
        )
    else:
        client.put_parameter(
            Name=parameter_name,
            Value=parameter_value,
            Type=parameter_type,
            Overwrite=parameter_overwrite
        )
    return True
