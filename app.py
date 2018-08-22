import os
import json

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()

    # We don't want to reply to ourselves:
    if data['name'] != 'John Madden' and 'john madden' in data['text'].lower():
        msg = f"{data['name']}, you sent '{data['text']}'"
        send_message(msg)

    elif '/rules' in data['text'].lower():
        with open('cfm-rules.json') as rules:
            cfm_rules = json.load(rules)
            league_rules = cfm_rules['league rules']
            send_message('\n'.join(league_rules))

    return 'ok', 200

@app.route('/exports/<path:endpoint>', methods=['POST'])
def madden_export(endpoint):
    data = request.get_json()
    print(data)

    return 'ok', 200


def send_message(msg):
    url = 'https://api.groupme.com/v3/bots/post'

    data = {
        'bot_id'    : os.getenv('GROUPME_BOT_ID'),
        'text'      : msg
    }

    request = Request(url, urlencode(data).encode())
    json = urlopen(request).read().decode()