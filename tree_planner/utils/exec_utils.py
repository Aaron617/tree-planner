import copy
import json
import sys
import os
ROOT_DIR = os.path.join(os.path.dirname(__file__))

try:
    from virtualhome.simulation.evolving_graph import utils as vh_utils
    from virtualhome.simulation.evolving_graph.execution import Relation, State
    from virtualhome.simulation.evolving_graph.scripts import read_script, script_to_list_string, read_script_from_list_string, read_script_from_string
    from virtualhome.simulation.evolving_graph.execution import ScriptExecutor
    from virtualhome.simulation.evolving_graph.environment import EnvironmentGraph, EnvironmentState
    from virtualhome.simulation.evolving_graph.preparation import AddMissingScriptObjects, AddRandomObjects, ChangeObjectStates, \
        StatePrepare, AddObject, ChangeState, Destination
except ImportError:
    from simulation.evolving_graph import utils as vh_utils
    from simulation.evolving_graph.execution import Relation, State
    from simulation.evolving_graph.scripts import read_script, script_to_list_string, read_script_from_list_string, read_script_from_string
    from simulation.evolving_graph.execution import ScriptExecutor
    from simulation.evolving_graph.environment import EnvironmentGraph, EnvironmentState
    from simulation.evolving_graph.preparation import AddMissingScriptObjects, AddRandomObjects, ChangeObjectStates, \
        StatePrepare, AddObject, ChangeState, Destination

# add_preconds module is not available in the standard VirtualHome
# import add_preconds
# from virtualhome.simulation.evolving_graph.check_programs import modify_objects_unity2script

from tree_planner.evolving_graph_patches.custom_graph_dict_helper import custom_graph_dict_helper
# from tree_planner.evolving_graph_patches.custom_executor import CustomScriptExecutor
from tree_planner.utils.data_utils import del_graph
from tree_planner.utils.deciding_graph import Deciding_Tree
from tree_planner.utils.env_utils import grounded_deciding_prompt


# get script prepared for execution (map the id in script (like (1) or (2)) to the exact object id ((237)) in the environment)
def prepare_for_execution(graph_dict, script):
    max_nodes = 400
    helper = custom_graph_dict_helper(max_nodes=max_nodes)
    helper.initialize(graph_dict)
    # what modify_objects_unity2script do except precond
    # script, precond = modify_objects_unity2script(helper, script, precond)
    """Convert the script's objects to match unity programs
    """
    # @mengkang this alignment leads to bug. like this will change couch -> sofa. but couch is in the environment but sofa not
    # for script_line in script:
    #     for param in script_line.parameters:
    #         if param.name in helper.unity_object2script_object:
    #             param.name = helper.unity_object2script_object[param.name]
    id_mapping = {}
    id_mapping, first_room, room_mapping = helper.mapping(script, graph_dict, id_mapping)   # the instance in the script changed in this function


def exec_one_step(script, state: EnvironmentState, executor):
    prev_state = state
    #print("in execute_one_step, char_index = {}".format(self.char_index))
    state = next(executor.call_action_method(script, state, executor.info), None)
    if state is None:
        return False, prev_state
    return True, state

# plan-level execution
def exec_script(script_str, graph_dict, verbose=False):
    script = read_script_from_list_string(script_str)
    # Assume the execution process won't corrupt here, put the filter process of precond in post-poss of generation result
    # try:
    #     precond = add_preconds.get_preconds_script(script_str).printCondsJSON()
    # except add_preconds.ScriptFail as e:
    #     return False, None, [], str(e)
    # prepare for exec
    try:
        prepare_for_execution(graph_dict, script)
    except Exception as e:
        return False, None, None, str(e)
    # exec
    graph = EnvironmentGraph(graph_dict)
    name_equivalence = vh_utils.load_name_equivalence()
    executor = ScriptExecutor(graph, name_equivalence)
    info = executor.info
    state = EnvironmentState(executor.graph, executor.name_equivalence, instance_selection=True)
    graph_state_list = []
    for i in range(len(script)):
        prev_state = state
        graph_state_list.append(state.to_dict())
        future_script = script.from_index(i)
        executability, state = exec_one_step(future_script, state, executor)
        if not executability:
            if verbose: print(executor.info.get_error_string())
            return False, state, graph_state_list, executor.info.get_error_string()
    graph_state_list.append(state.to_dict())
    return True, state, graph_state_list, ''


def calc_gcr(init_graph_dict, final_graph_dict, goal_condition):
    edge_list, node_list = del_graph(final_graph_dict, init_graph_dict)
    gold_edges, gold_nodes = goal_condition
    gold_edges = [tuple(_) for _ in gold_edges]
    gold_nodes = [tuple(_) for _ in gold_nodes]
    s = len(gold_edges) + len(gold_nodes)
    # print(edge_list, node_list)
    # print(gold_edges, gold_nodes)
    return (len(set(edge_list) & set(gold_edges)) + len(set(node_list) & set(gold_nodes))) / s

