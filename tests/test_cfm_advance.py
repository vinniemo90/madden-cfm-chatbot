from unittest.mock import patch
import sys
sys.path.append('./')
import cfm_advance
import cfm_schedule
import constants
from firebase_admin import db

@patch('firebase_admin.db')
def test_advance_to_preseason(mock_db):
    db_root = mock_db.reference()
    schedule = cfm_advance.advance_to_preseason(db_root)
    assert isinstance(schedule, list)
    assert schedule[0] == 'Preseason Week 1 Schedule'

@patch('cfm_schedule.get_user_games')
@patch('firebase_admin.db')
def test_advance_to_preseason_error(mock_db, mock_get_user_games):
    db_root = mock_db.reference()
    mock_get_user_games.return_value = [constants.USER_GAME_ERROR]
    schedule = cfm_advance.advance_to_preseason(db_root)
    assert isinstance(schedule, list)
    assert schedule[0] == constants.USER_GAME_ERROR

@patch('firebase_admin.db')
def test_advance_to_reg(mock_db):
    db_root = mock_db.reference()
    schedule = cfm_advance.advance_to_reg(db_root)
    assert isinstance(schedule, list)
    assert schedule[0] == 'Regular Season Week 1 Schedule'

@patch('cfm_schedule.get_user_games')
@patch('firebase_admin.db')
def test_advance_to_reg_error(mock_db, mock_get_user_games):
    db_root = mock_db.reference()
    mock_get_user_games.return_value = [constants.USER_GAME_ERROR]
    schedule = cfm_advance.advance_to_reg(db_root)
    assert isinstance(schedule, list)
    assert schedule[0] == constants.USER_GAME_ERROR

@patch('firebase_admin.db')
def test_advance_to_playoffs(mock_db):
    db_root = mock_db.reference()
    schedule = cfm_advance.advance_to_playoffs(db_root)
    assert isinstance(schedule, list)
    assert schedule[0] == 'Wildcard Schedule'

@patch('cfm_schedule.get_user_games')
@patch('firebase_admin.db')
def test_advance_to_playoffs_error(mock_db, mock_get_user_games):
    db_root = mock_db.reference()
    mock_get_user_games.return_value = [constants.USER_GAME_ERROR]
    schedule = cfm_advance.advance_to_playoffs(db_root)
    assert isinstance(schedule, list)
    assert schedule[0] == constants.USER_GAME_ERROR

@patch('cfm_advance.advance_to_preseason')
@patch('firebase_admin.db')
def test_advance_pre(mock_db, mock_advance_to_preseason):
    db_root = mock_db.reference()
    mock_advance_to_preseason.return_value = ['abc']
    schedule = cfm_advance.advance(db_root, ['/advance', 'pre'], 0)
    assert schedule == 'abc'

@patch('cfm_advance.advance_to_preseason')
@patch('firebase_admin.db')
def test_advance_pre_error(mock_db, mock_adv_to_preseason):
    db_root = mock_db
    mock_adv_to_preseason.side_effect = Exception
    schedule = cfm_advance.advance(db_root, ['/advance', 'pre'], 0)
    assert schedule == constants.UNEXPECTED_ERR_MSG

@patch('cfm_advance.advance_to_reg')
@patch('firebase_admin.db')
def test_advance_reg(mock_db, mock_adv_reg):
    db_root = mock_db.reference()
    mock_adv_reg.return_value = ['foo']
    schedule = cfm_advance.advance(db_root, ['/advance', 'reg'], 0)
    assert schedule == 'foo'

@patch('cfm_advance.advance_to_reg')
@patch('firebase_admin.db')
def test_advance_reg_error(mock_db, mock_adv_reg):
    db_root = mock_db
    mock_adv_reg.side_effect = Exception
    schedule = cfm_advance.advance(db_root, ['/advance', 'reg'], 0)
    assert schedule == constants.UNEXPECTED_ERR_MSG

@patch('cfm_advance.advance_to_playoffs')
@patch('firebase_admin.db')
def test_advance_playoffs(mock_db, mock_adv_to_playoffs):
    db_root = mock_db.reference()
    mock_adv_to_playoffs.return_value = ['bar']
    schedule = cfm_advance.advance(db_root, ['/advance', 'playoffs'], 0)
    assert schedule == 'bar'

@patch('cfm_advance.advance_to_playoffs')
@patch('firebase_admin.db')
def test_advance_playoffs_error(mock_db, mock_adv_to_playoffs):
    db_root = mock_db
    mock_adv_to_playoffs.side_effect = Exception
    schedule = cfm_advance.advance(db_root, ['/advance', 'playoffs'], 0)
    assert schedule == constants.UNEXPECTED_ERR_MSG

@patch('firebase_admin.db')
def test_advance_offseason(mock_db):
    db_root = mock_db.reference()
    schedule = cfm_advance.advance(db_root, ['/advance', 'offseason'], 0)
    assert schedule == 'Offseason Stage 1: Resign Players'

@patch('firebase_admin.db')
def test_advance_offseason_error(mock_db):
    db_root = mock_db
    mock_db.update.side_effect = Exception
    schedule = cfm_advance.advance(db_root, ['/advance', 'offseason'], 0)
    assert schedule == constants.UNEXPECTED_ERR_MSG