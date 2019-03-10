import os

from urllib.parse import urlencode
from urllib.request import Request, urlopen

def send_message(msg):
    url = 'https://api.groupme.com/v3/bots/post'

    data = {
        'bot_id'    : os.getenv('GROUPME_BOT_ID'),
        'text'      : msg
    }

    request = Request(url, urlencode(data).encode())
    json = urlopen(request).read().decode()