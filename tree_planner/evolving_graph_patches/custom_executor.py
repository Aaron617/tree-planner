"""
Custom ScriptExecutor for Tree-Planner.

This module extends VirtualHome's ScriptExecutor with custom behavior.
"""
try:
    from virtualhome.simulation.evolving_graph.execution import ScriptExecutor
except ImportError:
    from simulation.evolving_graph.execution import ScriptExecutor

from typing import List


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
