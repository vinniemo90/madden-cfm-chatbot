import response_objects
import constants

def get_assigned_teams(db_root, message, cmd_index):
    assigned_teams = []
    groupme_users_snapshot = db_root.child('groupMeUsers').get()

    try:
        print('Retrieving groupme user info')
        users = [ {'nickname': user.get('nickname'), 'teamId': user.get('teamId')} for user in groupme_users_snapshot if user.get('gamertag') ]
        for user in users:
            print('find associated team')
            team_snapshot = db_root.child('teams').child(user['teamId']).get()
            print(f'Team Snapshot ===> {team_snapshot}')
            assigned_teams.append(f"{user['nickname']} => {team_snapshot['displayName']}")
        return '\n'.join(assigned_teams)

    except Exception as e:
        print(e)
        return constants.UNEXPECTED_ERR_MSG
    

def get_team_info(db_root, message, cmd_index):
    '''Get general team specific info
    
    Arguments:
        db_root {Object} -- Reference to root of Firebase database
        message {List} -- GroupMe message as list of strings
        cmd_index {Number} -- Index of slash command in message list
    '''

    if(len(message) > cmd_index + 1):
        try:
            print(f'Retrieving team info for {message[cmd_index + 1]}')
            team_map_snapshot = db_root.child('teamMap').get()
            team_id = team_map_snapshot[message[cmd_index + 1].lower()]
            team_info_snapshot = db_root.child('teams').child(team_id).get()

            response_objects.team_info_dict['City'] = team_info_snapshot['cityName']
            response_objects.team_info_dict['Mascot'] = team_info_snapshot['displayName']
            response_objects.team_info_dict['Division'] = team_info_snapshot['divName']
            response_objects.team_info_dict['Ovr Rating'] = team_info_snapshot['ovrRating']

            if team_info_snapshot['userName']:
                response_objects.team_info_dict['Owner'] = team_info_snapshot['userName']
            else:
                response_objects.team_info_dict['Owner'] = 'CPU'

            team_info = [ f'{key}: {val}' for key, val in response_objects.team_info_dict.items() ]
            return '\n'.join(team_info)
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

    else:
        return constants.MISSING_TEAM_NAME_ERR_MSG

def get_team_season_stats(db_root, message, cmd_index):
    if(len(message) > cmd_index + 1):
        try:
            print(f'Retrieving team season stats for {message[cmd_index + 1]}')
            team_map_snapshot = db_root.child('teamMap').get()
            team_id = team_map_snapshot[message[cmd_index + 1].lower()]
            team_info_snapshot = db_root.child('standings').child(team_id).get()

            response_objects.team_stats_dict['Team'] = team_info_snapshot['teamName']
            response_objects.team_stats_dict['Team Rank'] = team_info_snapshot['rank']
            response_objects.team_stats_dict['Prev. Team Rank'] = team_info_snapshot['prevRank']
            response_objects.team_stats_dict['Pts For Rank'] = team_info_snapshot['ptsForRank']
            response_objects.team_stats_dict['Pts Against Rank'] = team_info_snapshot['ptsAgainstRank']
            response_objects.team_stats_dict['Off Total Yds Rank'] = team_info_snapshot['offTotalYdsRank']
            response_objects.team_stats_dict['Off Pass Yds Rank'] = team_info_snapshot['offPassYdsRank']
            response_objects.team_stats_dict['Off Rush Yds Rank'] = team_info_snapshot['offRushYdsRank']
            response_objects.team_stats_dict['Def Total Yds Rank'] = team_info_snapshot['defTotalYdsRank']
            response_objects.team_stats_dict['Def Pass Yds Rank'] = team_info_snapshot['defPassYdsRank']
            response_objects.team_stats_dict['Def Rush Yds Rank'] = team_info_snapshot['defRushYdsRank']
            response_objects.team_stats_dict['TO Diff'] = team_info_snapshot['tODiff']

            team_stats = [ f'{key}: {val}' for key, val in response_objects.team_stats_dict.items() ]
            return '\n'.join(team_stats)
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

    else:
        return constants.MISSING_TEAM_NAME_ERR_MSG

