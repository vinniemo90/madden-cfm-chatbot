import os
import re

from urllib.parse import urlencode
from urllib.request import Request, urlopen

def send_message(msg, db_root = None):
    '''Send message to groupme chat
    
    Arguments:
        message {String} -- Message to post in chat
    '''

    url = 'https://api.groupme.com/v3/bots/post'

    if(mentions_exists):
        data = {
            'bot_id'    : os.getenv('GROUPME_BOT_ID'),
            'text'      : msg,
            'attachments': [add_mentions_attachment(msg, db_root)]
        }

    else:
        data = {
            'bot_id'    : os.getenv('GROUPME_BOT_ID'),
            'text'      : msg
        }

    request = Request(url, urlencode(data).encode())
    json = urlopen(request).read().decode()

def mentions_exists(msg):
    if(msg.find('@') != -1):
        return True
    else:
        return False

def get_groupme_user_ids(mentions, db_root):
    groupme_ids = []
    groupme_users_snapshot = db_root.child('groupMeUsers').get()
    groupme_users_snapshot = [ user.get('user_id') for user in groupme_users_snapshot]

    for user in mentions:
        try:
            user_index = groupme_users_snapshot.index(user[1:])
            groupme_ids.append(groupme_users_snapshot[user_index])
        except ValueError:
            groupme_ids.append('')

    return groupme_ids

def add_mentions_attachment(msg, db_root):
    user_ids = []
    loci = []

    mentions = re.findall('\((.*?)\)',msg)
    indices = [ msg.index(mention) for mention in mentions ]
    lengths = [ len(mention) for mention in mentions ]

    groupme_user_ids = get_groupme_user_ids(mentions, db_root)

    for index, user_id in enumerate(groupme_user_ids):
        if user_id:
            user_ids.append(user_id)
            loci.append([indices[index], lengths[index]])

    return {
        'type': 'mentions',
        'user_ids': user_ids,
        'loci': loci
    }
