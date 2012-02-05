import requests

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

def shorten(msg):
    """ Shorten to 50 characters, if too long """
    if len(msg) > 50:
        msg = msg[0:47] + '...'
    return msg