def get_team_record(db_root, message, cmd_index):
    if(len(message) > cmd_index + 1):
        try:
            print(f'Retrieving season record for {message[cmd_index + 1]}')
            team_map_snapshot = db_root.child('teamMap').get()
            team_id = team_map_snapshot[message[cmd_index + 1].lower()]
            team_standings_snapshot = db_root.child('standings').child(team_id).get()

            team_record = f"{team_standings_snapshot['teamName']}: {team_standings_snapshot['totalWins']}-{team_standings_snapshot['totalLosses']}-{team_standings_snapshot['totalTies']} ({team_standings_snapshot['divWins']}-{team_standings_snapshot['divLosses']}-{team_standings_snapshot['divTies']})"
            return team_record
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

    else:
        return constants.MISSING_TEAM_NAME_ERR_MSG

def get_team_cap(db_root, message, cmd_index):
    if(len(message) > cmd_index + 1):
        try:
            print(f'Retrieving salary cap info for {message[cmd_index + 1]}')
            team_map_snapshot = db_root.child('teamMap').get()
            team_id = team_map_snapshot[message[cmd_index + 1].lower()]
            team_standings_snapshot = db_root.child('standings').child(team_id).get()

            response_objects.team_cap_dict['Team'] = team_standings_snapshot['teamName']
            response_objects.team_cap_dict['Cap Room'] = '{:,}'.format(team_standings_snapshot['capRoom'])
            response_objects.team_cap_dict['Cap Spent'] = '{:,}'.format(team_standings_snapshot['capSpent'])
            response_objects.team_cap_dict['Cap Available'] = '{:,}'.format(team_standings_snapshot['capAvailable'])

            team_cap = [ f'{key}: {val}' for key, val in response_objects.team_cap_dict.items() ]
            return '\n'.join(team_cap)
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

    else:
        return constants.MISSING_TEAM_NAME_ERR_MSG

def get_injured_players(db_root, message, cmd_index):
    if(len(message) > cmd_index + 1):
        try:
            print(f'Retrieving injuries info for {message[cmd_index + 1]}')
            team_map_snapshot = db_root.child('teamMap').get()
            team_id = team_map_snapshot[message[cmd_index + 1].lower()]
            team_info_snapshot = db_root.child('teams').child(team_id).get()
            roster_snapshot = db_root.child('rosters').child(team_id).get()

            injury_message = f"{team_info_snapshot['displayName']} have {team_info_snapshot['injuryCount']} players injured:"
            injured_players = [ f"{player['position']} {player['firstName']} {player['lastName']} ({player['playerBestOvr']} OVR) {player['injuryLength']} wks" 
            for player in roster_snapshot 
            if player['injuryLength'] != 0 and player['isActive'] == False]

            injured_players.insert(0, injury_message)
            return '\n'.join(injured_players)
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

    else:
        return constants.MISSING_TEAM_NAME_ERR_MSG

def get_expiring_contracts(db_root, message, cmd_index):
    if(len(message) > cmd_index + 1):
        try:
            print(f'Retrieving expiring contracts for {message[cmd_index + 1]}')
            team_map_snapshot = db_root.child('teamMap').get()
            team_id = team_map_snapshot[message[cmd_index + 1].lower()]
            roster_snapshot = db_root.child('rosters').child(team_id).get()

            contract_message = f"{message[cmd_index + 1]}' players with expiring contracts:"
            expiring_contracts = [ f"{player['position']} {player['firstName']} {player['lastName']} ({player['playerBestOvr']} OVR)" 
            for player in roster_snapshot 
            if player['contractYearsLeft'] == 1 ]

            expiring_contracts.insert(0, contract_message)
            return '\n'.join(expiring_contracts)
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

    else:
        return constants.MISSING_TEAM_NAME_ERR_MSG