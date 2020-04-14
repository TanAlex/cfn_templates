class HandlerBaseError(Exception):
    '''Base error class'''


class SlackBaseError(HandlerBaseError):
    '''Base Slack Error'''

class SlackApiError(SlackBaseError):
    '''Slack API error class'''
    def __init__(self, response: dict):
        self.msg = 'Slack error - {}'.format(response.get('error'))
        super(HandlerBaseError, self).__init__(self.msg)


class SlackChannelListError(SlackApiError):
    '''Slack publish error'''


class SlackMessageValidationError(SlackBaseError):
    '''Slack message format error'''


class SlackPublishError(SlackApiError):
    '''Slack publish error'''


class SlackInvalidChannelNameError(SlackBaseError):
    '''Slack invalid channel name'''
    def __init__(self, channel: str):
        self.msg = 'invalid channel name - {}'.format(channel)
        super(HandlerBaseError, self).__init__(self.msg)


class SnsPublishError(HandlerBaseError):
    '''SNS publish error'''

# usage
    if r.get('ok') is not True:
        raise SlackChannelListError(r)
    if channel_found is False:
        raise SlackInvalidChannelNameError(channel)