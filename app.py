import gzip
import io
import json
import os

import firebase_admin
import requests
from firebase_admin import credentials, db
from flask import Flask, request

import cfm_advance
import cfm_schedule
import cfm_standings
import cfm_team
import constants
import groupme
import response_objects
import utils

app = Flask(__name__)

# GroupMe info
groupme_token = os.getenv('GROUPME_TOKEN')
groupme_group_id = os.getenv('GROUPME_GROUP_ID')
groupme_bot_name = os.getenv('GROUPME_BOT_NAME')

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
    '/resign': cfm_team.get_expiring_contracts,
    '/users': cfm_team.get_assigned_teams
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
                    groupme_users_snapshot[groupme_user[0]].update({'gamertag': msg[func_index + 1].lower()})

                    user_to_team_map = {}
                    teams_snapshot = cfm.child('teams').get()

                    print('Find user teams')
                    for team_id, team in teams_snapshot.items():
                        if team['userName']:
                            user_to_team_map[team['userName'].lower()] = team_id
                    
                    print('Associate users to teams')
                    for i, user in enumerate(groupme_users_snapshot):
                        if(user.get('gamertag')):
                            team_id = user_to_team_map.get(user['gamertag'].lower())
                            if team_id:
                                groupme_users_snapshot[i]['teamId'] = team_id

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
            print(f'Found {slash_command} Command')
            if (slash_command == '/help' or slash_command == '/rules'):
                bot_response = SLASH_COMMANDS[slash_command]()
                groupme.send_message(bot_response)

            else:
                base_command = slash_command.split()[0]
                msg, func_index = get_command_index(data, base_command)
                bot_response = SLASH_COMMANDS[slash_command](cfm, msg, func_index)
                groupme.send_message(bot_response, cfm)

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

def does_league_already_exists(firebase_node, id):
    '''Check if ID exists in firebase
    
    Arguments:
        firebase_node {String} -- Firebase node
        id {String} -- ID to search for
    
    Returns:
        Boolean -- True if id is found
    '''

    if cfm.child(firebase_node).get(False, True):
        print(f'{id} exists')
        return True
    
    print(f'{id} does not exists')
    return False


######################################################
# Export Endpoints
######################################################

# Team info export endpoint
@app.route('/exports/<system>/<leagueId>/leagueteams', methods=['POST'])
def league_teams_export(system, leagueId):
    teams = json.loads(request.data)
    print(teams)
    teams = teams['leagueTeamInfoList']
    teams_ref = cfm.child('teams')
    team_map_ref = cfm.child('teamMap')

    if not does_league_already_exists('teams', teams[0]['teamId']):
        print('Deleting teams and team map nodes because new league is being exported')
        teams_ref.delete()
        team_map_ref.delete()

    for team in teams:
        teams_ref.update({team['teamId']: team})
        # Assign team id to associated nicknames
        nicknames = utils.get_team_nicknames(team['abbrName'])
        for nickname in nicknames:
            team_map_ref.update({nickname: f"{team['teamId']}"})

    return 'ok', 200

# Standings export endpoint
@app.route('/exports/<system>/<leagueId>/standings', methods=['POST'])
def standings_export(system, leagueId):
    standings = json.loads(request.data)
    standings = standings['teamStandingInfoList']
    standings_ref = cfm.child('standings')
    conference_map_ref = cfm.child('conferenceMap')
    conference_map = {
        "afc": "",
        "nfc": ""
    }

    if not does_league_already_exists('standings', standings[0]['teamId']):
        print('Deleting standings node because new league is being exported')
        standings_ref.delete()

    for team in standings:
        standings_ref.update({team['teamId']: team})
        # Set conference ids
        if team['conferenceName'].lower() == 'afc' and not conference_map['afc']:
            conference_map['afc'] = team['conferenceId']
        if team['conferenceName'].lower() == 'nfc' and not conference_map['nfc']:
            conference_map['nfc'] = team['conferenceId']

    # Upload conference map
    conference_map_ref.update(conference_map)


    return 'ok', 200

# Weekly info export endpoint
@app.route('/exports/<system>/<leagueId>/week/<weekType>/<weekNumber>/<dataType>', methods=['POST'])
def week_export(system, leagueId, weekType, weekNumber, dataType):
    weeks = json.loads(request.data)
    weekly_ref = cfm.child(f'weeks/{weekType}/{weekNumber}/{dataType}')

    if dataType.lower() == 'schedules':
        schedules = weeks['gameScheduleInfoList']
        
        for i, game in enumerate(schedules):
            weekly_ref.update({i: game}) 

    return 'ok', 200

@app.route('/exports/<system>/<leagueId>/freeagents/roster', methods=['POST'])
def free_agent_export(system, leagueId):
    free_agents = json.loads(request.data)

    return 'ok', 200

# Weekly info export endpoint
@app.route('/exports/<system>/<leagueId>/team/<teamId>/roster', methods=['POST'])
def roster_export(system, leagueId, teamId):
    roster = json.loads(request.data)
    rosters_ref = cfm.child('rosters')

    rosters_ref.update({teamId: roster['rosterInfoList']})

    return 'ok', 200   
