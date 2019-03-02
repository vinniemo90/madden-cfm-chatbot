import os
import json
import firebase_admin
import io
import gzip
import requests

from firebase_admin import credentials
from firebase_admin import db

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, request

app = Flask(__name__)

# GroupMe info
groupme_token = os.getenv('GROUPME_TOKEN')
groupme_group_id = os.getenv('GROUPME_GROUP_ID')

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

# Preseason (4 weeks)
pre_dict = {'weekNumber': 1, 'weekType': 'pre'}

# Regular season (17 weeks)
reg_dict = {'weekNumber': 1, 'weekType': 'reg'}

# Playoffs (5 weeks including pro bowl)
playoffs_dict = {'weekNumber': 18, 'weekType': 'playoffs'}

# Offseason (7 weeks - Resign players, free agency (4 weeks), Draft, Offseason recap)
offseason_dict = {'weekNumber': 23, 'weekType': 'offseason'}
offseason_stages = ['Resign Players', 'Free Agency', 'Free Agency', 'Free Agency', 'Free Agency', 'Draft', 'Offseason Recap']

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

    # Update users on GroupMe name change
    if data['sender_id'].lower() == 'system' and ('changed name to' in data['text'].lower() or 'added' in data['text'].lower()):
        print('Groupme user changed name or new user added to group')
        request_params = {'token': groupme_token}
        group_members = requests.get(f'https://api.groupme.com/v3/groups/{groupme_group_id}', params = request_params).json()['response']['members']
        print('Updating groupme users info')
        cfm.update({'groupMeUsers': group_members})

    # Weekly Advance
    elif data['name'] != 'John Madden' and '/advance' in data['text'].lower():
        print('Advance keyword found')
        msg = data['text'].lower().split()
        func_index = msg.index('/advance')
        schedule = []
        if(len(msg) > func_index + 1) and (msg[func_index + 1].lower() == 'pre'):
            try:
                print('Advancing to the beginning of preseason')
                cfm.update({'league': pre_dict})
                schedule.append('Preseason Week 1 Schedule')
                schedule = schedule + get_user_games('pre', '1')
                send_message('\n'.join(schedule))
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')

        elif(len(msg) > func_index + 1) and (msg[func_index + 1].lower() == 'reg'):
            try:
                print('Advancing to the beginning of regular season')
                cfm.update({'league': reg_dict})
                schedule.append('Regular Season Week 1 Schedule')
                schedule = schedule + get_user_games('reg', '1')
                send_message('\n'.join(schedule))
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')

        elif(len(msg) > func_index + 1) and (msg[func_index + 1].lower() == 'playoffs'):
            try:
                print('Advancing to the beginning of playoffs')
                cfm.update({'league': playoffs_dict})
                schedule.append('Wildcard Schedule')
                schedule = schedule + get_user_games('reg', '18')
                send_message('\n'.join(schedule))
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')

        elif(len(msg) > func_index + 1) and (msg[func_index + 1].lower() == 'offseason'):
            try:
                print('Advancing to the beginning of offseason')
                cfm.update({'league': offseason_dict})
                send_message('Offseason Stage 1: Resign Players')
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')

        else:
            try:
                league_snapshot = cfm.child('league').get()
                week_type = league_snapshot['weekType']
                week_number = league_snapshot['weekNumber']

                if week_type == 'pre':
                    week_number += 1
                    if week_number < 5:
                        week_dict = {'weekNumber': week_number, 'weekType': 'pre'}
                        cfm.update({'league': week_dict})
                        schedule.append(f'Preason Week {week_number} Schedule')
                        schedule = schedule + get_user_games('pre', str(week_number))
                        send_message('\n'.join(schedule))
                    else:
                        cfm.update({'league': reg_dict})
                        schedule.append(f'Regular Season Week 1 Schedule')
                        schedule = schedule + get_user_games('reg', '1')
                        send_message('\n'.join(schedule))

                elif week_type == 'reg':
                    week_number += 1
                    if week_number < 18:
                        week_dict = {'weekNumber': week_number, 'weekType': 'reg'}
                        cfm.update({'league': week_dict})
                        schedule.append(f'Regular Season Week {week_number} Schedule')
                        schedule = schedule + get_user_games('reg', str(week_number))
                        send_message('\n'.join(schedule))
                    else:
                        cfm.update({'league': playoffs_dict})
                        schedule.append('Wildcard Schedule')
                        schedule = schedule + get_user_games('reg', '18')
                        send_message('\n'.join(schedule))

                elif week_type == 'playoffs':
                    week_number += 1
                    if week_number == 21:
                        send_message('Pro Bowl Week')
                    elif week_number == 18:
                        week_dict = {'weekNumber': week_number, 'weekType': 'playoffs'}
                        cfm.update({'league': week_dict})
                        schedule.append('Wildcard Schedule')
                        schedule = schedule + get_user_games('reg', str(week_number))
                        send_message('\n'.join(schedule))
                    elif week_number == 19:
                        week_dict = {'weekNumber': week_number, 'weekType': 'playoffs'}
                        cfm.update({'league': week_dict})
                        schedule.append('Divisional Schedule')
                        schedule = schedule + get_user_games('reg', str(week_number))
                        send_message('\n'.join(schedule))
                    elif week_number == 20:
                        week_dict = {'weekNumber': week_number, 'weekType': 'playoffs'}
                        cfm.update({'league': week_dict})
                        schedule.append('Conference Championship Schedule')
                        schedule = schedule + get_user_games('reg', str(week_number))
                        send_message('\n'.join(schedule))
                    elif week_number == 22:
                        week_dict = {'weekNumber': week_number, 'weekType': 'playoffs'}
                        cfm.update({'league': week_dict})
                        schedule.append('Super Bowl Schedule')
                        schedule = schedule + get_user_games('reg', str(week_number))
                        send_message('\n'.join(schedule))
                    else:
                        cfm.update({'league': offseason_dict})
                        send_message('Offseason Stage 1: Resign Players')

                else:
                    week_number += 1
                    if week_number < 30:
                        week_dict = {'weekNumber': week_number, 'weekType': 'offseason'}
                        cfm.update({'league': week_dict})
                        offseason_stage = week_number - 22
                        send_message(f'Offseason Stage {offseason_stage}: {offseason_stages[week_number-23]}')
                    else:
                        cfm.update({'league': pre_dict})
                        schedule.append('Preseason Week 1 Schedule')
                        schedule = schedule + get_user_games('pre', '1')
                        send_message('\n'.join(schedule))
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')
    # Schedule
    elif data['name'] != 'John Madden' and '/schedule' in data['text'].lower():
        if '/schedule week' in data['text'].lower() or '/schedule wk' in data['text'].lower():
            print('Schedule week keyword found')
            msg = data['text'].lower().split()
            func_index = msg.index('/schedule')
            if(len(msg) > func_index + 2):
                try:
                    print(f'Retrieving user game schedule for wk {msg[func_index + 2]}')
                    schedule = get_user_games('reg', msg[func_index + 2])
                    send_message('\n'.join(schedule))
                
                except Exception as e:
                    print(e)
                    send_message('Sorry, an error occurred processing your request.')

            else:
                send_message("Sorry, I couldn't find a week associated with your request."
                            " Use '/help' to get a list of commands.")
        else:
            print('Schedule keyword found')
            msg = data['text'].lower().split()
            func_index = msg.index('/schedule')
            if(len(msg) > func_index + 1):
                try:
                    print(f'Retrieving season schedule for {msg[func_index + 1]}')
                    team_map_snapshot = cfm.child('teamMap').get()
                    team_id = team_map_snapshot[msg[func_index + 1].lower()]
                    schedule = get_team_schedule(team_id)
                    send_message('\n'.join(schedule))
                
                except Exception as e:
                    print(e)
                    send_message('Sorry, an error occurred processing your request.')

            else:
                send_message("Sorry, I couldn't find a team associated with your request."
                            " Use '/help' to get a list of commands.")
    # User game scores for the week
    elif data['name'] != 'John Madden' and ('/scores week' in data['text'].lower() or '/scores wk' in data['text'].lower()):
        print('Scores keyword found')
        msg = data['text'].lower().split()
        func_index = msg.index('/scores')
        if(len(msg) > func_index + 2):
            try:
                print(f'Retrieving user game scores for wk {msg[func_index + 2]}')
                schedule = get_user_scores('reg', msg[func_index + 2])
                send_message('\n'.join(schedule))
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')

        else:
            send_message("Sorry, I couldn't find a week associated with your request."
                        " Use '/help' to get a list of commands.")

    # Standings
    elif data['name'] != 'John Madden' and '/standings' in data['text'].lower():
        print('Standings keyword found')
        msg = data['text'].lower().split()
        func_index = msg.index('/standings')
        if(len(msg) > func_index + 1) and (msg[func_index + 1].lower() != 'nfl'):
            try:
                print(f'Retrieving standings info for {msg[func_index + 1]} conf')
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
            try:
                print('Retrieving standings info for entire nfl')
                standings_info_snapshot = cfm.child('standings').get()

                nfl_teams = [ (team['rank'], team['teamName']) for team_id, team in standings_info_snapshot.items() if int(team['rank']) < 19 ]
                sorted_teams = sorted(nfl_teams, key=lambda tup: tup[0])
                
                team_standings = [ f"{team[0]}. {team[1]}" for team in sorted_teams ]

                send_message('\n'.join(team_standings))
            
            except Exception as e:
                print(e)
                send_message('Sorry, an error occurred processing your request.')

    # Help prompt
    elif data['name'] != 'John Madden' and '/help' in data['text'].lower():
        print('Help keyword found')
        help_prompt = get_help_prompt()
        send_message('\n'.join(help_prompt))

    # Rules prompt
    elif data['name'] != 'John Madden' and '/rules' in data['text'].lower():
        print('Rules keyword found')
        league_rules = get_league_rules()
        send_message('\n'.join(league_rules))

    # Team info
    elif data['name'] != 'John Madden' and '/teams' in data['text'].lower():
        print('Teams keyword found')
        msg = data['text'].lower().split()
        func_index = msg.index('/teams')
        if(len(msg) > func_index + 1):
            try:
                print(f'Retrieving team info for {msg[func_index + 1]}')
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
        print('Stats keyword found')
        msg = data['text'].lower().split()
        func_index = msg.index('/stats')
        if(len(msg) > func_index + 1):
            try:
                print(f'Retrieving team season stats for {msg[func_index + 1]}')
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
        print('Record keyword found')
        msg = data['text'].lower().split()
        func_index = msg.index('/record')
        if(len(msg) > func_index + 1):
            try:
                print(f'Retrieving season record for {msg[func_index + 1]}')
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
        print('Cap keyword found')
        msg = data['text'].lower().split()
        func_index = msg.index('/cap')
        if(len(msg) > func_index + 1):
            try:
                print(f'Retrieving salary cap info for {msg[func_index + 1]}')
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
        print('Injuries keyword found')
        msg = data['text'].lower().split()
        func_index = msg.index('/injuries')
        if(len(msg) > func_index + 1):
            try:
                print(f'Retrieving injuries info for {msg[func_index + 1]}')
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
    print(dataType)

    # Decompress gzip bytes stream
    buf = io.BytesIO(request.data)
    gzip_f = gzip.GzipFile(fileobj=buf)
    data = gzip_f.read()
    data = data.decode('utf-8')
    weeks = json.loads(data)
    print(weeks)
    del data

    weekly_ref = cfm.child(f'weeks/{weekType}/{weekNumber}/{dataType}')
    if dataType.lower() == 'schedules':
        schedules = weeks['gameScheduleInfoList']
        
        for i, game in enumerate(schedules):
            weekly_ref.update({i: game}) 

    # elif dataType.lower() == 'teamstats':
    #     team_stats = weeks['teamStatInfoList']
    #     print(f'---TEAM STATS--- {team_stats}')

    # elif dataType.lower() == 'defense':
    #     print(f"---DEFENCSE--- {weeks['playerDefensiveStatInfoList']}")

    return 'ok', 200

