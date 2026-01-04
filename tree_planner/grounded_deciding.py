"""
Multiprocess annotating binder programs.
"""
import sys
import time
import json
import argparse
import copy
import os
import traceback
from typing import List
import platform
import multiprocessing
from tree_planner.generation.generator import Generator
from tree_planner.arguments import get_args
import random
from tree_planner.utils.env_utils import *
from tree_planner.utils.data_utils import *
from tree_planner.utils.exec_utils import *
random.seed(42)
# env libraries
try:
    from virtualhome.simulation.evolving_graph.environment import EnvironmentGraph, EnvironmentState
    from virtualhome.simulation.evolving_graph.scripts import read_script_from_list_string, script_to_list_string, read_script_from_string
    from virtualhome.simulation.evolving_graph.execution import ScriptExecutor
    import virtualhome.simulation.evolving_graph.utils as utils
except ImportError:
    # Fallback for non-standard virtualhome installation
    from simulation.evolving_graph.environment import EnvironmentGraph, EnvironmentState
    from simulation.evolving_graph.scripts import read_script_from_list_string, script_to_list_string, read_script_from_string
    from simulation.evolving_graph.execution import ScriptExecutor
    import simulation.evolving_graph.utils as utils
ROOT_DIR = os.path.join(os.path.dirname(__file__))


def construct_program_text(task_name, instruction=None, program=None):
    res = f'Task: {task_name}'
    if instruction is not None:
        res += f'\nInstruction: {instruction}'
    if program is not None:
        # p = '\n'.join(program + ['[END]'])  # @mengkang for the end prob
        p = '\n'.join(program)
        res += f'\n{p}'
    return res


from tree_planner.utils.exec_utils import grounded_exec, calc_gcr


def worker_annotate(
        pid: int,
        args,
        generator: Generator,
        g_eids: List,
        dataset,
        tokenizer,
        task_to_graph
):
    """
    A worker process for annotating.
    """
    # if pid != 0:
    #     sys.stdout = open(f'./log/output_{pid}.log', 'w', encoding='utf')
    g_dict = dict()
    metrics_list = []
    for g_eid in g_eids:
        g_data_item = dataset[g_eid]
        g_dict[g_eid] = {
            'ori_data_item': copy.deepcopy(g_data_item)
        }
        try:
            # graph_dict = json.load(open(args.graph_dict_path))
            graph_dict = task_to_graph[g_data_item['task']]
            init_graph_dict = copy.deepcopy(graph_dict)
            executability, state, graph_state_list, info, selected_plan, usage, _traceback, retry_cnt, index_list = grounded_exec(
                args=args,
                script_str_list=g_data_item['valid_programs'],
                graph_dict=graph_dict,
                task=g_data_item['task'],
                generator=generator,
                g_eid=g_eid,
                goal_conditions=g_data_item['goal_condition']
            )
            if executability:
                # gcr = calc_gcr(init_graph_dict, state.to_dict(), goal_condition=g_data_item['goal_condition'])
                gcr = max([calc_gcr(init_graph_dict, s, goal_condition=g_data_item['goal_condition']) for s in graph_state_list])
                sr = 1 if abs(gcr - 1) < 1e-10 else 0
            else:
                gcr, sr = 0.0, 0
            metrics = {"executability": int(executability), "success rate": sr, "gcr": gcr, 'tokens': usage + g_data_item['tokens'], 'retry': retry_cnt}
            g_dict[g_eid].update(
                {
                    'plan': selected_plan,
                    'index_list': index_list,
                    'metrics': metrics,
                    'usage': usage,
                    'info': info,
                    'traceback': _traceback,
                }
            )
            metrics_list.append(metrics)
        except Exception as e:
            print(f"Process#{pid}: eid#{g_eid}, generation error: {e}")
            g_dict[g_eid].update({'generation_error':str(e)})
            print(traceback.format_exc())
            # raise e
    # show_result(metrics_list)
    return g_dict, metrics_list




'''
datasets : list of dictionary
'''
def main(args):
    # Build paths
    args.api_keys_file = os.path.join(ROOT_DIR, args.api_keys_file)
    args.save_dir = os.path.join(ROOT_DIR, args.save_dir)
    # os.makedirs(args.save_dir, exist_ok=True)
    start_time = time.time()
    # Load post-processed data
    generation_result = json.load(open(os.path.join(args.save_dir, args.processed_plan_generation_result_file)))
    # filter with task names
    all_tasks = [_.strip() for _ in open("./debugging/all_tasks_v3_modified.txt").readlines()]
    generation_result = list(filter(lambda x:x['task'] in all_tasks, generation_result))
    print("Number of samples in the dataset:", len(generation_result))
    # Load openai keys and split
    with open(args.api_keys_file, 'r') as f:
        keys = [line.strip() for line in f.readlines()]
    keys_process = [[''] for _ in range(args.n_processes)]
    for _, k in enumerate(keys): keys_process[int(_)%args.n_processes].append(k)
    keys_process = [_[1:] for _ in keys_process]
    # Split Dataset
    generate_eids = list(range(len(generation_result)))
    generate_eids_group = [[] for _ in range(args.n_processes)]
    for g_eid in generate_eids:
        generate_eids_group[int(g_eid) % args.n_processes].append(g_eid)
    print('\n******* Annotating *******')
    g_dict = dict()
    worker_results = []
    task_to_graph = json.load(open(args.task_to_graph))
    pool = multiprocessing.Pool(processes=args.n_processes)
    for pid in range(args.n_processes):
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path=os.path.join(ROOT_DIR, "utils", "gpt2"))
        generator = Generator(args, keys=keys_process[pid], tokenizer=tokenizer)
        worker_results.append(pool.apply_async(worker_annotate, args=(
            pid,
            args,
            generator,
            generate_eids_group[pid],
            generation_result,
            tokenizer,
            task_to_graph
        )))

    # Merge annotation results
    metrics_list_all = []
    for r in worker_results:
        worker_g_dict, metrics_list = r.get()
        metrics_list_all += metrics_list
        g_dict.update(worker_g_dict)
    pool.close()
    pool.join()
    print(f"Elapsed time: {time.time() - start_time}")
    return g_dict



if __name__ == '__main__':
    if platform.system() == "Darwin":
        multiprocessing.set_start_method('spawn')
    args = get_args()
    os.makedirs(args.save_dir, exist_ok=True)
    args.stop_tokens = ['\n']
    print(f'Grounded Deciding stop tokens {args.stop_tokens}')
    res = main(args)
    json.dump(obj=res, fp=open(os.path.join(args.save_dir, args.grounded_deciding_result_file), 'w', encoding='utf'), indent=4)
