import copy
import json
import os
import random
import sys
ROOT_DIR = os.path.join(os.path.dirname(__file__))
# print(ROOT_DIR)
sys.path.append(f'{ROOT_DIR}/../../simulation')
sys.path.append(f'{ROOT_DIR}/../../')
import evolving_graph.utils as utils
from evolving_graph.environment import EnvironmentGraph, EnvironmentState, Relation, State
# import simulation.evolving_graph.utils as utils
# from simulation.evolving_graph.environment import EnvironmentGraph, EnvironmentState, Relation, State
# from simulation.evolving_graph.execution import Relation, State


# adapt from https://github.com/ShuangLI59/Pre-Trained-Language-Models-for-Interactive-Decision-Making
def _mask_state(state):
    # Assumption: inside is not transitive. For every object, only the closest inside relation is recorded
    # print('self.character_n: {}, len:{}, char_index: {}'.format(self.character_n, len(self.character_n), char_index))
    # print('%d agents: get partial observation of agent %d' % (len(self.character_n), char_index))
    if isinstance(state, dict):
        state = state
    else:
        state = state.to_dict()
    character = [n for n in filter(lambda x:x['class_name'] == 'character', state['nodes'])]
    assert len(character) == 1
    character = character[0]
    # find character
    character_id = character['id']
    id2node = {node['id']: node for node in state['nodes']}
    inside_of, is_inside, edge_from = {}, {}, {}
    grabbed_ids = []
    for edge in state['edges']:

        if edge['relation_type'] == 'INSIDE':
            if edge['to_id'] == edge['from_id']:
                continue
            if edge['to_id'] not in is_inside.keys():
                is_inside[edge['to_id']] = []

            is_inside[edge['to_id']].append(edge['from_id'])
            inside_of[edge['from_id']] = edge['to_id']


        elif 'HOLDS' in edge['relation_type']:
            if edge['from_id'] == character['id']:
                grabbed_ids.append(edge['to_id'])


    character_inside_ids = inside_of[character_id]
    room_id = character_inside_ids


    object_in_room_ids = is_inside[room_id]

    # Some object are not directly in room, but we want to add them
    curr_objects = list(object_in_room_ids)
    obj_id_set = set(curr_objects)  # deduplicate
    while len(curr_objects) > 0:
        objects_inside = []
        for curr_obj_id in curr_objects:
            new_inside = is_inside[curr_obj_id] if curr_obj_id in is_inside.keys() else []
            new_inside = list(filter(lambda x:x not in obj_id_set, new_inside))
            objects_inside += new_inside
            obj_id_set = obj_id_set | set(new_inside)
        object_in_room_ids += list(objects_inside)
        curr_objects = list(objects_inside)

    # Only objects that are inside the room and not inside something closed
    # this can be probably speed up if we can ensure that all objects are either closed or open
    rooms = [n for n in filter(lambda x:x['category'] == 'Rooms', state['nodes'])]
    rooms_ids = [n['id'] for n in rooms]
    object_hidden = lambda ido: inside_of[ido] not in rooms_ids and 'CLOSED' in id2node[inside_of[ido]]['states']

    observable_object_ids = [object_id for object_id in object_in_room_ids if not object_hidden(object_id)] + rooms_ids
    observable_object_ids += grabbed_ids


    partilly_observable_state = {
        "edges": [edge for edge in state['edges'] if edge['from_id'] in observable_object_ids and edge['to_id'] in observable_object_ids],
        "nodes": [id2node[id_node] for id_node in observable_object_ids]
    }

    return partilly_observable_state


def get_object_id_list_from_script(script_lines):
    # assert len(script) == 1
    object_id_list = set()
    for script_line in script_lines:
        script_line = script_line[0]
        for parameter in script_line.parameters:
            object_id = parameter.instance
            object_id_list.add(object_id)
    return object_id_list

def multiple_objects_related_observation(object_id_list, partially_observation):
    res = {}
    res.update({
        'nodes': [node for node in filter(lambda x:x['id'] in object_id_list, partially_observation['nodes'])],
        'edges': [edge for edge in filter(lambda x:x['from_id'] in object_id_list or x['to_id'] in object_id_list, partially_observation['edges'])],
    })
    return res


