import cfm_schedule
import response_objects
import constants

def advance_to_preseason(db_root):
    '''Set internal league counter to week 1 of preseason

    Arguments:
        db_root {Object} -- Reference to root of Firebase database
    
    Returns:
        List -- User vs. User games for week 1 of preseason
    '''

    schedule = []
    db_root.update({'league': response_objects.pre_dict})
    schedule.append('Preseason Week 1 Schedule')
    return schedule + cfm_schedule.get_user_games(db_root, 'pre', '1')

def advance_to_reg(db_root):
    '''Set internal league counter to week 1 of the regular season

    Arguments:
        db_root {Object} -- Reference to root of Firebase database
    
    Returns:
        List -- User vs. User games for week 1 of the regular season
    '''

    schedule = []
    db_root.update({'league': response_objects.reg_dict})
    schedule.append('Regular Season Week 1 Schedule')
    return schedule + cfm_schedule.get_user_games(db_root, 'reg', '1')

def advance_to_playoffs(db_root):
    '''Set internal league counter to wildcard week of the playoffs

    Arguments:
        db_root {Object} -- Reference to root of Firebase database
    
    Returns:
        List -- User vs. User games for wildcard week
    '''

    schedule = []
    db_root.update({'league': response_objects.playoffs_dict})
    schedule.append('Wildcard Schedule')
    return schedule + cfm_schedule.get_user_games(db_root, 'reg', '18')
    
def advance(db_root, msg, func_index):
    schedule = []
    if(len(msg) > func_index + 1) and (msg[func_index + 1].lower() == 'pre'):
        try:
            print('Advancing to the beginning of preseason')
            schedule = advance_to_preseason(db_root)
            return '\n'.join(schedule)
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

    elif(len(msg) > func_index + 1) and (msg[func_index + 1].lower() == 'reg'):
        try:
            print('Advancing to the beginning of regular season')
            schedule = advance_to_reg(db_root)
            return '\n'.join(schedule)
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

    elif(len(msg) > func_index + 1) and (msg[func_index + 1].lower() == 'playoffs'):
        try:
            print('Advancing to the beginning of playoffs')
            schedule = advance_to_playoffs(db_root)
            return '\n'.join(schedule)
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

    elif(len(msg) > func_index + 1) and (msg[func_index + 1].lower() == 'offseason'):
        try:
            print('Advancing to the beginning of offseason')
            db_root.update({'league': response_objects.offseason_dict})
            return 'Offseason Stage 1: Resign Players'
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG

    else:
        try:
            league_snapshot = db_root.child('league').get()
            week_type = league_snapshot['weekType']
            week_number = league_snapshot['weekNumber']

            if week_type == 'pre':
                week_number += 1
                if week_number < 5:
                    week_dict = {'weekNumber': week_number, 'weekType': 'pre'}
                    db_root.update({'league': week_dict})
                    schedule.append(f'Preason Week {week_number} Schedule')
                    schedule = schedule + cfm_schedule.get_user_games(db_root, 'pre', str(week_number))
                    return '\n'.join(schedule)
                else:
                    db_root.update({'league': response_objects.reg_dict})
                    schedule.append(f'Regular Season Week 1 Schedule')
                    schedule = schedule + cfm_schedule.get_user_games(db_root, 'reg', '1')
                    return '\n'.join(schedule)

            elif week_type == 'reg':
                week_number += 1
                if week_number < 18:
                    week_dict = {'weekNumber': week_number, 'weekType': 'reg'}
                    db_root.update({'league': week_dict})
                    schedule.append(f'Regular Season Week {week_number} Schedule')
                    schedule = schedule + cfm_schedule.get_user_games(db_root, 'reg', str(week_number))
                    return '\n'.join(schedule)
                else:
                    db_root.update({'league': response_objects.playoffs_dict})
                    schedule.append('Wildcard Schedule')
                    schedule = schedule + cfm_schedule.get_user_games(db_root, 'reg', '18')
                    return '\n'.join(schedule)

            elif week_type == 'playoffs':
                week_number += 1
                if week_number == 21:
                    return 'Pro Bowl Week'
                elif week_number == 18:
                    week_dict = {'weekNumber': week_number, 'weekType': 'playoffs'}
                    db_root.update({'league': week_dict})
                    schedule.append('Wildcard Schedule')
                    schedule = schedule + cfm_schedule.get_user_games(db_root, 'reg', str(week_number))
                    return '\n'.join(schedule)
                elif week_number == 19:
                    week_dict = {'weekNumber': week_number, 'weekType': 'playoffs'}
                    db_root.update({'league': week_dict})
                    schedule.append('Divisional Schedule')
                    schedule = schedule + cfm_schedule.get_user_games(db_root, 'reg', str(week_number))
                    return '\n'.join(schedule)
                elif week_number == 20:
                    week_dict = {'weekNumber': week_number, 'weekType': 'playoffs'}
                    db_root.update({'league': week_dict})
                    schedule.append('Conference Championship Schedule')
                    schedule = schedule + cfm_schedule.get_user_games(db_root, 'reg', str(week_number))
                    return '\n'.join(schedule)
                elif week_number == 22:
                    week_dict = {'weekNumber': week_number, 'weekType': 'playoffs'}
                    db_root.update({'league': week_dict})
                    schedule.append('Super Bowl Schedule')
                    schedule = schedule + cfm_schedule.get_user_games(db_root, 'reg', str(week_number))
                    return '\n'.join(schedule)
                else:
                    db_root.update({'league': response_objects.offseason_dict})
                    return 'Offseason Stage 1: Resign Players'

            else:
                week_number += 1
                if week_number < 30:
                    week_dict = {'weekNumber': week_number, 'weekType': 'offseason'}
                    db_root.update({'league': week_dict})
                    offseason_stage = week_number - 22
                    return f'Offseason Stage {offseason_stage}: {response_objects.offseason_stages[week_number-23]}'
                else:
                    db_root.update({'league': response_objects.pre_dict})
                    schedule.append('Preseason Week 1 Schedule')
                    schedule = schedule + cfm_schedule.get_user_games(db_root, 'pre', '1')
                    return '\n'.join(schedule)
        
        except Exception as e:
            print(e)
            return constants.UNEXPECTED_ERR_MSG
