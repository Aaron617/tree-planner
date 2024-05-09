import sys
from .execution import ScriptExecutor
from typing import List
# from scripts import Script
from .utils import *


# keep graph unchanged
class CustomScriptExecutor(ScriptExecutor):
    def __init__(self, graph, name_equivalence):
        super(CustomScriptExecutor, self).__init__(graph, name_equivalence)

    def execute_one_step(self, script, state):
        prev_state = state
        #print("in execute_one_step, char_index = {}".format(self.char_index))
        state = next(self.call_action_method(script, state, self.info), None)
        if state is None:
            return False, prev_state
        return True, state