num_to_eng = {1:'one', 2:'two', 3:'three', 4:'four', 5:'five', 6:'six', 7:'seven', 8:'eight'}


def ontology_observation_prompt(state):   # @mengkang what is the agent holding, the state of the agent, where is the agent
    # name_equivalence = utils.load_name_equivalence()
    # state = EnvironmentState(graph_dict)
    res = []
    char = state.get_nodes_by_attr('class_name', 'character')[0]
    rh = state.get_nodes_from(char, Relation.HOLDS_RH)
    lh = state.get_nodes_from(char, Relation.HOLDS_LH)
    hand_prompt = []
    for h, s in zip([rh, lh], ['right', 'left']):
        if len(h) == 0:
            # res.append(f'You are holding nothing in your {s} hand')
            obj_name = 'nothing'
        else:
            obj_name = h[0].class_name
        # res.append(f'You are holding {obj_name} in your {s} hand')
        hand_prompt.append(f'{obj_name} in your {s} hand')
    hand_prompt = ' and '.join(hand_prompt)
    # res.append(f'You are holding {hand_prompt}')
    char_state = char.states
    # assert len(char_state) <= 1
    state_str_list = [str.lower(str(_).replace('State.', '')) for _ in list(char.states)]
    if 'clean' in state_str_list:
        state_str_list.remove('clean')
    assert len(state_str_list) <= 1
    # print(state_str_list)
    if len(state_str_list) == 0:
        state_str = 'standing'
    else:
        # state_str = str(list(char.states)[0])
        # state_str = str.lower(state_str.replace('State.', ''))
        state_str = state_str_list[0]
        obj_name = state.get_nodes_from(char, Relation.ON)[0].class_name
        state_str += f' on {obj_name}'
    room_inside = state.get_nodes_from(char, Relation.INSIDE)[0].class_name
    res.append(f'Currently, you are {state_str} in the {room_inside}, and holding {hand_prompt}.')
    return '\n'.join(res)


def translate_sub_graph_to_text(graph_dict, observation):
    obj_id_to_class_name = {_['id']:_['class_name'] for _ in graph_dict['nodes']}
    id_to_node = {node['id']:node for node in graph_dict['nodes']}
    edge_text_list = []
    room_obj_map = {}
    for _e in observation['edges']:
        from_obj, to_obj = obj_id_to_class_name[int(_e['from_id'])], obj_id_to_class_name[int(_e['to_id'])]
        rel_type = _e['relation_type'].lower()
        if rel_type == 'close': rel_type = 'close to'
        to_node = id_to_node[_e['to_id']]
        if to_node['category'] == 'Rooms' and rel_type == 'inside':
            if to_obj not in room_obj_map:
                room_obj_map[to_obj] = []
            room_obj_map[to_obj].append(from_obj)
        edge_text_list.append(f'{from_obj} is {rel_type} {to_obj}')
    edge_text_list = list(set(edge_text_list))
    for room, obj_list in room_obj_map.items():
        obj_str = ','.join(obj_list)
        edge_text_list.append(f'{obj_str} is inside {room}')
    node_text_list = []
    for node in observation['nodes']:
        class_name = node['class_name']
        state_text = ', '.join([_.lower() for _ in node['states']])
        node_text_list.append(f'{class_name} is {state_text}')
    node_text_list = list(set(node_text_list))
    res = ''
    if len(node_text_list) > 0:
        res += '\n'.join(node_text_list)
    if len(edge_text_list) > 0:
        res += '\n' + '\n'.join(edge_text_list)
    return res


from evolving_graph.scripts import Script, read_script_from_list_string
def observation_prompt(graph_dict, action_choices): # for grounded deciding
    # observation : partial graph_dict
    script_lines = [read_script_from_list_string([c]) for c in action_choices]
    object_observation = multiple_objects_related_observation(get_object_id_list_from_script(script_lines), _mask_state(graph_dict))
    ontology_prompt = ontology_observation_prompt(EnvironmentState(EnvironmentGraph(graph_dict), utils.load_name_equivalence(), instance_selection=True))
    res = ontology_prompt
    res += '\n' + translate_sub_graph_to_text(graph_dict, object_observation)
    return res



