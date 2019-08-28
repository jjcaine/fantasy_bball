import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

from fantasy.draft.utils import log_transaction


def test_log_transaction():
