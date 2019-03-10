import cfm_advance
import cfm_schedule
import cfm_team
import cfm_standings
import utils

UNEXPECTED_ERR_MSG = 'Sorry, an error occurred processing your request.'
MISSING_TEAM_NAME_ERR_MSG = ("Sorry, I couldn't find a team name associated with your request."
                                " Use '/help' to get a list of commands.")
MISSING_WK_NUM_ERR_MSG = ("Sorry, I couldn't find a week associated with your request."
                            " Use '/help' to get a list of commands.")

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
    '/rules': utils.get_league_rules
}