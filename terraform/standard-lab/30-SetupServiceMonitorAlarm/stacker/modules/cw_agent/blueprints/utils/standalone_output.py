"""Output CFN template for a Blueprint."""

from stacker.lookups.handlers.file import parameterized_codec
from stacker.variables import Variable


def json(blueprint, userdata_dict=None, function_dict=None):
    """Turn a stacker blueprint into CloudFormation JSON."""
    if userdata_dict is None:
        userdata_dict = {}
    if function_dict is None:
        function_dict = {}

    # Check the blueprint for CFN parameters in its variables, and define bogus
    # values for those parameters so the template can be generated.
    # Easiest check to find variables that are CFN parameters (and not native
    # python types) seems to be looking for the 'parameter_type' attribute
    test_variables = []
    for key, value in blueprint.defined_variables().iteritems():
        if hasattr(value['type'], 'parameter_type'):
            test_variables.append(Variable(key, 'dummy_value'))

    # Populate the userdata via the file lookup
    for userdata in userdata_dict.iteritems():
        parameterized_b64 = parameterized_codec(open(userdata[1], 'r').read(),
                                                True)  # base64
        test_variables.append(Variable(userdata[0],
                                       parameterized_b64))
    # Populate the lambda functions via the file lookup
    for function in function_dict.iteritems():
        parameterized = parameterized_codec(open(function[1], 'r').read(),
                                            False)  # base64
        test_variables.append(Variable(function[0],
                                       parameterized))

    blueprint.resolve_variables(test_variables)
    print blueprint.render_template()[1]
