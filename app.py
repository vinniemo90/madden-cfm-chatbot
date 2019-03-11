import os
import json
import firebase_admin
import io
import gzip
import requests

import cfm_schedule
import cfm_advance
import cfm_team
import cfm_standings
import groupme
import response_objects
import constants
import utils

from firebase_admin import credentials
from firebase_admin import db

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, request

app = Flask(__name__)

# GroupMe info
groupme_token = os.getenv('GROUPME_TOKEN')
groupme_group_id = os.getenv('GROUPME_GROUP_ID')
groupme_bot_name = 'John Madden'

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

SLASH_COMMANDS = {
    '/advance': cfm_advance.advance,
    '/schedule week': cfm_schedule.get_weekly_schedule,
    '/schedule wk': cfm_schedule.get_weekly_schedule,
    '/schedule': cfm_schedule.get_season_schedule,
    '/scores week': cfm_schedule.get_user_weekly_scores,
    '/scores wk': cfm_schedule.get_user_weekly_scores,
    '/standings afc': cfm_standings.get_conf_standings,
    '/standings nfc': cfm_standings.get_conf_standings,
    '/standings':cfm_standings.get_nfl_standings,
    '/cap': cfm_team.get_team_cap,
    '/teams': cfm_team.get_team_info,
    '/stats': cfm_team.get_team_season_stats,
    '/record': cfm_team.get_team_record,
    '/injuries': cfm_team.get_injured_players,
    '/help': utils.get_help_prompt,
    '/rules': utils.get_league_rules,
    '/resign': cfm_team.get_expiring_contracts
}

# Root db reference
cfm = db.reference()

######################################################
# GroupMe Endpoint
######################################################

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()

    # Update users on GroupMe name change
    if data['sender_id'].lower() == 'system' and ('changed name to' in data['text'].lower() or 'added' in data['text'].lower()):
        print('Groupme user changed name or new user added to group')
        request_params = {'token': groupme_token}
        group_members = requests.get(f'https://api.groupme.com/v3/groups/{groupme_group_id}', params = request_params).json()['response']['members']
        print('Updating groupme users info')
        cfm.update({'groupMeUsers': group_members})

    # Set gamertag for groupme user
    elif data['name'] != groupme_bot_name and '/gamertag' in data['text'].lower():
        msg, func_index = get_command_index(data, '/gamertag')
        if(len(msg) > func_index + 1):
                try:
                    print(f"Setting gamertag for {data['name']}")
                    groupme_users_snapshot = cfm.child('groupMeUsers').get()
                    groupme_user = [ i for i, user in enumerate(groupme_users_snapshot) if user['nickname'] == data['name'] ]
                    print(f'Groupme user index {groupme_user}')
                    groupme_users_snapshot[groupme_user[0]].update({'gamertag': msg[func_index + 1].lower()})

                    user_to_team_map = {}
                    teams_snapshot = cfm.child('teams').get()
                    print(teams_snapshot)
                    print('Find user teams')
                    for team_id, team in teams_snapshot.items():
                        if team['userName']:
                            user_to_team_map[team['userName']] = team_id
                    
                    print('Associate users to teams')
                    for i, user in enumerate(groupme_users_snapshot):
                        team_id = user_to_team_map.get(user['gamertag'])
                        if team_id:
                            groupme_users_snapshot[i].update({'teamId': team_id})

                    cfm.update({'groupMeUsers': groupme_users_snapshot})
                    groupme.send_message(constants.GAMERTAG_SUCCESS_MESSAGE)
                
                except Exception as e:
                    print(e)
                    groupme.send_message(constants.UNEXPECTED_ERR_MSG)

        else:
            groupme.send_message(constants.MISSING_GAMERTAG_ERR_MSG)

    elif data['name'] != groupme_bot_name:
        command = [ cmd for cmd in SLASH_COMMANDS.keys() if cmd in data['text'] ]
        if command:
            slash_command = command[0]
            if (slash_command == '/help' or slash_command == '/rules'):
                bot_response = SLASH_COMMANDS[slash_command]()
                groupme.send_message(bot_response)

            else:
                base_command = command[0].split()[0]
                msg, func_index = get_command_index(data, base_command)
                bot_response = SLASH_COMMANDS[slash_command](cfm, msg, func_index)
                groupme.send_message(bot_response)

    return 'ok', 200

def get_command_index(message, command):
    '''Get index of slash command within message
    
    Arguments:
        message {String} -- GroupMe message
        command {String} -- Slash command to search for
    
    Returns:
        Tuple -- (Message as list of strings, index of slash command)
    '''

    msg_as_list = message['text'].lower().split()
    cmd_index = msg_as_list.index(command)

    return msg_as_list, cmd_index


######################################################
# Export Endpoints
######################################################

# Team info export endpoint
@app.route('/exports/<system>/<leagueId>/leagueteams', methods=['POST'])
def league_teams_export(system, leagueId):
    teams = decode_bytes_stream(request)
    teams = teams['leagueTeamInfoList']
    teams_ref = cfm.child('teams')

    for team in teams:
        teams_ref.update({team['teamId']: team})

    return 'ok', 200

# Standings export endpoint
@app.route('/exports/<system>/<leagueId>/standings', methods=['POST'])
def standings_export(system, leagueId):
    standings = decode_bytes_stream(request)
    standings = standings['teamStandingInfoList']
    standings_ref = cfm.child('standings')

    for team in standings:
        standings_ref.update({team['teamId']: team})

    return 'ok', 200

# Weekly info export endpoint
@app.route('/exports/<system>/<leagueId>/week/<weekType>/<weekNumber>/<dataType>', methods=['POST'])
def week_export(system, leagueId, weekType, weekNumber, dataType):
    weeks = decode_bytes_stream(request)
    weekly_ref = cfm.child(f'weeks/{weekType}/{weekNumber}/{dataType}')

    if dataType.lower() == 'schedules':
        schedules = weeks['gameScheduleInfoList']
        
        for i, game in enumerate(schedules):
            weekly_ref.update({i: game}) 

    return 'ok', 200

@app.route('/exports/<system>/<leagueId>/freeagents/roster', methods=['POST'])
def free_agent_export(system, leagueId):
    free_agents = decode_bytes_stream(request)

    return 'ok', 200

# Weekly info export endpoint
@app.route('/exports/<system>/<leagueId>/team/<teamId>/roster', methods=['POST'])
def roster_export(system, leagueId, teamId):
    roster = decode_bytes_stream(request)

    rosters_ref = cfm.child('rosters')
    rosters_ref.update({teamId: roster['rosterInfoList']})

    return 'ok', 200

def decode_bytes_stream(request):
    '''Decode bytes stream
    
    Arguments:
        data {[type]} -- [description]

    Returns:
        String -- json string format of bytes stream
    '''

    # Decompress gzip bytes stream
    buf = io.BytesIO(request.data)
    gzip_f = gzip.GzipFile(fileobj=buf)
    data = gzip_f.read()
    data = data.decode('utf-8')
    return json.loads(data)    
