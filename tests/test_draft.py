import filecmp
import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

from fantasy.draft.utils import log_transaction
from fantasy.draft.exceptions import InvalidTransactionException


def test_log_transaction(tmp_path):
    transaction_file_path = os.path.join(tmp_path, 'test_file1.json')
    player = 'LeBron James'
    team = 'Team 3'
    dollar_amount = 23

    log_transaction(transaction_file_path, player, team, dollar_amount)

    j = {"transactions": [{"player": "LeBron James","team": "Team 3","dollar_amount": 23}]}
    gold_file_path = os.path.join(tmp_path, 'test_file2.json')
    with open(gold_file_path, 'w') as transaction_file:
        transaction_file.write(json.dumps(j, indent=4))

    assert filecmp.cmp(transaction_file_path, gold_file_path)


@pytest.mark.parametrize("player,team,dollar_amount", [('', '', ''), (None, None, None)])
def test_log_invalid_transaction(tmp_path, player, team, dollar_amount):
    transaction_file_path = os.path.join(tmp_path, 'test_file1.json')

    with pytest.raises(InvalidTransactionException):
        assert log_transaction(transaction_file_path, player, team, dollar_amount)