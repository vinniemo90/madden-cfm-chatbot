import json

def get_league_rules():
    '''Get league rules
    
    Returns:
        List -- CFM league rules
    '''

    with open('cfm-rules.json') as rules:
        cfm_rules = json.load(rules)
        return '\n'.join(cfm_rules['league rules'])

def get_help_prompt():
    '''Get info regarding Madden GroupMe bot
    
    Returns:
        List -- Help prompt
    '''

    with open('cfm-rules.json') as rules:
        cfm_rules = json.load(rules)
        return '\n'.join(cfm_rules['help prompt'])

def get_team_nicknames(teamAbbreviation):
    '''Get nicknames associated with NFL team
    
    Returns:
        List -- Nicknames associated with team
    '''

    with open('teamNicknames.json') as teamNicknames:
        nicknames = json.load(teamNicknames)
        return nicknames[teamAbbreviation]