# app.post('/:username/:platform/:leagueId/freeagents/roster', (req, res)
# app.post('/:username/:platform/:leagueId/team/:teamId/roster', (req, res)
# Weekly info export endpoint
@app.route('/exports/<system>/<leagueId>/team/<teamId>/roster', methods=['POST'])
def roster_export(system, leagueId, teamId):
    # Decompress gzip bytes stream
    buf = io.BytesIO(request.data)
    gzip_f = gzip.GzipFile(fileobj=buf)
    data = gzip_f.read()
    data = data.decode('utf-8')
    roster = json.loads(data)
    del data

    rosters_ref = cfm.child('rosters')
    rosters_ref.update({teamId: roster['rosterInfoList']})

    #cfm.update({'roster': roster['rosterInfoList']})
    # weekly_ref = cfm.child(f'weeks/{weekType}/{weekNumber}/{dataType}')
    # if dataType.lower() == 'schedules':
    #     schedules = weeks['gameScheduleInfoList']
        
    #     for i, game in enumerate(schedules):
    #         weekly_ref.update({i: game}) 

    # elif dataType.lower() == 'teamstats':
    #     team_stats = weeks['teamStatInfoList']
    #     print(f'---TEAM STATS--- {team_stats}')

    # elif dataType.lower() == 'defense':
    #     print(f"---DEFENCSE--- {weeks['playerDefensiveStatInfoList']}")

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

