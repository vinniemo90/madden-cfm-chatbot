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
        attachment = add_mentions_attachment(msg, db_root)
        print(f'Groupme Attachment ===> {attachment}')
        data = {
            'bot_id'    : os.getenv('GROUPME_BOT_ID'),
            'text'      : msg,
            'attachments': [attachment]
        }

    else:
        print('No user mentions found')
        data = {
            'bot_id'    : os.getenv('GROUPME_BOT_ID'),
            'text'      : msg
        }

    print('Sending groupme message')
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
    groupme_users_nicknames = [ user.get('nickname') for user in groupme_users_snapshot]
    print(f'GroupMe user id ===> {groupme_users_snapshot}')

    for user in mentions:
        print('Retrieving groupme ids for mentioned users')
        try:
            user_index = groupme_users_nicknames.index(user[1:])
            groupme_ids.append(groupme_users_snapshot[user_index]['user_id'])
        except ValueError:
            print(f'{user[1:]} was mentioned but user does not exists')
            groupme_ids.append('')

    return groupme_ids

def add_mentions_attachment(msg, db_root):
    user_ids = []
    loci = []

    print('Finding all user mentions within message')
    mentions = re.findall('\((.*?)\)',msg)
    indices = [ msg.index(mention) for mention in mentions ]
    lengths = [ len(mention) for mention in mentions ]

    print('Get groupme user ids for each mentioned user')
    groupme_user_ids = get_groupme_user_ids(mentions, db_root)

    print('Generate groupme attachment dictionary')
    for index, user_id in enumerate(groupme_user_ids):
        if user_id:
            user_ids.append(user_id)
            loci.append([indices[index], lengths[index]])

    return {
        'type': 'mentions',
        'user_ids': user_ids,
        'loci': loci
    }
