import response_objects
import constants

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
            injuries = []
            team_map_snapshot = db_root.child('teamMap').get()
            team_id = team_map_snapshot[message[cmd_index + 1].lower()]
            team_info_snapshot = db_root.child('teams').child(team_id).get()
            roster_snapshot = db_root.child('rosters').child(team_id).get()

            injured_players = [ player for player in roster_snapshot if player['injuryLength'] != 0]
            print('INJURED PLAYERS =====> ')
            print(injured_players)
            for player in injured_players:
                response_objects.player_dict['First Name'] = player['firstName']
                response_objects.player_dict['Last Name'] = player['lastName']
                response_objects.player_dict['Position'] = player['position']
                response_objects.player_dict['Overall'] = player['playerBestOvr']
                response_objects.player_dict['Injury Length'] = player['injuryLength']
                injuries.append(response_objects.player_dict)

            print('\n'.join(injuries))
            return f"{team_info_snapshot['displayName']} have {team_info_snapshot['injuryCount']} players injured"
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

    else:
        return constants.MISSING_TEAM_NAME_ERR_MSG