def get_user_scores(week_type, week_number):
    ''' Get user vs. user game scores and return as list '''
    try:
        team_snapshot = cfm.child('teams').get()
        user_team_ids = [ team['teamId'] for team_id, team in team_snapshot.items() if team['userName'] ]
        schedule_snapshot = cfm.child(f'weeks/{week_type}/{week_number}/schedules').get()
        
        user_games = []
        schedule = []
        for game_info in schedule_snapshot:
            if game_info['awayTeamId'] in user_team_ids and game_info['homeTeamId'] in user_team_ids:
                user_games.append((game_info['homeTeamId'], game_info['homeScore'], game_info['awayTeamId'], game_info['awayScore']))

        if user_games:
            for home_team_id, home_score, away_team_id, away_score in user_games:
                schedule.append(f"{team_snapshot[str(home_team_id)]['nickName']} {home_score} vs. {team_snapshot[str(away_team_id)]['nickName']} {away_score}")

        else:
            schedule.append(f"No user vs. user games were found for {week_type} week {week_number}")

    except Exception as e:
        print(e)
        schedule.clear()
        schedule.append('Sorry, an error occurred retrieving user games.')

    finally:
        return schedule

def get_user_games(week_type, week_number):
    ''' Get user vs. user game schedule and return as list '''
    try:
        team_snapshot = cfm.child('teams').get()
        user_team_ids = [ team['teamId'] for team_id, team in team_snapshot.items() if team['userName'] ]
        schedule_snapshot = cfm.child(f'weeks/{week_type}/{week_number}/schedules').get()
        
        user_games = []
        schedule = []
        for game_info in schedule_snapshot:
            if game_info['awayTeamId'] in user_team_ids and game_info['homeTeamId'] in user_team_ids:
                user_games.append((game_info['homeTeamId'], game_info['awayTeamId']))

        if user_games:
            for home_team_id, away_team_id in user_games:
                schedule.append(f"{team_snapshot[str(home_team_id)]['nickName']} vs. {team_snapshot[str(away_team_id)]['nickName']}")

        else:
            schedule.append(f"No user vs. user games were found for {week_type} week {week_number}")

    except Exception as e:
        print(e)
        schedule.clear()
        schedule.append('Sorry, an error occurred retrieving user games.')

    finally:
        return schedule

