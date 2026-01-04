import copy
from typing import List
import os

class Deciding_Node:
    def __init__(self, parent, action_str, idx_list, son_list:List, layer_id, node_color='white', edge_color='black'):
        self.parent = parent
        self.son_list = son_list
        self.action_str = action_str
        self.idx_list = idx_list
        self.layer_id = layer_id
        p = parent
        self.node_path = [self]
        while p != None:
            self.node_path.append(p)
            p = p.parent
        self.node_path.pop()
        self.node_path.reverse()
        self.node_color = node_color
        self.edge_color = edge_color
        self.reset()

    def reset(self):
        self.status = True
        # self.info = ''

    def identifier(self):
        res = '\n'.join([_.action_str for _ in self.node_path])
        return res

    def set_edge_color(self, color):
        self.edge_color = color

    def set_node_color(self, color):
        self.node_color = color

    def add_son(self, dn):
        self.son_list.append(dn)

    def add_sons(self, sons):
        self.son_list += sons

    def find_son_by_action(self, action, verbose=True):
        for son in self.son_list:
            if son.action_str == action:
                return son
        if verbose: print(f'{action} not found')

    def modify_status(self):
        self.status = False
        # self.info

    def get_choices(self):
        return [_.action_str for _ in self.son_list]

    def get_valid_choices(self):
        return [_.action_str for _ in filter(lambda x:x.status, self.son_list)]

    def get_valid_choices_sequence(self):   # TODO sequence implementation version (w/o beamsearch window size)
        sub_son_list = list(filter(lambda x:x.status, self.son_list))
        res = []
        for son in sub_son_list:
            cur_seq = [son.action_str]
            node = son
            while len(node.son_list) == 1:
                node = node.son_list[0]
                cur_seq.append(node.action_str)
            res.append(cur_seq)
        return res

    def get_valid_choices_beam(self, beam_num):   # TODO beam search
        sub_son_list = list(filter(lambda x:x.status, self.son_list))
        if len(sub_son_list) >= beam_num:
            return [[s.action_str] for s in sub_son_list]
        else:
            res = [([s.action_str], s) for s in sub_son_list]
            prev_res = res
            while len(res) < beam_num:
                new_res = []
                prev_res = res
                for action_str_list, node in res:
                    for son in node.son_list:
                        action_str_list.append(son.action_str)
                        new_res.append((action_str_list, son))
                res = new_res
            return [_[0] for _ in prev_res]


def construct_tree(root:Deciding_Node, script_str_list):
    if root.action_str == '[END]':
        return
    layer_id = root.layer_id
    idx_list = root.idx_list
    # sub_script_str_list = [script_str_list[idx] for idx in idx_list]
    cur_layer_id = layer_id+1
    # sub_action_list = [_[cur_layer_id] for _ in filter(lambda x:len(x)>cur_layer_id, sub_script_str_list)]
    action2idx = {}
    for idx in idx_list:
        # if len(script_str_list[idx]) <= cur_layer_id:   # [END]?
        #     continue
        # print(script_str_list[idx],  cur_layer_id)
        action_str = script_str_list[idx][cur_layer_id]
        if action_str not in action2idx:
            action2idx[action_str] = []
        action2idx[action_str].append(idx)
    sons = []
    for action, idx in action2idx.items():
        sons.append(Deciding_Node(parent=root, action_str=action, idx_list=idx, son_list=[], layer_id=cur_layer_id))
    root.add_sons(sons)
    for son in sons:
        construct_tree(son, script_str_list)


def print_tree(node: Deciding_Node, indent=0):
    print(" " * indent + node.action_str + " (Layer:{})".format(node.layer_id))
    for son in node.son_list:
        print_tree(son, indent + 4)


def visualize_tree(root_node: Deciding_Node):
    from graphviz import Digraph
    dot = Digraph()
    stack = [(root_node, None)]
    while len(stack) > 0:
        node, parent_name = stack.pop()
        parent = node.parent
        node_name = node.identifier()
        label = "{}\nLayer:{}".format(node.action_str, node.layer_id)
        dot.node(node_name, label=label, style="filled", fillcolor=node.node_color)
        if parent_name is not None:
            edge_color = node.edge_color
            dot.edge(parent_name, node_name, color=edge_color)
        for son in node.son_list:
            stack.append((son, node_name))

    return dot


class Deciding_Tree:
    def __init__(self, script_str_list, task):
        self.script_str_list = copy.deepcopy(script_str_list)
        self.task = task
        for _ in self.script_str_list:
            _.append('[END]')
        idx_list = list(range(len(self.script_str_list)))
        self.root = Deciding_Node(parent=None, action_str=task, idx_list=idx_list, son_list=[], layer_id=-1)
        construct_tree(self.root, self.script_str_list)
        self.deciding_point = self.root
        self.max_steps = max([len(_) for _ in self.script_str_list])

    def show(self):
        print_tree(self.root)

    def highlight_path(self, hp, color):
        node = self.root
        for action in hp + ['[END]']:
            node = node.find_son_by_action(action)
            node.set_edge_color(color)

    def viz(self, filename='tree', directory='../plot', view=False):
        dot = visualize_tree(self.root)
        dot.format = 'png'
        dot.render(filename=filename, directory=directory, view=view)

    def count_node(self):
        def count_num(root):
            return 1 + sum([count_num(son) for son in root.son_list])
        return count_num(self.root)

    def get_node_by_path(self, path:List[str]):
        p = copy.deepcopy(path)
        p.reverse()
        point_node = self.root
        while len(p) > 0:
            action_str = p.pop()
            point_node = point_node.find_son_by_action(action=action_str)
        return point_node

    def start_point(self):
        return self.root

    def average_branches_to_leaves(self):
        """
        Calculate the average number of branches needed to reach the leaves.
        """
        leaf_branch_counts = self._count_branches_in_leaves(self.root)
        total_branches = sum(leaf_branch_counts)
        number_of_leaves = len(leaf_branch_counts)
        return total_branches / number_of_leaves if number_of_leaves > 0 else 0

    def _count_branches_in_leaves(self, node, current_depth=0):
        """
        Recursively count the branches in the leaves.
        """
        if not node.son_list:  # Leaf node
            return [current_depth]
        else:
            counts = []
            for son in node.son_list:
                counts.extend(self._count_branches_in_leaves(son, current_depth + 1))
            return counts