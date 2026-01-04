import json
import os
from tree_planner.utils.data_utils import *
from tree_planner.utils.exec_utils import *

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
print(ROOT_DIR)


os.makedirs(f"../dataplace/generation_results", exist_ok=True)

plan_generation_prompt_path = os.path.join(ROOT_DIR, "prompt/plan_generation_prompt.txt")


engine = 'text-davinci-003'
n_processes = 5


def plan_generation(data_dir, save_dir, sampling_n, postfix=''):
    # plan generation
    # sampling
    temp = 0.8
    topp = 0.95
    # sampling_n = 50
    max_gen = 512
    # n_processes = 1
    n_shots = 4
    retrieval_dataset = f'{data_dir}/train.json'
    dataset_name = 'val.json'
    _ = dataset_name[:-5]
    plan_generation_prompt_path = os.path.join(ROOT_DIR, 'prompt/plan_generation_prompt.txt')
    plan_generation_result_file = f'{engine}_{sampling_n}_{postfix}.json'
    dataset = f'{data_dir}/{dataset_name}'
    task_to_graph = f'{data_dir}/task_to_graph.json'
    os.system(fr"""python -m tree_planner.plan_generation    \
                --temperature {temp}    \
                --top_p {topp}  \
                --max_generation_tokens {max_gen}   \
                --sampling_n {sampling_n}  \
                --n_parallel_prompts    1   \
                --plan_generation_result_file   {plan_generation_result_file}   \
                --n_processes {n_processes} \
                --n_shots   {n_shots}       \
                --dataset {dataset} \
                --retrieval_dataset {retrieval_dataset} \
                --save_dir {save_dir}   \
                --plan_generation_prompt_path   {plan_generation_prompt_path}   \
                --task_to_graph {task_to_graph} \
                --engine    {engine}
                """)
    # return os.path.join(save_dir, plan_generation_result_file)
    return plan_generation_result_file

def post_process_of_generation_result(plan_generation_result_file, data_dir, save_dir):
    post_generation_file_name = plan_generation_result_file[:-5] + '_processed.json'
    generation_result = json.load(open(os.path.join(save_dir, plan_generation_result_file)))
    task_to_graph = f'{data_dir}/task_to_graph.json'
    task_to_graph = json.load(open(task_to_graph))
    res = post_process_of_generation(generation_result, task_to_graph, obj_translate=True)
    json.dump(obj=res, fp=open(os.path.join(save_dir, post_generation_file_name), 'w', encoding='utf'), indent=4)


def grounded_deciding(plan_generation_result_file, data_dir, save_dir, retry_times, postfix):
    # global plan_generation_result_file
    # Grounded Deciding
    # temp = 0
    # topp = 1
    # sampling_n = 1
    # Majority Vote
    temp = 0.7
    topp = 1.00
    sampling_n = 20
    max_gen = 50
    # n_processes = 5
    grounded_deciding_prompt_path = os.path.join(ROOT_DIR, 'prompt/grounded_deciding_prompt.txt')
    # retry_times = 10    # 0 no error correction else
    # retry_times = 0
    grounded_deciding_result_file = plan_generation_result_file[:-5] + f'_{retry_times}_{postfix}.json'
    post_generation_file_name = plan_generation_result_file[:-5] + '_processed.json'
    n_shots = 4
    task_to_graph = f'{data_dir}/task_to_graph.json'
    os.system(fr"""python -m tree_planner.grounded_deciding    \
                --temperature {temp}    \
                --top_p {topp}  \
                --max_generation_tokens {max_gen}   \
                --sampling_n {sampling_n}  \
                --n_parallel_prompts    1   \
                --grounded_deciding_result_file   {grounded_deciding_result_file}   \
                --n_processes {n_processes} \
                --n_shots   {n_shots}       \
                --processed_plan_generation_result_file {post_generation_file_name} \
                --save_dir {save_dir}   \
                --grounded_deciding_prompt_path   {grounded_deciding_prompt_path}   \
                --task_to_graph {task_to_graph} \
                --retry_times   {retry_times}    \
                --engine    {engine}
                """)


def main():
    batch_data_dir = f'TrimmedTestScene{_}_graph'
    data_dir = f"../dataplace/data/{batch_data_dir}"
    save_dir = f"../dataplace/generation_results/{batch_data_dir}"
    sampling_n = 50
    plan_generation_result_file = plan_generation(data_dir, save_dir, sampling_n=sampling_n)
    post_process_of_generation_result(plan_generation_result_file, data_dir, save_dir)
    retry_times = 10
    grounded_deciding(plan_generation_result_file, data_dir, save_dir, retry_times=retry_times)


if __name__ == "__main__":
    main()
