"""
Multiprocess annotating binder programs.
"""
import sys
sys.path.append("../simulation")
import time
import json
import argparse
import copy
import os
import traceback
from typing import List
import platform
import multiprocessing
from generation.generator import Generator
from arguments import get_args
import random
from utils.env_utils import *
random.seed(42)


def construct_program_text(task_name, instruction=None, program=None):
    res = f'Task: {task_name}'
    if instruction is not None:
        res += f'\nInstruction: {instruction}'
    if program is not None:
        # p = '\n'.join(program + ['[END]'])  # @mengkang for the end prob
        p = '\n'.join(program)
        res += f'\n{p}'
    return res


def build_few_shot_prompt(
        examples,
        n_shots
):
    # @mengkang this version of implementation does not take instruction into consideration
    return '\n\n'.join(construct_program_text(_e['task'], None, _e['program']) for _e in examples[:n_shots])


ROOT_DIR = os.path.join(os.path.dirname(__file__))


def worker_annotate(
        pid: int,
        args,
        generator: Generator,
        g_eids: List,
        dataset,
        tokenizer,
        retrieval_dataset,
        task_to_idx,
        task_to_graph
):
    """
    A worker process for annotating.
    """
    # if pid != 0:
    #     sys.stdout = open(f'./log/output_{pid}.log', 'w', encoding='utf')
    g_dict = dict()
    built_few_shot_prompts = []
    for g_eid in g_eids:
        try:
            g_data_item = dataset[g_eid]
            g_dict[g_eid] = {
                'generations': [],
                'ori_data_item': copy.deepcopy(g_data_item)
            }
            n_shots = args.n_shots
            max_prompt_tokens = args.max_api_total_tokens - args.max_generation_tokens
            task = g_data_item['task']
            assert task_to_idx is None  # retrieve based examplar waiting for implementation
            examples = retrieval_dataset # fixed prompt
            prefix = plan_generation_prompt(
                # graph_dict=json.load(open(args.graph_dict_path, 'r', encoding='utf')),
                graph_dict=task_to_graph[task],
                prefix_path=args.plan_generation_prompt_path
            )
            # instruct = g_data_item['programs'][0]['task_description'] if args.instruction else None   # deprecated
            instruct = g_data_item['programs']['task_description'] if args.instruction else None
            # Ensure the input length fit Codex max input tokens by shrinking the n_shots
            few_shot_prompt = build_few_shot_prompt(examples, n_shots)
            prompt = prefix + '\n\n' + few_shot_prompt + '\n\n' + construct_program_text(task_name=task, instruction=instruct, program=None) + '\n'
            while len(tokenizer.tokenize(prompt)) >= max_prompt_tokens:
                n_shots -= 1
                assert n_shots >= 0
                few_shot_prompt = build_few_shot_prompt(examples, n_shots)
                prompt = prefix + '\n\n' + few_shot_prompt + '\n\n' + construct_program_text(task_name=task, instruction=instruct, program=None) + '\n'
            assert len(tokenizer.tokenize(prompt)) < max_prompt_tokens
            g_dict[g_eid]['ori_data_item'].update({'plan_generation_prompt': prompt})   # @mengkang for debugging
            print(f"Process#{pid}: Building prompt for eid#{g_eid}")
            built_few_shot_prompts.append((g_eid, prompt))
            if len(built_few_shot_prompts) < args.n_parallel_prompts:   # @mengkang we assert args.n_parallel_prompts==1
                continue

            # print(f"Process#{pid}: Prompts ready with {len(built_few_shot_prompts)} parallels. Run openai API.")
            response_dict, usage = generator.generate_one_pass(
                prompts=built_few_shot_prompts,
                verbose=args.verbose
            )
            for eid, g_pairs in response_dict.items():
                # g_pairs = sorted(g_pairs, key=lambda x: x[-1], reverse=True)
                g_dict[eid]['generations'] = g_pairs
            assert len(set([eid for eid, g_pairs in response_dict.items()])) == 1
            g_dict[list(response_dict.keys())[0]]['usage'] = usage
            built_few_shot_prompts = []
        except Exception as e:
            print(f"Process#{pid}: eid#{g_eid}, generation error: {e}")
            print(traceback.format_exc())
            # raise e

    return g_dict


'''
datasets : list of dictionary
'''
def annotate_multi_process_run(args):
    # Build paths
    args.api_keys_file = os.path.join(ROOT_DIR, args.api_keys_file)
    args.save_dir = os.path.join(ROOT_DIR, args.save_dir)
    os.makedirs(args.save_dir, exist_ok=True)
    start_time = time.time()
    # Load dataset
    dataset = json.load(open(args.dataset, 'r', encoding='utf'))
    task_to_graph = json.load(open(args.task_to_graph, 'r', encoding='utf'))
    retrieval_dataset = json.load(open(args.retrieval_dataset))
    task_to_idx = json.load(open(args.example_idx_file)) if args.example_idx_file is not None else None
    print("Number of samples in the dataset:", len(dataset))
    # Load openai keys and split
    with open(args.api_keys_file, 'r') as f:
        keys = [line.strip() for line in f.readlines()]
    keys_process = [[''] for _ in range(args.n_processes)]
    for _, k in enumerate(keys): keys_process[int(_)%args.n_processes].append(k)
    keys_process = [_[1:] for _ in keys_process]
    # Split Dataset
    generate_eids = list(range(len(dataset)))
    generate_eids_group = [[] for _ in range(args.n_processes)]
    for g_eid in generate_eids:
        generate_eids_group[int(g_eid) % args.n_processes].append(g_eid)
    print('\n******* Annotating *******')
    g_dict = dict()
    worker_results = []
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
            dataset,
            tokenizer,
            retrieval_dataset,
            task_to_idx,
            task_to_graph
        )))

    # Merge annotation results
    for r in worker_results:
        worker_g_dict = r.get()
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
    save_name = os.path.join(args.save_dir, args.plan_generation_result_file)
    res = annotate_multi_process_run(args)
    json.dump(obj=res, fp=open(save_name, 'w', encoding='utf'), indent=4)
