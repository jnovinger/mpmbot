import requests


class WebAPIError(Exception):
    """ Generic web service error to handle different API call failures """
    pass

def fetch_content(url, headers=None, credentials=None):
    """ Github specific helper method to handle HTTP API calls """
    try:
        req = requests.get(url, auth=credentials, headers=headers)
        if req.status_code != 200:
            raise WebAPIError("Got %s while trying to access API."\
                % req.status_code)

        return req.text
    except Exception, ex:
        raise WebAPIError("error accessing Github: %s" % ex)

def truncate(msg, length):
    """ Shorten to <length> characters, if too long """
    if len(msg) > length:
        msg = msg[0:length - 3] + '...'
    return msg