def get_team_schedule(team_id):
    ''' Get team schedule and return as list '''
    try:
        print('Get team schedule as team ids')
        season_schedule_team_ids = []
        schedule_snapshot = cfm.child('weeks/reg').get()
        weekly_schedule = [ week['schedules'] for week in schedule_snapshot[1:18] if week != None]
        for week in weekly_schedule:
            # print(schedule_snapshot)
            for i, game in enumerate(week):
                if game['homeTeamId'] == int(team_id):
                    season_schedule_team_ids.append((game['weekIndex'], game['awayTeamId']))
                    break
                elif game['awayTeamId'] == int(team_id):
                    season_schedule_team_ids.append((game['weekIndex'], game['homeTeamId']))
                    break
                elif i == (len(week) - 1):
                    season_schedule_team_ids.append((game['weekIndex'], 'Bye'))

        print('Get opponent team names')
        season_schedule_team_names = []
        teams_snapshot = cfm.child('teams').get()
        for wk_num, opp_team_id in season_schedule_team_ids:
            if(opp_team_id == 'Bye'):
                season_schedule_team_names.append(f'wk {wk_num + 1}: {opp_team_id}')
            else:
                season_schedule_team_names.append(f"wk {wk_num + 1}: {teams_snapshot[str(opp_team_id)]['displayName']}")

    except Exception as e:
        print(e)
        season_schedule_team_names.clear()
        season_schedule_team_names.append('Sorry, an error occurred retrieving user games.')

    finally:
        return season_schedule_team_names