import traceback
def calc_metrics(script_str, graph_dict, goal_condition, verbose=True):
    def float_equal(a, b):
        return abs(a-b) < 1e-10
    metric_list = []
    init_graph_dict = copy.deepcopy(graph_dict)
    try:
        executability, state, graph_state_list, info = exec_script(script_str, init_graph_dict, False)
        if executability:
            gcr = calc_gcr(init_graph_dict, state.to_dict(), goal_condition)
            metric_list.append((int(executability), gcr))
        elif verbose:
            print(info)
            metric_list.append((0, 0.0))
    except Exception as e:
        # traceback.print_exc()
        if verbose:
            print(str(e))
        metric_list.append((0, 0.0))
        info = str(e)
    executability, gcr = sorted(metric_list, key=lambda x:x[1], reverse=True)[0]
    sr = 1 if float_equal(gcr, 1) else 0
    return {"executability": int(executability), "success rate": sr, "gcr": gcr}, info


def most_freq(seq):
    chrs = {chr(_) for idx, _ in enumerate(list(range(65, 91)))}
    freq_map = {}
    for _ in seq:
        if _ not in freq_map:
            freq_map[_] = 0
        freq_map[_] += 1
    ignored_keys = []
    for k, v in freq_map.items():
        if k not in chrs:
            # freq_map.pop(k)
            ignored_keys.append(k)
    for k in ignored_keys:
        freq_map.pop(k)
    return sorted(list(freq_map.items()), key=lambda x:x[1], reverse=True)[0][0]


def post_process_of_generated_action(g):
    return g.strip().replace('.', '')


def construct_error_info(past_error_info, error_info, step):
    cur_error_info = f'The sub-task: \"{step}\" caused an error: {error_info}'
    if past_error_info != '':
        return f'{past_error_info}\n{cur_error_info}'
    else:
        return cur_error_info

def construct_error_info_global_replanning(past_error_info, error_info, step, history):
    history = '\n'.join(history)
    cur_error_info = f'The previous failed plan is: \n{history}.\n The sub-task: \"{step}\" caused an error: {error_info}\n'
    if past_error_info != '':
        return f'{past_error_info}\n{cur_error_info}'
    else:
        return cur_error_info


def construct_gd_error_info(past_error_info, error_info, step):
    cur_error_info = f'Your previously choosed sub-task: \"{step}\" caused an error: {error_info}'
    if past_error_info != '':
        return f'{past_error_info}\n{cur_error_info}'
    else:
        return cur_error_info


