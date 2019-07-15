import response_objects
import constants

def get_user_scores(db_root, week_type, week_number):
    '''Get user vs. user game scores and return as list
    
    Arguments:
        db_root {Object} -- Root of Firebase database
        week_type {String} -- Preseason or Regular season
        week_number {String} -- Week number
    
    Returns:
        List -- User vs. user game scores for the week
    '''

    try:
        team_snapshot = db_root.child('teams').get()
        user_team_ids = [ team['teamId'] for team_id, team in team_snapshot.items() if team['userName'] ]
        schedule_snapshot = db_root.child(f'weeks/{week_type}/{week_number}/schedules').get()
        
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

def get_user_games(db_root, week_type, week_number):
    '''Get user vs. user game schedule and return as list
    
    Arguments:
        db_root {Object} -- Root of Firebase database
        week_type {String} -- Preseason or Regular season
        week_number {String} -- Week number
    
    Returns:
        List -- User vs. user games for the week
    '''

    try:
        team_snapshot = db_root.child('teams').get()
        user_team_ids = [ team['teamId'] for team_id, team in team_snapshot.items() if team['userName'] ]
        schedule_snapshot = db_root.child(f'weeks/{week_type}/{week_number}/schedules').get()
        
        user_games = []
        schedule = []
        for game_info in schedule_snapshot:
            if game_info['awayTeamId'] in user_team_ids and game_info['homeTeamId'] in user_team_ids:
                user_games.append((game_info['homeTeamId'], game_info['awayTeamId']))

        if user_games:
            user_teams = {}
            groupme_users_snapshot = db_root.child('groupMeUsers').get()
            print('Creating dictionary of gamertags')
            for user in groupme_users_snapshot:
                if user.get('teamId'):
                    user_teams[user['teamId']] = user['nickname']

            for home_team_id, away_team_id in user_games:
                if user_teams.get(str(home_team_id)) and user_teams.get(str(away_team_id)):
                    print('Both gamertags found')
                    schedule.append(f"{team_snapshot[str(home_team_id)]['displayName']} (@{user_teams[str(home_team_id)]}) vs. {team_snapshot[str(away_team_id)]['displayName']} (@{user_teams[str(away_team_id)]})")
                
                elif user_teams.get(str(home_team_id)):
                    print('Home team gamertag found')
                    schedule.append(f"{team_snapshot[str(home_team_id)]['displayName']} (@{user_teams[str(home_team_id)]}) vs. {team_snapshot[str(away_team_id)]['displayName']}")
                
                elif user_teams.get(str(away_team_id)):
                    print('Away team gamertag found')
                    schedule.append(f"{team_snapshot[str(home_team_id)]['displayName']} vs. {team_snapshot[str(away_team_id)]['displayName']} (@{user_teams[str(away_team_id)]})")
                
                else:
                    print('No gamertag found')
                    schedule.append(f"{team_snapshot[str(home_team_id)]['displayName']} vs. {team_snapshot[str(away_team_id)]['displayName']}")

        else:
            schedule.append(f"No user vs. user games were found for {week_type} week {week_number}")

    except Exception as e:
        print(e)
        schedule.clear()
        schedule.append(constants.USER_GAME_ERROR)

    finally:
        return schedule

def get_team_schedule(db_root, team_id):
    '''Get team schedule
    
    Arguments:
        db_root {Object} -- Root of Firebase database
        team_id {String} -- ID of team
    
    Returns:
        List -- team schedule
    '''
    
    try:
        print('Get team schedule as team ids')
        season_schedule_team_ids = []
        season_schedule_team_names = []
        schedule_snapshot = db_root.child('weeks/reg').get()
        print('getting weekly schedule')
        weekly_schedule = [ week['schedules'] for week in schedule_snapshot[1:18] if week != None]
        for week in weekly_schedule:
            print('Iterating through games for the week')
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
        teams_snapshot = db_root.child('teams').get()
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

def get_weekly_schedule(db_root, msg, func_index):
    '''Get user vs. user games for the specified week
    
    Arguments:
        db_root {Object} -- Root of Firebase database
        msg {List} -- GroupMe message as list
        func_index {Number} -- Index of slash command in GroupMe message
    '''

    print('Schedule week keyword found')
    if(len(msg) > func_index + 2):
        try:
            print(f'Retrieving user game schedule for wk {msg[func_index + 2]}')
            schedule = get_user_games(db_root, 'reg', msg[func_index + 2])
            return '\n'.join(schedule)
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

    else:
        return constants.MISSING_WK_NUM_ERR_MSG

def get_season_schedule(db_root, msg, func_index):
    '''Get season schedule for specific team
    
    Arguments:
        db_root {Object} -- Root of Firebase database
        msg {List} -- GroupMe message as list
        func_index {Number} -- Index of slash command in GroupMe message
    '''

    print('Schedule keyword found')
    if(len(msg) > func_index + 1):
        try:
            print(f'Retrieving season schedule for {msg[func_index + 1]}')
            team_map_snapshot = db_root.child('teamMap').get()
            team_id = team_map_snapshot[msg[func_index + 1].lower()]
            schedule = get_team_schedule(db_root, team_id)
            return '\n'.join(schedule)
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

    else:
        return constants.MISSING_TEAM_NAME_ERR_MSG

def get_user_weekly_scores(db_root, msg, func_index):
    '''Get scores for user vs. user games for the specified week
    
    Arguments:
        db_root {Object} -- Root of Firebase database
        msg {List} -- GroupMe message as list
        func_index {Number} -- Index of slash command in GroupMe message
    '''

    print('Scores keyword found')
    if(len(msg) > func_index + 2):
        try:
            print(f'Retrieving user game scores for wk {msg[func_index + 2]}')
            schedule = get_user_scores(db_root, 'reg', msg[func_index + 2])
            return '\n'.join(schedule)
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

    else:
        return constants.MISSING_WK_NUM_ERR_MSG