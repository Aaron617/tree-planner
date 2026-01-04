"""
Custom graph_dict_helper for Tree-Planner.

This module extends VirtualHome's graph_dict_helper with custom mapping logic.
"""
try:
    from virtualhome.simulation.evolving_graph.utils import graph_dict_helper
except ImportError:
    from simulation.evolving_graph.utils import graph_dict_helper

import copy
import random
random.seed(2)


class custom_graph_dict_helper(graph_dict_helper):
    def __init__(self, properties_data=None, object_placing=None, object_states=None, max_nodes=300):
        super(custom_graph_dict_helper, self).__init__(properties_data=properties_data, object_placing=object_placing, object_states=object_states, max_nodes=max_nodes)

    def mapping(self, script, graph_dict, id_mapping):
        equivalent_rooms = self.equivalent_rooms
        possible_rooms = self.possible_rooms

        available_rooms_in_graph = [i['class_name'] for i in filter(lambda v: v["category"] == 'Rooms', graph_dict['nodes'])]
        # print(available_rooms_in_graph)
        available_rooms_in_graph_id = [i['id'] for i in filter(lambda v: v["category"] == 'Rooms', graph_dict['nodes'])]

        available_nodes = copy.deepcopy(graph_dict['nodes'])
        available_name = list(set([node['class_name'] for node in available_nodes]))
        room_mapping = {k:k for k in available_rooms_in_graph}

        # apply room mapping to the script
        for script_line in script:
            for parameter in script_line.parameters:
                if parameter.name in possible_rooms:
                    parameter.name = room_mapping[parameter.name]

        # initialize the `objects_in_script`
        objects_in_script = {}
        time_step_to_objects_in_script = {}  # time_step -> object in script
        character_id = [i for i in filter(lambda v: v['class_name'] == 'character', graph_dict["nodes"])][0]["id"]
        key = ('character', 1)
        objects_in_script[key] = id_mapping[key] if key in id_mapping else character_id
        id_to_class_name = {n['id']:n['class_name'] for n in graph_dict['nodes']}
        first_room = [id_to_class_name[edge['to_id']] for edge in filter(lambda x: x['from_id'] == character_id and x['relation_type'] == 'INSIDE',graph_dict['edges'])]
        first_room = first_room[0]
        for idx, script_line in enumerate(script):
            time_step_to_objects_in_script[idx] = {}
            for parameter in script_line.parameters:
                key = (parameter.name, parameter.instance)
                if key not in objects_in_script:
                    time_step_to_objects_in_script[idx][key] = id_mapping[key] if key in id_mapping else None
                    objects_in_script[key] = time_step_to_objects_in_script[idx][key]
        time_step_to_room = {}  # time step -> character at which room
        cur_room = first_room
        for idx, script_line in enumerate(script):
            for parameter in script_line.parameters:
                if parameter.name in available_rooms_in_graph:
                    cur_room = parameter.name
                    break
            time_step_to_room[idx] = cur_room

        # set up the first room
        #location_precond = {tuple(i['location'][0]): i['location'][1][0] for i in filter(lambda v: 'location' in v, precond)}
        # location_precond = {(i['location'][0][0], int(i['location'][0][1])): i['location'][1][0] for i in filter(lambda v: 'location' in v, precond)}
        # rooms_in_precond = list(set([i for i in location_precond.values()]))
        # print(first_room)
        # if first_room == None:
        #     assert len(rooms_in_precond) == 0
        #     first_room = self._random_pick_a_room_with_objects_name_in_graph(available_rooms_in_graph, available_rooms_in_graph_id, objects_in_script, available_nodes, graph_dict)
        # else:
        #     first_room = self._any_room_except(first_room, available_rooms_in_graph)
        # assert first_room is not None and first_room in available_rooms_in_graph
        # print(first_room)
        # mapping objects
        for idx in range(len(script)):
            cur_objects_in_script = time_step_to_objects_in_script[idx]
            cur_room_obj = time_step_to_room[idx]
            cur_room_id = [i["id"] for i in filter(lambda v: v['class_name'] == cur_room_obj, graph_dict["nodes"])][0]
            for obj in cur_objects_in_script.keys():
                # objects that are specified already
                if objects_in_script[obj] is not None:
                    continue
                # if obj[0] in possible_rooms:    # object name is a room, directly assign
                if obj[0] in available_rooms_in_graph:
                    id_to_be_assigned = [i["id"] for i in filter(lambda v: v["class_name"] == obj[0], graph_dict["nodes"])]
                    objects_in_script[obj] = id_to_be_assigned[0]
                elif obj[0] in available_name:  # 环境中有的object
                    # 所有可以match的node
                    possible_matched_nodes = [i for i in filter(lambda v: v['class_name'] == obj[0], available_nodes)]
                    possible_matched_nodes_ids = [n['id'] for n in possible_matched_nodes]
                    # 1. if the object exist in current room, assign directly
                    obj_in_room = [i['from_id'] for i in filter(lambda v: v['relation_type'] == 'INSIDE' and v['from_id'] in possible_matched_nodes_ids and v["to_id"] == cur_room_id, graph_dict["edges"])]
                    if len(obj_in_room) > 0:
                        node_id = random.choice(obj_in_room)
                    elif len(possible_matched_nodes_ids) > 0: # 2. if the object exist in another room, pick one randomly
                        node_id = random.choice(possible_matched_nodes_ids)
                    else:
                        raise Exception(f"{obj} does not exist in the environment")
                    objects_in_script[obj] = node_id
                    available_nodes.remove(list(filter(lambda x:x['id'] == node_id, available_nodes))[0])
                else:
                    raise Exception(f"{obj} does not exist in the environment")


        # change the id in script
        for script_line in script:
            for parameter in script_line.parameters:
                parameter.instance = objects_in_script[(parameter.name, parameter.instance)]
                # print((parameter.name, parameter.instance))

        return objects_in_script, first_room, room_mapping
