# coding=utf-8
# Generating a DFA, without Shadowencoding.
import ahocorasick
import json
import math
from config import *
# from shadow_code_gen import getShadowCodeWithDFA
# from shadow_code_gen import getSCIDWithDFA

class DFAMatchEntriesSimpleGenerator():
    def __init__(self, pattern_expression, stride=1, table_id_list=[0]):
        # Init and configure the automaton
        self.stride = stride
        self.table_id_list = table_id_list
        self.pattern_list, self.policies = \
                self.parse_pattern_expression(pattern_expression)
        self.automaton = self.generate_automaton(self.pattern_list)
        # Gegerate dfa descriptor according to the automaton
        self.dfa = self.generate_dfa(self.automaton.dump())
        self.fulldfa = self.generate_fulldfa(self.automaton.dump())
        # self.shadow_code = getShadowCodeWithDFA(self.dfa)
        # self.ID_code = 
        # self.SC_ID_tuple = getSCIDWithDFA(self.dfa)
        self.default_code = self.dfa[4]
        # self.dfa = self.recode_dfa(self.dfa, self.shadow_code)
        # stride should always be 1, msdfa no use now
        self.msdfa = self.generate_multi_stride_dfa(self.dfa, self.stride)
        self.dfa_mat_entries = self.generate_dfa_mat_entries(self.msdfa)
        self.runtime_dfa_mat_entries = self.generate_runtime_dfa_mat_entries(
            self.dfa_mat_entries, self.table_id_list
        )
        self.runtime_policy_mat_entries = \
                self.generate_runtime_policy_mat_entries(self.policies)
        self.runtime_mat_entries = \
                self.runtime_dfa_mat_entries + self.runtime_policy_mat_entries
        self.runtime_mat_default_entries = \
                self.generate_runtime_mat_default_entries(self.table_id_list)

    def parse_pattern_expression(self, patrn_expr_str):
        pattern_num = 0
        pattern_list = []
        policies = []
        # Remove space in the pattern expression strng
        patrn_expr_str = patrn_expr_str.replace(' ', '')
        # Replace \| with unseen ASCII char
        patrn_expr_str = patrn_expr_str.replace('\|', '\b')
        for policy in patrn_expr_str.split('|'):
            # Restore \| with |
            policy = policy.replace('\b', '|')
            # Replace \* with unseen ASCII char
            policy = policy.replace('\*', '\b')
            policy_mask = list('*' * PATTERN_MAX_NUM)
            for pattern in policy.split('*'):
                # Restore \* with *
                pattern = pattern.replace('\b', '*')
                reverse_flag = False
                if pattern[0] == '~':
                    pattern = pattern[1:]
                    reverse_flag = True
                if pattern in pattern_list:
                    pattern_idx = pattern_list.index(pattern)
                else:
                    pattern_idx = pattern_num
                    pattern_list.append(pattern)
                    pattern_num += 1
                if reverse_flag:
                    policy_mask[pattern_idx] = '0'
                else:
                    policy_mask[pattern_idx] = '1'
            policy_mask = ''.join(policy_mask)
            policies.append(policy_mask)

        # pattern has been preprocess, the ' ' is  set as '\-'
        return_pattern_lst = []
        for pattern in pattern_list:
            temp_pattern = pattern.replace('\-', ' ')
            return_pattern_lst.append(temp_pattern)

        return return_pattern_lst, policies

    def generate_automaton(self, pattern_list):
        automaton = ahocorasick.Automaton(ahocorasick.STORE_LENGTH)
        for pattern in pattern_list:
            automaton.add_word(pattern)
        automaton.make_automaton()
        return automaton

    def generate_dfa(self, automaton_graph_descriptor):
        nodes = automaton_graph_descriptor[0]
        edges = automaton_graph_descriptor[1]
        failure_links = automaton_graph_descriptor[2]
        converse_dict = {}
        dfa_nodes = {}
        dfa_edges = []
        dfa_failure_links = []
        dfa_next_nodes = {}
        default_code = []
        pattern_idx = 0
        dfa_goto_function = {}
        dfa_failure_function = {}
        for node_id in range(len(nodes)):
            origin_node_id = nodes[node_id][0]
            converse_dict[origin_node_id] = node_id
            accept_flag = nodes[node_id][1]
            if accept_flag == 1:
                pattern_idx += 1
                accept_flag = pattern_idx
            dfa_nodes[node_id] = accept_flag
            dfa_next_nodes[node_id] = []
            dfa_goto_function[node_id] = {}
        for edge in edges:
            start_node_id = converse_dict[edge[0]]
            transfer_char = edge[1]
            end_node_id = converse_dict[edge[2]]
            # dfa_edges.append(
                # (start_node_id, transfer_char, end_node_id, 1)
            # )
            dfa_next_nodes[start_node_id].append(
                (transfer_char, end_node_id)
            )
            dfa_goto_function[start_node_id][transfer_char] = end_node_id
        for failure_link in failure_links:
            start_node_id = converse_dict[failure_link[0]]
            intermediate_node_id = converse_dict[failure_link[1]]
            dfa_failure_links.append((start_node_id, intermediate_node_id))
            dfa_failure_function[start_node_id] = intermediate_node_id
        for node in dfa_nodes:
            for i in range(256):
                c = chr(i)
                if c in dfa_goto_function[node].keys():
                    dfa_edges.append(
                        (node, c, dfa_goto_function[node][c], 1)
                    )
                else:
                    if node == 0:
                        continue
                    else:
                        current_node = node
                        while True:
                            next_node = dfa_failure_function[current_node]
                            if c in dfa_goto_function[next_node].keys():
                                dfa_edges.append(
                                    (node, c, dfa_goto_function[next_node][c], 0)
                                )
                                break
                            elif next_node == 0:
                                break
                            current_node = next_node
        bit_width = math.ceil(math.log(len(dfa_nodes), 2))
        for dfa_node_id in dfa_nodes:
            str1 = bin(dfa_node_id).replace('0b','')
            str1 = str1.zfill(int(bit_width))
            # print str1
            default_code.append(str1)
        return (
            dfa_nodes, dfa_edges, dfa_failure_links, \
            dfa_next_nodes, default_code
        )
        '''
        dfa_nodes {0: 0, 1: 0, 2: 1, 3: 0, 4: 2}  key: nodeID, value: accepting_flag
        '''

    def generate_fulldfa(self, automaton_graph_descriptor):
        nodes = automaton_graph_descriptor[0]
        edges = automaton_graph_descriptor[1]
        failure_links = automaton_graph_descriptor[2]
        converse_dict = {}
        dfa_nodes = {}
        dfa_edges = []
        dfa_failure_links = []
        dfa_next_nodes = {}
        default_code = []
        pattern_idx = 0
        dfa_goto_function = {}
        dfa_failure_function = {}
        for node_id in range(len(nodes)):
            origin_node_id = nodes[node_id][0]
            converse_dict[origin_node_id] = node_id
            accept_flag = nodes[node_id][1]
            if accept_flag == 1:
                pattern_idx += 1
                accept_flag = pattern_idx
            dfa_nodes[node_id] = accept_flag
            dfa_next_nodes[node_id] = []
            dfa_goto_function[node_id] = {}
        for edge in edges:
            start_node_id = converse_dict[edge[0]]
            transfer_char = edge[1]
            end_node_id = converse_dict[edge[2]]
            # dfa_edges.append(
                # (start_node_id, transfer_char, end_node_id, 1)
            # )
            dfa_next_nodes[start_node_id].append(
                (transfer_char, end_node_id)
            )
            dfa_goto_function[start_node_id][transfer_char] = end_node_id
        for failure_link in failure_links:
            start_node_id = converse_dict[failure_link[0]]
            intermediate_node_id = converse_dict[failure_link[1]]
            dfa_failure_links.append((start_node_id, intermediate_node_id))
            dfa_failure_function[start_node_id] = intermediate_node_id
        for node in dfa_nodes:
            for i in range(256):
                c = chr(i)
                if c in dfa_goto_function[node].keys():
                    dfa_edges.append(
                        (node, c, dfa_goto_function[node][c], 1)
                    )
                else:
                    if node == 0:
                        dfa_edges.append(
                            (node, c, node, 0)
                        )
                        dfa_goto_function[node][c] = node
                    else:
                        current_node = node
                        while True:
                            next_node = dfa_failure_function[current_node]
                            if c in dfa_goto_function[next_node].keys():
                                dfa_edges.append(
                                    (node, c, dfa_goto_function[next_node][c], 0)
                                )
                                break
                            elif next_node == 0:
                                break
                            current_node = next_node
        bit_width = math.ceil(math.log(len(dfa_nodes), 2))
        for dfa_node_id in dfa_nodes:
            str1 = bin(dfa_node_id).replace('0b','')
            str1 = str1.zfill(int(bit_width))
            # print str1
            default_code.append(str1)
        return (
            dfa_nodes, dfa_edges, dfa_failure_links, \
            dfa_next_nodes, default_code
        )
        '''
        dfa_nodes {0: 0, 1: 0, 2: 1, 3: 0, 4: 2}  key: nodeID, value: accepting_flag
        '''
    def recode_dfa(self, dfa_descriptor, shadow_code):
        return (
            dfa_descriptor[0], dfa_descriptor[1], \
            dfa_descriptor[2], dfa_descriptor[3], shadow_code
        )

    def generate_multi_stride_dfa(self, dfa_descriptor, stride):
        dfa_nodes = dfa_descriptor[0]
        dfa_edges = dfa_descriptor[1]
        dfa_failure_links = dfa_descriptor[2]
        dfa_next_nodes = dfa_descriptor[3]
        shadow_code = dfa_descriptor[4]
        dfa_next_nodes_extend = {}
        msdfa_nodes = dfa_nodes
        msdfa_edges = []
        msdfa_next_nodes = {}
        for dfa_node_id in dfa_nodes:
            dfa_next_nodes_extend[dfa_node_id] = dfa_next_nodes[dfa_node_id][:]
            msdfa_next_nodes[dfa_node_id] = []
        # Extend single stride DFA first
        for (start_node_id, transfer_char, end_node_id, type) in dfa_edges:
            if start_node_id == 0 and type == 1:
                for star_num in range(1, stride):
                    transfer_chars = b'\xff' * star_num + transfer_char
                    dfa_next_nodes_extend[start_node_id].append(
                        (transfer_chars, end_node_id)
                    )
            if dfa_nodes[end_node_id] != 0 and type == 1:
                for star_num in range(1, stride):
                    transfer_chars = transfer_char + b'\xff' * star_num
                    dfa_next_nodes_extend[start_node_id].append(
                        (transfer_chars, end_node_id)
                    )
        # Get all transistion edges of multi-stride DFA
        for dfa_node in dfa_nodes:
            start_node_id = dfa_node
            self.find_multi_stride_edges(
                msdfa_edges, msdfa_next_nodes, dfa_next_nodes_extend, \
                start_node_id, b'', start_node_id, stride
            )
        # Process failure links finally
        for failure_link in dfa_failure_links:
            start_node_id = failure_link[0]
            # # Below condition statements indicate what we care about is 
            # # the input whether hit one of the patterns, not all patterns
            # if msdfa_next_nodes[start_node_id] != 0:
                # continue
            intermediate_node_id = failure_link[1]
            for next_node in msdfa_next_nodes[intermediate_node_id]:
                transfer_chars = next_node[0]
                end_node_id = next_node[1]
                cover_flag = False
                # Check whether this failure link endge is valid
                for origin_next_node in msdfa_next_nodes[start_node_id]:
                    existing_path = origin_next_node[0]
                    cover_flag = True
                    for idx in range(stride):
                        if transfer_chars[idx] != existing_path[idx] \
                           and ord(b'\xff') != existing_path[idx]:
                            cover_flag = False
                            break
                if not cover_flag:
                    msdfa_edges.append(
                        (start_node_id, transfer_chars, end_node_id, 0)
                    )
        return (msdfa_nodes, msdfa_edges, shadow_code)
       

    def find_multi_stride_edges(self, msdfa_edges, msdfa_next_nodes, \
                                dfa_next_nodes, start_node_id, \
                                current_path, current_node_id, stride):
        for next_node in dfa_next_nodes[current_node_id]:
            next_path = current_path + next_node[0]
            next_node_id = next_node[1]
            if len(next_path) < stride:
                self.find_multi_stride_edges(
                    msdfa_edges, msdfa_next_nodes, dfa_next_nodes, \
                    start_node_id, next_path, next_node_id, stride
                )
            elif len(next_path) == stride:
                transfer_chars = next_path
                end_node_id = next_node_id
                msdfa_edges.append(
                    (start_node_id, transfer_chars, end_node_id, 1)
                )
                msdfa_next_nodes[start_node_id].append(
                    (transfer_chars, end_node_id)
                )
            else:
                continue
    
    def generate_dfa_mat_entries(self, msdfa_descriptor):
        msdfa_nodes = msdfa_descriptor[0]
        msdfa_edges = msdfa_descriptor[1]
        shadow_code = msdfa_descriptor[2]
        mat_entries = []
        for (current_state, received_chars, next_state, type) in msdfa_edges:
            match = (shadow_code[current_state], received_chars)
            # if msdfa_nodes[next_state] != 0:
                # action = 'accept'
            # else:
                # action = 'goto'
            action = 'goto'
            modifier = 0
            if msdfa_nodes[next_state] != 0:
                modifier = 1 << (msdfa_nodes[next_state] - 1)
            action_params = (shadow_code[next_state], modifier)
            mat_entries.append((match, action, action_params))
        return mat_entries

    def generate_runtime_mat_default_entries(self, table_id_list):
        mat_default_entries = []
        stride_mat_default_entry = {}
        stride_mat_default_entry["table_name"] = \
                        SWITCH_CONFIG["stride_mat_name"]
        stride_mat_default_entry["default_action"]= True
        stride_mat_default_entry["action_name"]= \
                        SWITCH_CONFIG["stride_action_name"]
        stride_mat_default_entry["action_params"]= {
            SWITCH_CONFIG["stride_param"]: 1,
        }
        mat_default_entries.append(stride_mat_default_entry)
        for table_id in table_id_list:
            dfa_mat_default_entry = {}
            dfa_mat_default_entry["table_name"] = \
                    SWITCH_CONFIG["dfa_mat_name"] % table_id
            dfa_mat_default_entry["default_action"]= True
            dfa_mat_default_entry["action_name"]= \
                    SWITCH_CONFIG["goto_action_name"] % self.stride
            dfa_mat_default_entry["action_params"]= {
                SWITCH_CONFIG["next_state"]: 0,
                SWITCH_CONFIG["modifier"]: 0,
            }
            mat_default_entries.append(dfa_mat_default_entry)
        policy_mat_default_entry = {}
        policy_mat_default_entry["table_name"] = \
                        SWITCH_CONFIG["policy_mat_name"]
        policy_mat_default_entry["default_action"]= True
        policy_mat_default_entry["action_name"]= \
                        SWITCH_CONFIG["drop_action_name"]
        policy_mat_default_entry["action_params"]= {
        }
        mat_default_entries.append(policy_mat_default_entry)
        return mat_default_entries

    def generate_runtime_dfa_mat_entries(self, mat_entries, table_id_list):
        runtime_mat_entries = []
        for table_id in table_id_list:
            for (match, action, action_params) in mat_entries:
                runtime_mat_entry = {}
                runtime_mat_entry["table_name"] = \
                        SWITCH_CONFIG["dfa_mat_name"] % table_id
                runtime_mat_entry["match"] = {
                    SWITCH_CONFIG["current_state"]: match[0]
                }
                for idx in range(len(match[1])):
                    received_char = match[1][idx]
                    # Follow systement is for difference 
                    # between python2 and python3
                    if type(received_char) != int:
                        received_char = ord(match[1][idx])
                    if ord(b'\xff') != received_char:
                        field_name = SWITCH_CONFIG["received_char"] % idx
                        runtime_mat_entry["match"][field_name] \
                                = [received_char, 255]
                if action == "goto":
                    runtime_mat_entry["action_name"] = \
                            SWITCH_CONFIG["goto_action_name"] % self.stride
                    runtime_mat_entry["action_params"] = {
                        SWITCH_CONFIG["next_state"]: action_params[0],
                        SWITCH_CONFIG["modifier"]: action_params[1],
                    }
                # elif action == "accept":
                    # runtime_mat_entry["action_name"] = \
                            # SWITCH_CONFIG["accept_action_name"]
                    # runtime_mat_entry["action_params"] = {
                        # SWITCH_CONFIG["next_state"]: action_params[0],
                    # }
                runtime_mat_entries.append(runtime_mat_entry)
        return runtime_mat_entries

    def generate_runtime_policy_mat_entries(self, policies):
        runtime_mat_entries = []
        for policy_mask in policies:
            match_field = 0
            match_mask = 0
            for pattern_bit in reversed(policy_mask):
                if pattern_bit == '0':
                    match_field = (match_field << 1) + 0
                    match_mask = (match_mask << 1) + 1
                elif pattern_bit == '1':
                    match_field = (match_field << 1) + 1
                    match_mask = (match_mask << 1) + 1
                else:
                    match_field = (match_field << 1) + 0
                    match_mask = (match_mask << 1) + 0
            runtime_mat_entry = {}
            runtime_mat_entry["table_name"] = SWITCH_CONFIG["policy_mat_name"]
            runtime_mat_entry["match"] = {
                SWITCH_CONFIG["pattern_state"]: [match_field, match_mask]
            }
            runtime_mat_entry["action_name"] = SWITCH_CONFIG["policy_action_name"]
            runtime_mat_entry["action_params"] = {}
            runtime_mat_entries.append(runtime_mat_entry)
        return runtime_mat_entries

    def get_pattern_list(self):
        return self.pattern_list

    def get_policies(self):
        return self.policies

    def get_automaton(self):
        return self.automaton

    def get_dfa(self):
        return self.dfa

    def get_multi_stride_dfa(self):
        return self.msdfa

    def get_dfa_mat_entries(self):
        return self.dfa_mat_entries

    def get_runtime_dfa_mat_entries(self):
        return self.runtime_dfa_mat_entries

    def get_runtime_policy_mat_entries(self):
        return self.runtime_policy_mat_entries

    def get_runtime_mat_entries(self):
        return self.runtime_mat_entries

    def get_runtime_mat_default_entries(self):
        return self.runtime_mat_default_entries

    def get_runtime_mat_entries_json(self):
        return json.dumps(
            self.runtime_mat_entries, indent=4, separators=(',', ': ')
        )

    def get_runtime_mat_default_entries_json(self):
        return json.dumps(
            self.runtime_mat_default_entries, indent=4, separators=(',', ': ')
        )

if __name__ == '__main__':
    x = DFAMatchEntriesSimpleGenerator("\|oo\-aa\| | ~his", 2)
    print("Full DFA")
    print("***************************************")
    print(len(x.fulldfa[1]))
    print("***************************************")
    print x.pattern_list
    print("***************************************")
    print x.policies
    exit(0)
    # x = DFAMatchEntriesSimpleGenerator("her | hers", 1)
    dfa = x.dfa
    msdfa = x.msdfa
    
    lst = []
    # for i in range(1, 4):
    #     x = DFAMatchEntriesSimpleGenerator("dog", i)
    #     lst.append(x.msdfa)
    # for i in lst:
    #     for j in i:
    #         print j
    #     print "*************"
    for i in dfa:
        print i
    print("*******************")
    for i in msdfa:
        print i
    # print("*******************")
    print len(x.get_dfa_mat_entries())
    for i in x.get_dfa_mat_entries():
        print(i)
    print("*******************")
    # for i in x.get_runtime_mat_entries():
    #     print(i)
    # print("*******************")
    # for i in x.get_runtime_mat_default_entries():
    #     print(i)
