import sys
sys.path.append('./')
import utils

def test_league_rules():
    league_rules = utils.get_league_rules()
    assert isinstance(league_rules, str)

def test_help_prompt():
    help_prompt = utils.get_help_prompt()
    assert isinstance(help_prompt, str)