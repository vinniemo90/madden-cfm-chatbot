import os
import json
import firebase_admin
import io
import gzip

from firebase_admin import credentials
from firebase_admin import db

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, request

app = Flask(__name__)

# Create firebase creds file
firebase_creds = {
  "type": os.getenv('FIREBASE_CREDS_TYPE'),
  "project_id": os.getenv('FIREBASE_PROJECT_ID'),
  "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
  "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
  "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
  "client_id": os.getenv('FIREBASE_CLIENT_ID'),
  "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
  "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
  "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER'),
  "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL'),
}

# Initialize firebase connection
cred = credentials.Certificate(firebase_creds)
firebase_admin.initialize_app(cred, {
    'databaseURL' : os.getenv('DATABASE_URL')
})

# Root db reference
cfm = db.reference()

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

@app.route('/exports/<system>/<leagueId>/leagueteams', methods=['POST'])
def league_teams_export(system, leagueId):
    # Decompress gzip bytes stream
    buf = io.BytesIO(request.data)
    gzip_f = gzip.GzipFile(fileobj=buf)
    data = gzip_f.read()
    data = data.decode('utf-8')
    teams = json.loads(data)
    teams = teams['leagueTeamInfoList']
    del data

    teams_ref = cfm.child('teams')

    for team in teams:
        if not team['userName']:
            team['userName'] = ' '

        teams_ref.child(team['teamId']).set(team)

    return 'ok', 200

@app.route('/exports/<system>/<leagueId>/standings', methods=['POST'])
def standings_export(system, leagueId):
    # Decompress gzip bytes stream
    buf = io.BytesIO(request.data)
    gzip_f = gzip.GzipFile(fileobj=buf)
    data = gzip_f.read()
    data = data.decode('utf-8')
    standings = json.loads(data)
    standings = standings['teamStandingInfoList']
    del data

    standings_ref = cfm.child('standings')

    for team in standings:
        standings_ref.child(team['teamId']).set(team)

    return 'ok', 200

@app.route('/exports/<system>/<leagueId>/week/<weekType>/<weekNumber>/<dataType>', methods=['POST'])
def week_export(system, leagueId, weekType, weekNumber, dataType):
    print(request.is_json)
    print(request.mimetype)

    # Decompress gzip bytes stream
    buf = io.BytesIO(request.data)
    gzip_f = gzip.GzipFile(fileobj=buf)
    data = gzip_f.read()
    data = data.decode('utf-8')
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