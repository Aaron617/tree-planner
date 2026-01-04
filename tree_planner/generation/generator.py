# Wrapped OpenAI Generator
import json
from typing import Dict, List, Union, Tuple
import openai
import time
import random
# from generation.prompt import PromptBuilder


class Generator(object):
    """
    Codex generation wrapper.
    """

    def __init__(self, args, keys=None, tokenizer=None):
        self.args = args
        self.keys = keys
        self.current_key_id = 0
        self.tokenizer = tokenizer

        # if the args provided, will initialize with the prompt builder for full usage
        # self.prompt_builder = PromptBuilder(args) if args else None


    def generate_one_pass(
            self,
            prompts: List[Tuple],
            verbose: bool = False
    ):
        """
        Generate one pass with codex according to the generation phase.
        """
        result_idx_to_eid = []
        assert len(prompts) == 1  # @mengkang assume only one prompt
        for p in prompts:
            result_idx_to_eid.extend([p[0]] * self.args.sampling_n)
        prompts = [p[1] for p in prompts]
        engine = self.args.engine
        completion_list = ['text-davinci-003']
        if engine in completion_list:
            result = self._call_codex_api(
                engine=self.args.engine,
                prompt=prompts,
                max_tokens=self.args.max_generation_tokens,
                temperature=self.args.temperature,
                top_p=self.args.top_p,
                n=self.args.sampling_n,
                stop=self.args.stop_tokens
            )
        else:
            result = self._call_chat_api(
                engine=self.args.engine,
                prompt=prompts,
                max_tokens=self.args.max_generation_tokens,
                temperature=self.args.temperature,
                top_p=self.args.top_p,
                n=self.args.sampling_n,
                stop=self.args.stop_tokens
            )
        if verbose:
            print('\n', '*' * 20, 'Codex API Call', '*' * 20)
            for prompt in prompts:
                print(prompt)
                print('\n')
            print('- - - - - - - - - - ->>')

        # parse api results
        response_dict = dict()
        usage = result['usage']
        for idx, g in enumerate(result['choices']):
            try:
                text = g['text'] if engine in completion_list else g['message']['content']
                # text = g['text']
                # logprob = sum(g['logprobs']['token_logprobs'])
                eid = result_idx_to_eid[idx]
                eid_pairs = response_dict.get(eid, None)
                if eid_pairs is None:
                    eid_pairs = []
                    response_dict[eid] = eid_pairs
                # eid_pairs.append((text, logprob))
                eid_pairs.append((text, g['logprobs'] if engine in completion_list else 0))

                if verbose:
                    print(text)

            except ValueError as e:
                if verbose:
                    print('----------- Error Msg--------')
                    print(e)
                    print(text)
                    print('-----------------------------')
                pass

        return response_dict, usage

    def _call_codex_api(
            self,
            engine: str,
            prompt: Union[str, List],
            max_tokens,
            temperature: float,
            top_p: float,
            n: int,
            stop: List[str]
    ):
        start_time = time.time()
        result = None
        MAX_N_SAMPLING = 1000  # @mengkang adjust the parameter if needed
        count = n
        while count > 0:
            try:
                key = self.keys[self.current_key_id]
                # self.current_key_id = (self.current_key_id + 1) % len(self.keys)
                cur_sample = min(count, MAX_N_SAMPLING)
                print(f"Using openai api key: {key}, Sampling {cur_sample}, Left {count}")
                cur_result = openai.Completion.create(
                    engine=engine,
                    prompt=prompt,
                    api_key=key,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    n=cur_sample,
                    stop=stop,
                    # remove the stop tokens. If removed, post-process of generation result is needed
                    logprobs=1
                )
                count -= cur_sample
                if result is None:
                    result = cur_result
                else:
                    # result['choices'].append(cur_result['choices'])
                    result['choices'] += cur_result['choices']
                print('Openai api inference time:', time.time() - start_time)
            except Exception as e:
                print(e, 'Retry.')
                self.current_key_id = (self.current_key_id + 1) % len(self.keys)
                time.sleep(5)
        return result


    def _call_chat_api(
            self,
            engine: str,
            prompt: Union[str, List],
            max_tokens,
            temperature: float,
            top_p: float,
            n: int,
            stop: List[str]
    ):
        start_time = time.time()
        result = None
        MAX_N_SAMPLING = 1000  # FIXME @mengkang 这里的sampling num是一个可以自己调整的超参数，即每次生成采样的次数
        count = n
        prompt = prompt[0]
        max_retry_times, retry_cnt = 5, 0
        while count > 0:
            try:
                key = self.keys[self.current_key_id]
                self.current_key_id = (self.current_key_id + 1) % len(self.keys)
                cur_sample = min(count, MAX_N_SAMPLING)
                print(f"Using openai api key: {key}, Sampling {cur_sample}, Left {count}")
                cur_result = openai.ChatCompletion.create(
                    model=engine,
                    messages=[{'role':'user', 'content':prompt}],
                    api_key=key,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    n=cur_sample,
                    stop=stop,
                    # FIXME : remove the stop tokens
                    # logprobs=1
                )
                count -= cur_sample
                if result is None:
                    result = cur_result
                else:
                    # result['choices'].append(cur_result['choices'])
                    result['choices'] += cur_result['choices']
                print('Openai api inference time:', time.time() - start_time)
            except Exception as e:
                print(e, 'Retry.')
                # retry_cnt += 1
                # if retry_cnt == max_retry_times:
                #     result = {'choices':[{'message':{'content': ''}}], 'usage':0}
                #     break
                time.sleep(1)
        return result