def get_env_prompt(graph_dict):
    prompt = ''
    available_rooms_in_graph = [i['class_name'] for i in filter(lambda v: v["category"] == 'Rooms', graph_dict['nodes'])]
    room_num_eng = num_to_eng[len(available_rooms_in_graph)]
    room_str = ', '.join(available_rooms_in_graph)
    prompt += f'You are in a house that consists of {room_num_eng} rooms. These rooms are {room_str}.'
    name_equivalence = utils.load_name_equivalence()
    state = EnvironmentState(EnvironmentGraph(graph_dict), name_equivalence)
    prompt += '\n' + ontology_observation_prompt(state) + '\n' + available_object_prompt(graph_dict)
    return prompt


def available_object_prompt(graph_dict):
    objs = list(set([_['class_name'] for _ in graph_dict['nodes']]))
    obj_prompt = ', '.join(objs)
    return f'Available objects in the house are : {obj_prompt}\nAll object names must be chosen from the above object list'


def plan_generation_prompt(graph_dict, prefix_path):
    prefix = ''.join(open(prefix_path, 'r', encoding='utf').readlines())
    prompt = prefix + '\n' + get_env_prompt(graph_dict)
    # print('-'*10 + 'Plan Generation Prompt' + '-'*10)
    # print(prompt)
    return prompt
    # open(out_path, 'w', encoding='utf').write(prompt)

def plan_generation_prompt_code(graph_dict, prefix_path):
    prefix = ''.join(open(prefix_path, 'r', encoding='utf').readlines())
    prompt = prefix + f'\n\"\"\"\n{get_env_prompt(graph_dict)}\n\"\"\"'
    # print('-'*10 + 'Plan Generation Prompt' + '-'*10)
    # print(prompt)
    return prompt

def progprompt_prompt(graph_dict, ):
    # graph_dict = state.to_dict()
    # 1. _mask_state()
    # 2. prompt
    pass


def grounded_deciding_prompt(args, graph_dict, task, action_choices, past_actions, error_info=''):
    obj_action_choices = copy.deepcopy(action_choices)
    if isinstance(action_choices[0], list):
        t = []
        for _ in obj_action_choices:
            if '[END]' in _:
                _.remove('[END]')
            t += _
        obj_action_choices = t
    if '[END]' in obj_action_choices:
        obj_action_choices.remove('[END]')
    prefix_path = args.grounded_deciding_prompt_path if args.retry_times == 0 else args.grounded_deciding_prompt_path[:-4] + '_error_correction.txt'
    prefix = ''.join(open(prefix_path, 'r', encoding='utf').readlines())
    env_prompt = observation_prompt(graph_dict, obj_action_choices)
    if len(past_actions) > 0:
        past_experience_prompt = '\n'.join(past_actions)
        past_experience_prompt = f'You have executed the following sub-tasks: \n{past_experience_prompt}'
    else:
        past_experience_prompt = f'This is the first sub-task you need to execute'
    # action_prompt = '\n'.join(action_choices)
    # @mengkang A. xxx B. xxx
    alphabet = [chr(_) for _ in list(range(65, 91))]
    def get_chr(idx):
        return alphabet[idx]
    if isinstance(action_choices[0], list): # sequence version of implementation. can be deleted if the performance is worse
        def get_seq_str(a):
            return ' | '.join(a)
        action_prompt = '\n'.join([f'{get_chr(idx)}. {get_seq_str(a)}' for idx, a in enumerate(action_choices)])
    else:
        action_prompt = '\n'.join([f'{get_chr(idx)}. {a}' for idx, a in enumerate(action_choices)])
    action_prompt = f'Among the following sub-tasks (or sub-task sequence), which one would you take.\n{action_prompt}'
    prompt = prefix + f'\nYour current observation is: {env_prompt}' + f'\nYour task is: {task}' + f'\n{past_experience_prompt}'
    if error_info == '':
        prompt = prompt + f'\n{action_prompt}' + f'\nThe best choice of sub-task is:\n'
    else:
        prompt = prompt + '\n' + error_info + f'\n{action_prompt}' + '\nA corrective choice of sub-task would be:\n'
    return prompt

