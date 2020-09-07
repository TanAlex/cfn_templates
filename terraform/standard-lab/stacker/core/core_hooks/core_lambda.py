"""Wrapper for aws_lambda hook adding support for functions in remote pkgs."""
from os import path

import core_blueprints.aws_lambda.find_code as find_code  # noqa pylint: disable=E0401
import stacker.hooks.aws_lambda as aws_lambda


def upload_remote_lambda_functions(context, provider, **kwargs):
    """Wrap upload_lambda_functions and fix cached paths."""
    functions = {}
    for name, options in kwargs['functions'].items():
        functions[name] = options
        if not path.exists(options['path']):
            functions[name]['path'] = find_code.dirname(options['path'])
    return aws_lambda.upload_lambda_functions(context=context,
                                              provider=provider,
                                              functions=functions)
