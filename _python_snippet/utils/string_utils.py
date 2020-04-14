import re


def sanitize(name, space_allowed=False, replace_with_character='_'):
    """Sanitizes input string.
    Replaces any character other than [a-zA-Z0-9._-] in a string
    with a specified character (default '_').
    Args:
        name: Input string
        space_allowed (optional):
            Is there a space in the input string. Default to false.
        replace_with_character (optional):
            Character to replace the target character with. Default to '_'.
    Returns:
        Sanitized string
    Raises:
    """
    if space_allowed:
        sanitized_name = re.sub(r'([^\sa-zA-Z0-9._-])',
                                replace_with_character,
                                name)
    else:
        sanitized_name = re.sub(r'([^a-zA-Z0-9._-])',
                                replace_with_character,
                                name)
    return sanitized_name


