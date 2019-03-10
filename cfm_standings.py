import groupme
import constants

def get_conf_standings(db_root, msg, func_index):
    '''Get conference standings
    
    Arguments:
        db_root {Object} -- Root of Firebase database
        msg {List} -- GroupMe message as list
        func_index {Number} -- Index of slash command in GroupMe message
    '''

    print('Standings keyword found')
    if(len(msg) > func_index + 1) and (msg[func_index + 1].lower() != 'nfl'):
        try:
            print(f'Retrieving standings info for {msg[func_index + 1]} conf')
            conf_map_snapshot = db_root.child('conferenceMap').get()
            conf_id = conf_map_snapshot[msg[func_index + 1].lower()]
            standings_info_snapshot = db_root.child('standings').get()

            conf_teams = [ (team['seed'], team['teamName']) for team_id, team in standings_info_snapshot.items() if team['conferenceId'] == conf_id ]
            sorted_teams = sorted(conf_teams, key=lambda tup: tup[0])
            
            team_standings = [ f"{team[0]}. {team[1]}" for team in sorted_teams[0:9] ]

            return '\n'.join(team_standings)
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

def get_nfl_standings(db_root, msg, func_index):
    '''Get NFL standings
    
    Arguments:
        db_root {Object} -- Root of Firebase database
        msg {List} -- GroupMe message as list
        func_index {Number} -- Index of slash command in GroupMe message
    '''

    try:
        print('Retrieving standings info for entire nfl')
        standings_info_snapshot = db_root.child('standings').get()

        nfl_teams = [ (team['rank'], team['teamName']) for team_id, team in standings_info_snapshot.items() if int(team['rank']) < 19 ]
        sorted_teams = sorted(nfl_teams, key=lambda tup: tup[0])
        
        team_standings = [ f"{team[0]}. {team[1]}" for team in sorted_teams ]

        return '\n'.join(team_standings)
    
    except Exception as e:
        print(e)
        return constants.UNEXPECTED_ERR_MSG