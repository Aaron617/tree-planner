import os
import json
import re
import sys
ROOT_DIR = os.path.join(os.path.dirname(__file__))
# sys.path.append("../../simulation")
sys.path.append(f'{ROOT_DIR}/../../')
from simulation.evolving_graph.scripts import parse_script_line
from sampling_grounding_deciding.utils.retriever import Retriever

# ignore
def parse_woconds(file_path):
    data = [line.strip() for line in open(file_path, 'r', encoding='utf').readlines()]
    assert data[2] == data[3] == ''
    task_name, task_desc, program = data[0], data[1], data[4:]
    return {'task': task_name, 'task_description': task_desc, 'program': program}


def parse_generation(g):
    return g.strip().split('\n')



# @mengkang whether to use pre-conditions / no
def check_action_format(action_str):
    try:
        data = parse_script_line(action_str, 0)
    except Exception as e:  # Unknown action
        info = str(e)
        return None, info
    return data, ''

def check_action_valid(action_str, graph_dict):
    data, info = check_action_format(action_str)
    if data is None:
        return False, info
    objs = list(set([_['class_name'].lower().replace(' ', '_') for _ in graph_dict['nodes']]))
    obj = data.object()
    sub = data.subject()
    # Unknow obj
    if not(obj.name in objs if obj is not None else True):
        return False, f'Unknow Object \"{obj.name}\"'
    if not(sub.name in objs if sub is not None else True):
        return False, f'Unknow Object \"{sub.name}\"'
    return True, ''


def del_graph(a, b):
    # edges
    node_id_to_class_name = {n['id']:n['class_name'] for n in a['nodes']}
    b_edges = [(edge['from_id'], edge['to_id'], edge['relation_type'], node_id_to_class_name[edge['from_id']], node_id_to_class_name[edge['to_id']]) for edge in b['edges']]
    a_edges = [(edge['from_id'], edge['to_id'], edge['relation_type'], node_id_to_class_name[edge['from_id']], node_id_to_class_name[edge['to_id']]) for edge in a['edges']]
    b_edges, a_edges = set(b_edges), set(a_edges)
    res = list(a_edges - b_edges)
    # delete close @mengkang should move this line? most of 'CLOSE' relation is not necessary
    # this is a heuristic process for graph deletion
    res = list(filter(lambda x:x[2]!='CLOSE', res))
    # nodes
    def node_set(nodes):
        res = []
        for node in nodes:
            for state in node['states']:
                res.append((node['id'], node['class_name'], state))
        return set(res)
    a_nodes = node_set(a['nodes'])
    b_nodes = node_set(b['nodes'])
    return res, list(a_nodes-b_nodes)   # edges, nodes

# Adapt from https://github.com/ShuangLI59/Pre-Trained-Language-Models-for-Interactive-Decision-Making
def parse_language_from_action_script(action_script):
    act_name = re.findall(r"\[([A-Za-z0-9_]+)\]", action_script)[0]

    obj_name = re.findall(r"\<([A-Za-z0-9_]+)\>", action_script)[0]
    obj_id = re.findall(r"\(([A-Za-z0-9_]+)\)", action_script)[0]
    obj_id = int(obj_id)

    if '[putback]' in action_script.lower() or '[putin]' in action_script.lower():
        obj_name2 = re.findall(r"\<([A-Za-z0-9_]+)\>", action_script)[1]
        obj_id2 = re.findall(r"\(([A-Za-z0-9_]+)\)", action_script)[1]
        obj_id2 = int(obj_id2)
    else:
        obj_name2 = None
        obj_id2 = None

    return act_name, obj_name, obj_id, obj_name2, obj_id2


# @mengkang post process of plan generation. Align the objects in plan to objects that exist in the environment
class Obj_Translator:
    def __init__(self, retriever: Retriever, obj_list):
        self.retriever = retriever
        self.obj_list = obj_list
        self.obj_list_embedding = retriever.init_corpus_embedding(self.obj_list, batch_size=32)

    def translate_obj(self, obj):
        name = obj
        if name in self.obj_list:
            return name
        else:
            idx = self.retriever.find_most_similar(query_str=name, corpus_embedding=self.obj_list_embedding, topk=1)[0][0]
            return self.obj_list[idx]

    def translate_action(self, action_str):
        # data, info = check_action_format(action_str)
        # if data is None:
        #     return action_str   # no translate
        try:
            act_name, obj_name, obj_id, obj_name2, obj_id2 = parse_language_from_action_script(action_str)
            if obj_name is not None:
                action_str = action_str.replace(obj_name, self.translate_obj(obj_name))
            if obj_name2 is not None:
                action_str = action_str.replace(obj_name2, self.translate_obj(obj_name2))
        except:
            # print(action_str)
            pass
        return action_str


def clean_action(script_str, graph_dict):
    # if there exists an unknown action, remove the action from script
    new_script_str = []
    for action_str in script_str:
        valid, info = check_action_valid(action_str, graph_dict)
        if 'unknown action' in info.lower():
            pass
        else:
            new_script_str.append(action_str)
    return new_script_str

def clean_action_wprob(script_wprob, graph_dict):
    # if there exists an unknown action, remove the action from script
    new_script_str = []
    for action_str, prob in script_wprob:
        valid, info = check_action_valid(action_str, graph_dict)
        if 'unknown action' in info.lower():
            pass
        else:
            new_script_str.append((action_str, prob))
    return new_script_str


def post_process_of_generation(generation_result, task_to_graph, obj_translate=False):
    # data = json.load(open(generation_file))
    data = generation_result
    res = []
    for k, item in data.items():
        task = item['ori_data_item']['task']
        graph_dict = task_to_graph[task]
        if obj_translate:
            obj_list = list(set([_['class_name'] for _ in graph_dict['nodes']]))
            retriver = Retriever(cuda='cuda:1')
            ot = Obj_Translator(retriever=retriver, obj_list=obj_list)
        tokens = item['usage']['total_tokens']
        ori_data_item = item['ori_data_item']
        ori_data_item['plan_generation_prompt'] = ori_data_item['plan_generation_prompt']
        ori_data_item.pop('plan_generation_prompt')
        generations = item['generations']
        program_str_list = []
        invalid_programs = []
        for g in generations:
            gt = g[0]
            script_str = parse_generation(gt)
            # Translate Object
            if obj_translate: script_str = [ot.translate_action(action_str) for action_str in script_str]
            # clean action
            script_str = clean_action(script_str, graph_dict)
            if all([check_action_valid(_, graph_dict)[0] for _ in script_str]):
                program_str_list.append(script_str)
            else:
                info_list = [check_action_valid(_, graph_dict)[1] for _ in script_str]
                invalid_programs.append('\n'.join(list(['\t'.join([a, b]) for a, b in zip(script_str, info_list)])))
        # program_str_list = [parse_generation(g[0]) for g in generations]
        # item.update({'programs': program_str_list})
        ori_data_item.update({'valid_programs': program_str_list, 'invalid_programs': invalid_programs, 'tokens': tokens})
        res.append(ori_data_item)
    return res
    # return data
