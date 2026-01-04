import argparse


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--task_to_graph', type=str)

    # Error Correction
    parser.add_argument('--retry_times', type=int, default=0)   # if 0, do not do error correction

    # Few shot experiment Setting
    parser.add_argument('--n_shots', type=int, default=1)
    parser.add_argument('--instruction', action='store_true')

    # Grounded Deciding
    parser.add_argument('--grounded_deciding_prompt_path', type=str)
    parser.add_argument('--grounded_deciding_result_file', type=str, default='default_gd.json')
    parser.add_argument('--prompt_choices_sequence', action='store_true')

    # File path or name
    parser.add_argument('--dataset_split', type=str, default='validation', choices=['train', 'validation', 'test'])
    parser.add_argument('--dataset', type=str, default='./data/val.json')
    parser.add_argument('--retrieval_dataset', type=str, default='./data/train.json')
    parser.add_argument('--example_idx_file', type=str, default=None)
    parser.add_argument('--api_keys_file', type=str, default='key.txt')
    parser.add_argument('--save_dir', type=str, default='results/')
    parser.add_argument('--plan_generation_result_file', type=str, default='default_pg.json')
    parser.add_argument('--processed_plan_generation_result_file', type=str, default=None)
    parser.add_argument('--graph_dict_path', type=str)
    parser.add_argument('--plan_generation_prompt_path', type=str)


    # Multiprocess options
    parser.add_argument('--n_processes', type=int, default=1)

    parser.add_argument('--seed', type=int, default=42)

    # Codex options
    parser.add_argument('--engine', type=str, default="text-davinci-003")
    parser.add_argument('--n_parallel_prompts', type=int, default=1)    # this is an parameter of openai api. we assert this to 1 during our experiment.
    parser.add_argument('--max_generation_tokens', type=int, default=512)
    parser.add_argument('--max_api_total_tokens', type=int, default=4096)
    parser.add_argument('--temperature', type=float, default=0.4)
    parser.add_argument('--sampling_n', type=int, default=20)
    parser.add_argument('--top_p', type=float, default=1.0)
    parser.add_argument('--stop_tokens', type=str, default='\n\n',    # @mengkang for plan generation
                        help='Split stop tokens by ||')
    # Do not use any stop_tokens, parse result in postprocess (code generation)
    # parser.add_argument('--stop_tokens', type=str, default=None,
    #                     help='Split stop tokens by ||')

    # debug options
    parser.add_argument('-v', '--verbose', action='store_true')


    args = parser.parse_args()
    args.stop_tokens = args.stop_tokens.split('||')
    print("Args info:")
    for k in args.__dict__:
        print(k + ": " + str(args.__dict__[k]))
    return args