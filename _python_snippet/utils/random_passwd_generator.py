import string
import random


def random_pwd_generator(length, additional_str=''):
    """Generate random password.
    Args:
        length: length of the password
        additional_str: Optional. Input additonal string that is allowed in
                        the password. Default to '' empty string.
    Returns:
        password
    """
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits \
        + additional_str
    # Making sure the password has two numbers and symbols at the very least
    password = ''.join(random.SystemRandom().choice(chars)
                       for _ in range(length-4)) + \
               ''.join(random.SystemRandom().choice(string.digits)
                       for _ in range(2)) + \
               ''.join(random.SystemRandom().choice(additional_str)
                       for _ in range(2))
    return password