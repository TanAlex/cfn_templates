"""importing modules."""
import os
import os.path
import yaml
import json
from stacker.util import get_config_directory


def _get_file(provided_path):
    root = os.path.expanduser(provided_path)
    if not os.path.isabs(root):
        root = os.path.abspath(os.path.join(get_config_directory(), root))
    with open(root) as f:
        return f.read()


def to_json_string(context, provider, **kwargs):
    """Function JSON to String."""
    results = {}

    for name, options in kwargs['yaml_files'].items():
        try:
            results[name] = json.dumps(
                yaml.safe_load(_get_file(options['path']))
            )
        except Exception as err:
            print err
            raise
    return results


def to_json_dict(context, provider, **kwargs):
    """Function JSON to Dict."""
    results = {}

    for name, options in kwargs['yaml_files'].items():
        try:
            results[name] = yaml.safe_load(_get_file(options['path']))
        except Exception as err:
            print err
            raise
    return results
