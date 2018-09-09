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

# Team stats to be returned
team_stats_dict = {'Team':'','Team Rank':'', 'Prev. Team Rank':'', 'Pts For Rank':'', 'Pts Against Rank':'', 'Off Total Yds Rank':'', 'Off Pass Yds Rank':'','Off Rush Yds Rank':'', 'Def Total Yds Rank':'', 'Def Pass Yds Rank':'','Def Rush Yds Rank':'', 'TO Diff':''}

# Team cap info to be returned
team_cap_dict = {'Team':'', 'Cap Room': '', 'Cap Spent': '', 'Cap Available': ''}

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

    elif data['name'] != 'John Madden' and ('/schedule week' in data['text'].lower() or '/schedule wk' in data['text'].lower()):
        msg = data['text'].lower().split()
        func_index = msg.index('/schedule')
        if(len(msg) > func_index + 2):
            try:
                team_snapshot = cfm.child('teams').get()
                user_team_ids = [ team['teamId'] for team_id, team in team_snapshot.items() if team['userName'] ]
                schedule_snapshot = cfm.child(f'weeks/reg/{msg[func_index + 2]}/schedules').get()
                
                user_games = []
                schedule = []
                for game_info in schedule_snapshot:
                    if game_info['awayTeamId'] in user_team_ids and game_info['homeTeamId'] in user_team_ids:
                        user_games.append((game_info['homeTeamId'], game_info['awayTeamId']))
                        print('finished if statement')

                if user_games:
                    for home_team_id, away_team_id in user_games:
                        print('inside team mapping')
                        schedule.append(f"{team_snapshot[home_team_id]['nickName']} vs. {team_snapshot[away_team_id]['nickName']}")
                else:
                    schedule.append(f"No user vs. user games were found for week {msg[func_index + 2]}")
                
                send_message('\n'.join(schedule))
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')

        else:
            send_message("Sorry, I couldn't find a team name associated with your request."
                        " Use '/help' to get a list of commands.")

    # Standings
    elif data['name'] != 'John Madden' and '/standings' in data['text'].lower():
        msg = data['text'].lower().split()
        func_index = msg.index('/standings')
        if(len(msg) > func_index + 1):
            try:
                conf_map_snapshot = cfm.child('conferenceMap').get()
                conf_id = conf_map_snapshot[msg[func_index + 1].lower()]
                standings_info_snapshot = cfm.child('standings').get()

                conf_teams = [ (team['seed'], team['teamName']) for team_id, team in standings_info_snapshot.items() if team['conferenceId'] == conf_id ]
                sorted_teams = sorted(conf_teams, key=lambda tup: tup[0])
                
                team_standings = [ f"{team[0]}. {team[1]}" for team in sorted_teams[0:9] ]

                send_message('\n'.join(team_standings))
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')

        else:
           send_message("Sorry, I couldn't find a conference associated with your request."
                        " Use '/help' to get a list of commands.")

    # Help prompt
    elif data['name'] != 'John Madden' and '/help' in data['text'].lower():
        help_prompt = get_help_prompt()
        send_message('\n'.join(help_prompt))

    # Rules prompt
    elif data['name'] != 'John Madden' and '/rules' in data['text'].lower():
        league_rules = get_league_rules()
        send_message('\n'.join(league_rules))

    # Team info
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

                team_info = [ f'{key}: {val}' for key, val in team_info_dict.items() ]
                send_message('\n'.join(team_info))
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')

        else:
            send_message("Sorry, I couldn't find a team name associated with your request."
                        " Use '/help' to get a list of commands.")

    # Team season stats
    elif data['name'] != 'John Madden' and '/stats' in data['text'].lower():
        msg = data['text'].lower().split()
        func_index = msg.index('/stats')
        if(len(msg) > func_index + 1):
            try:
                team_map_snapshot = cfm.child('teamMap').get()
                team_id = team_map_snapshot[msg[func_index + 1].lower()]
                team_info_snapshot = cfm.child('standings').child(team_id).get()

                team_stats_dict['Team'] = team_info_snapshot['teamName']
                team_stats_dict['Team Rank'] = team_info_snapshot['rank']
                team_stats_dict['Prev. Team Rank'] = team_info_snapshot['prevRank']
                team_stats_dict['Pts For Rank'] = team_info_snapshot['ptsForRank']
                team_stats_dict['Pts Against Rank'] = team_info_snapshot['ptsAgainstRank']
                team_stats_dict['Off Total Yds Rank'] = team_info_snapshot['offTotalYdsRank']
                team_stats_dict['Off Pass Yds Rank'] = team_info_snapshot['offPassYdsRank']
                team_stats_dict['Off Rush Yds Rank'] = team_info_snapshot['offRushYdsRank']
                team_stats_dict['Def Total Yds Rank'] = team_info_snapshot['defTotalYdsRank']
                team_stats_dict['Def Pass Yds Rank'] = team_info_snapshot['defPassYdsRank']
                team_stats_dict['Def Rush Yds Rank'] = team_info_snapshot['defRushYdsRank']
                team_stats_dict['TO Diff'] = team_info_snapshot['tODiff']

                team_stats = [ f'{key}: {val}' for key, val in team_stats_dict.items() ]
                send_message('\n'.join(team_stats))
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')

        else:
            send_message("Sorry, I couldn't find a team name associated with your request."
                        " Use '/help' to get a list of commands.")

    # Team record
    elif data['name'] != 'John Madden' and '/record' in data['text'].lower():
        msg = data['text'].lower().split()
        func_index = msg.index('/record')
        if(len(msg) > func_index + 1):
            try:
                team_map_snapshot = cfm.child('teamMap').get()
                team_id = team_map_snapshot[msg[func_index + 1].lower()]
                team_standings_snapshot = cfm.child('standings').child(team_id).get()

                team_record = f"{team_standings_snapshot['teamName']}: {team_standings_snapshot['totalWins']}-{team_standings_snapshot['totalLosses']}-{team_standings_snapshot['totalTies']} ({team_standings_snapshot['divWins']}-{team_standings_snapshot['divLosses']}-{team_standings_snapshot['divTies']})"
                send_message(team_record)
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')

        else:
            send_message("Sorry, I couldn't find a team name associated with your request."
                        " Use '/help' to get a list of commands.")

    # Team cap info
    elif data['name'] != 'John Madden' and '/cap' in data['text'].lower():
        msg = data['text'].lower().split()
        func_index = msg.index('/cap')
        if(len(msg) > func_index + 1):
            try:
                team_map_snapshot = cfm.child('teamMap').get()
                team_id = team_map_snapshot[msg[func_index + 1].lower()]
                team_standings_snapshot = cfm.child('standings').child(team_id).get()

                team_cap_dict['Team'] = team_standings_snapshot['teamName']
                team_cap_dict['Cap Room'] = '{:,}'.format(team_standings_snapshot['capRoom'])
                team_cap_dict['Cap Spent'] = '{:,}'.format(team_standings_snapshot['capSpent'])
                team_cap_dict['Cap Available'] = '{:,}'.format(team_standings_snapshot['capAvailable'])

                team_cap = [ f'{key}: {val}' for key, val in team_cap_dict.items() ]
                send_message('\n'.join(team_cap))
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')

        else:
            send_message("Sorry, I couldn't find a team name associated with your request."
                        " Use '/help' to get a list of commands.")
    
    # Number of injured players
    elif data['name'] != 'John Madden' and '/injuries' in data['text'].lower():
        msg = data['text'].lower().split()
        func_index = msg.index('/injuries')
        if(len(msg) > func_index + 1):
            try:
                team_map_snapshot = cfm.child('teamMap').get()
                team_id = team_map_snapshot[msg[func_index + 1].lower()]
                team_info_snapshot = cfm.child('teams').child(team_id).get()

                msg = f"{data['name']}, you sent '{data['text']}'"
                send_message(f"{team_info_snapshot['displayName']} have {team_info_snapshot['injuryCount']} players injured")
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')

        else:
            send_message("Sorry, I couldn't find a team name associated with your request."
                        " Use '/help' to get a list of commands.")



    return 'ok', 200

# Team info export endpoint
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

# Standings export endpoint
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

# Weekly info export endpoint
@app.route('/exports/<system>/<leagueId>/week/<weekType>/<weekNumber>/<dataType>', methods=['POST'])
def week_export(system, leagueId, weekType, weekNumber, dataType):
    print(request.is_json)
    print(request.mimetype)

    # Decompress gzip bytes stream
    buf = io.BytesIO(request.data)
    gzip_f = gzip.GzipFile(fileobj=buf)
    data = gzip_f.read()
    data = data.decode('utf-8')
    weeks = json.loads(data)
    del data

    weekly_ref = cfm.child(f'weeks/{weekType}/{weekNumber}/{dataType}')
    if dataType.lower() == 'schedules':
        schedules = weeks['gameScheduleInfoList']
        
        for i, game in enumerate(schedules):
            weekly_ref.update({i: game}) 

    elif dataType.lower() == 'teamstats':
        team_stats = weeks['teamStatInfoList']
        print(team_stats)

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