def grounded_exec(args, script_str_list, graph_dict, task, generator, g_eid, goal_conditions, verbose=False):
    max_retry_times, retry_cnt = args.retry_times, 0    # when retry_times == 0, do not do error correction
    end_of_execution = ''   # choose in ['success', 'failed']
    return_error_info = None
    # prepare environment and executor
    init_graph_dict = copy.deepcopy(graph_dict)
    graph = EnvironmentGraph(graph_dict)
    name_equivalence = vh_utils.load_name_equivalence()
    executor = ScriptExecutor(graph, name_equivalence)
    info = executor.info
    state = EnvironmentState(executor.graph, executor.name_equivalence, instance_selection=True)
    # construct deciding tree
    script_list = [read_script_from_list_string(_) for _ in script_str_list]
    new_script_list = []
    for _ in script_list:
        try:
            prepare_for_execution(graph_dict, _)
            new_script_list.append(_)
        except Exception as e:
            # print(str(e))
            continue
    script_list = new_script_list
    script_str_list_aligned = [script_to_list_string(_) for _ in script_list]
    # dg = Deciding_Graph(script_str_list_aligned)
    dt = Deciding_Tree(script_str_list_aligned, task)
    node = dt.start_point()

    graph_state_list, state_traceback = [], []
    plan = []
    _traceback = []
    usage_all = 0
    chr_to_idx = {chr(_):idx for idx, _ in enumerate(list(range(65, 91)))}
    # for t in range(dt.max_steps):
    while True:
        error_info = '' # for prompting error correction
        prev_state = state
        graph_state_list.append(state.to_dict())
        state_traceback.append(copy.deepcopy(state))
        while True:
            # choices = dg.choices_at_t(t)
            # choices = node.get_choices()
            choices = node.get_valid_choices()
            if len(choices) == 1:
                choice = choices[0]
                prompt = ''
            else:
                # seq version
                if args.prompt_choices_sequence:
                    # prompt_choices = node.get_valid_choices_sequence()
                    # prompt_choices = node.get_valid_choices_beam(8)
                    prompt_choices = node.get_valid_choices()
                # original version
                else:
                    prompt_choices = choices
                prompt = grounded_deciding_prompt(args, state.to_dict(), task, prompt_choices, plan, error_info)
                print(prompt)
                response_dict, usage = generator.generate_one_pass(
                    prompts=[(g_eid, prompt)],
                    verbose=False
                )
                usage_all += usage['total_tokens']
                # @mengkang alpha choice selection
                llm_gen = [_[0].strip().replace('.', '')[:1] for _ in response_dict[g_eid]]
                print(llm_gen)
                c = most_freq(llm_gen)
                choice = choices[chr_to_idx[c]]
                print(choice)
            # print(choice)
            if choice == '[END]':   # end of execution (success)
                end_of_execution = 'success'
                break
            candidate_node = node.find_son_by_action(action=choice)
            _traceback.append({'action': choice, 'prompt':prompt})
            # exec
            future_script = read_script_from_string(choice)
            # future_script = script_list[dg.get_idx_list(choice, t)[0]].from_index(t)
            executability, state = exec_one_step(future_script, state, executor)
            if not executability:
                if verbose: print(executor.info.get_error_string())
                if retry_cnt >= max_retry_times:    # end of execution (failed)
                    end_of_execution = 'failed'
                    return_error_info = executor.info.get_error_string()
                    break
                    # return False, state, graph_state_list, executor.info.get_error_string(), plan, usage_all, _traceback, retry_cnt
                else:
                    candidate_node.modify_status()    # True -> False
                    retry_cnt += 1
                    # @mengkang do we need to leverage the error info (feedback from the environment)? / yes
                    # 1. if there are other choices at current time step, let the llm re-choose
                    # 2. if not, move back to the last time-step where other choices are available
                    if len(node.get_valid_choices()) > 0:
                        error_info = construct_gd_error_info(error_info, executor.info.messages[-1], choice)
                        continue
                    else:   # move back and recover state
                        # move back
                        traceback_plan = [choice]
                        while node is not None and len(node.get_valid_choices()) == 0:
                            node.modify_status()
                            traceback_plan.append(node.action_str)
                            node = node.parent
                        if node is None:
                            end_of_execution = 'failed'
                            return_error_info = executor.info.get_error_string()
                            break
                        traceback_plan.reverse()
                        error_info = construct_gd_error_info(error_info, executor.info.messages[-1], '|'.join(traceback_plan))
                        # recover state
                        t = node.layer_id + 1
                        state = state_traceback[t]
                        state_traceback = state_traceback[:t+1]
                        graph_state_list = graph_state_list[:t+1]
                        plan = plan[:t+1]
                        print(node.action_str, plan)
                        continue
            else:
                node = candidate_node
                current_graph_dict = state.to_dict()
                if abs(calc_gcr(init_graph_dict, current_graph_dict, goal_conditions) - 1) < 1e-5:
                    end_of_execution = 'success'
            break
        # _traceback.append({'action': choice, 'prompt':prompt})
        if choice != '[END]':
            plan.append(choice)
        if end_of_execution in ['success', 'failed']:
            if end_of_execution == 'success':
                graph_state_list.append(state.to_dict())
                return True, state, graph_state_list, '', plan, usage_all, _traceback, retry_cnt, node.idx_list
            else:
                return False, state, graph_state_list, return_error_info, plan, usage_all, _traceback, retry_cnt, []


if __name__ == "__main__":
    script_str = [
        '[WALK] <bedroom> (67)',
        '[WALK] <home_office> (319)',
        '[WALK] <shoes> (1016)',
        '[FIND] <shoes> (1016)',
        '[GRAB] <shoes> (1016)',
        '[PUTOFF] <shoes> (1016)'
    ]
    graph_dict = json.load(open("../../example_graphs/ours_env1.json"))
    id2node = {node['id']:node for node in graph_dict['nodes']}
    def get_class_name(_id):
        return id2node[_id]['class_name']
    def shoes_on_char(graph_dict):
        for edge in graph_dict['edges']:
            from_obj, to_obj = get_class_name(edge['from_id']), get_class_name(edge['to_id'])
            rel_type = edge['relation_type']
            if (from_obj == 'shoes' or to_obj == 'shoes') and rel_type == 'ON':
                print(from_obj, rel_type, to_obj)
                break
    script = read_script_from_list_string(script_str)
    graph = EnvironmentGraph(graph_dict)
    name_equivalence = vh_utils.load_name_equivalence()
    executor = ScriptExecutor(graph, name_equivalence)
    state = EnvironmentState(executor.graph, executor.name_equivalence, instance_selection=True)
    graph_state_list = []
    for i in range(len(script)):
        prev_state = state
        graph_state_list.append(state.to_dict())
        future_script = script.from_index(i)
        executability, state = exec_one_step(future_script, state, executor)
        print(script_str[i])
        shoes_on_char(state.to_dict())
        if not executability:
            print(executor.info.get_error_string())
