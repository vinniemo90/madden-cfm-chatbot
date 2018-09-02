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

# Team info to be returned
team_info_dict = {'City':'', 'Mascot':'','Division':'','Ovr Rating':'','Owner':''}

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

    elif data['name'] != 'John Madden' and '/help' in data['text'].lower():
        help_prompt = get_help_prompt()
        send_message('\n'.join(help_prompt))

    elif data['name'] != 'John Madden' and '/rules' in data['text'].lower():
        league_rules = get_league_rules()
        send_message('\n'.join(league_rules))

    elif data['name'] != 'John Madden' and '/teams' in data['text'].lower():
        msg = data['text'].lower().split()
        func_index = msg.index('/teams')
        if(len(msg) > func_index + 1):
            try:
                team_map_snapshot = cfm.child('teamMap').get()
                team_id = team_map_snapshot[msg[func_index + 1].lower()]
                team_info_snapshot = cfm.child('teams').child(team_id).get()

                team_info_dict['City'] = team_info_snapshot['cityName']
                team_info_dict['Mascot'] = team_info_snapshot['displayName']
                team_info_dict['Division'] = team_info_snapshot['divName']
                team_info_dict['Ovr Rating'] = team_info_snapshot['ovrRating']
                if team_info_snapshot['userName']:
                    team_info_dict['Owner'] = team_info_snapshot['userName']
                else:
                    team_info_dict['Owner'] = 'CPU'

                send_message(team_info_dict)
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')

        else:
            send_message("Sorry, I couldn't find a team name associated with your request."
                        " Use '/help' to get a list of commands.")



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
        teams_ref.update({team['teamId']: team})

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
        standings_ref.update({team['teamId']: team})

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

def get_league_rules():
    with open('cfm-rules.json') as rules:
            cfm_rules = json.load(rules)
            return cfm_rules['league rules']

def get_help_prompt():
    with open('cfm-rules.json') as rules:
            cfm_rules = json.load(rules)
            return cfm_rules['help prompt']