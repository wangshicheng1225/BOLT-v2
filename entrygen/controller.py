# coding=utf-8
# write entries to *.config file
from math import pi
import os
import sys
# from config import *
import json
from entries_generator_simple import DFAMatchEntriesSimpleGenerator
from entries_generator_shadow import NFAMatchEntriesShadowGenerator
from config import SWITCH_BUCKET_CONFIG
import jsonio as jsio
# from entries_compress import compress_transition_sharing,shadow_code_transition_sharing
'''
- table_set_default <table name> <action name> <action parameters>
- table_add <table name> <action name> <match fields> => <action parameters> [priority]
- table_delete <table name> <entry handle>

- table_add t_ipv4_lpm a_ipv4_forward 10.0.0.10/32 => 00:04:00:00:00:00 1
- table_add t_ipv4_lpm a_ipv4_forward 10.0.1.10/32 => 00:04:00:00:00:01 2
'''




def writeRulesToConfig_from_mat_lst(ruleset, stride,table_id_list,filename=''):
    x = NFAMatchEntriesShadowGenerator(pattern_expression = ruleset, stride = stride, table_id_list=table_id_list)
    MAX_STRIDE = SWITCH_CONFIG['max_stride']
    root_state_ID = int(x.SC_ID_tuple[1][0],2)
    # print x.nfa_mat_entries

    # print x.nfa_shadow_mat_entries

    # print x.vstride_nfa_mat_entries
    # print "vstride_nfa_shadow_mat_entries"
    # print x.vstride_nfa_shadow_mat_entries
    # print "*********************************"
    policy_runtime_mat_entries = []
    # x.generate_runtime_mat_entries()
    runtime_nfa_shadow_mat_entries = x.get_runtime_nfa_shadow_mat_entries()
    runtime_policy_mat_entries = x.get_runtime_policy_mat_entries()
    runtime_mat_default_entries = x.get_runtime_mat_default_entries()
    
    max_priority = len(x.runtime_nfa_shadow_mat_entries) + 1
    cur_priority = max_priority
    entry_lst = []
    for entry_idx in runtime_nfa_shadow_mat_entries:
        # print entry_idx
        if entry_idx["table_name"][0:-1] == "t_DFA_match_":
            if entry_idx["action_name"][0:-1] == "a_set_state_":
                entry_str = 'table_add '+ entry_idx["table_name"] +' ' + entry_idx["action_name"] + ' '
                for idx in range(MAX_STRIDE):
                    field_name = SWITCH_CONFIG["received_char"] % idx
                    temp1 = str(entry_idx["match"][field_name][0])
                    temp2 = str(entry_idx["match"][field_name][1])
                    entry_str += temp1 + '&&&' + temp2 + ' '


                temp3 = str(entry_idx["match"]["meta.state"][0])
                temp4 = str(entry_idx["match"]["meta.state"][1])
                entry_str += temp3 + '&&&' + temp4 + ' => ' + str(entry_idx["action_params"]["_state"]) +' ' + str(entry_idx["action_params"]["modifier"]) + ' ' + str(cur_priority)
                cur_priority -=1
                print entry_str
                entry_lst.append(entry_str)
                # f.write("table_add", entry["table_name"], entry["action_name"], temp1+'&&&'+temp2,entry["match"]["meta.state"],"=>", entry["action_params"]["_state"], entry["action_params"]["modifier"])
                # print "table_add", entry["table_name"], entry["action_name"], temp1+'&&&'+temp2, temp3+'&&&'+temp4,"=>", entry["action_params"]["_state"], entry["action_params"]["modifier"],entry["priority"]
            # print "table_add", entry["table_name"], entry["action_name"], entry["match"]["hdr.patrns[0].string"],entry["match"]["meta.state"],"=>", entry["action_params"]["_state"], entry["action_params"]["modifier"]

    normal_priority = 1
    for entry_idx in runtime_policy_mat_entries:
        # print entry

        if entry_idx["table_name"] == "t_policy":
            entry_str = 'table_add ' + entry_idx["table_name"] +' ' + entry_idx["action_name"] + ' '
            temp1 = str(entry_idx["match"]["meta.pattern_state"][0])
            temp2 = str(entry_idx["match"]["meta.pattern_state"][1])
            entry_str += temp1+'&&&'+temp2 + ' => ' +  str(normal_priority)
            print entry_str
            entry_lst.append(entry_str)
            # print "table_add", entry_idx["table_name"], entry_idx["action_name"], temp1+'&&&'+temp2,"=>" , str(normal_priority)
                # f.write("table_add " + entry["table_name"] + ' '+ entry["action_name"] +' '+ entry["match"] + ' '+ "=>"+' '+entry["action_params"] )
    
    for entry_idx in runtime_mat_default_entries:
        # print entry
        if entry_idx["table_name"] == "t_get_stride":
            entry_str = 'table_set_default ' +  entry_idx["table_name"] + ' ' +entry_idx["action_name"] + ' ' + str(entry_idx["action_params"]["_stride"])
            
            # print "table_set_default", entry["table_name"], entry["action_name"], entry["action_params"]["_stride"]
        if entry_idx["table_name"] == "t_policy":
            entry_str = 'table_set_default ' +  entry_idx["table_name"] + ' ' +entry_idx["action_name"]
            
            # print "table_set_default", entry["table_name"], entry["action_name"]
            # print "table_set_default", entry["table_name"], entry["action_name"], entry["match"],"=>", entry["action_params"] 
        elif entry_idx["table_name"][0:-1] == "t_DFA_match_":
            entry_str = 'table_set_default ' +  entry_idx["table_name"] + ' ' +entry_idx["action_name"] + ' ' + str(entry_idx["action_params"]["_state"]) + ' ' + str(entry_idx["action_params"]["modifier"])
            
        print entry_str
        entry_lst.append(entry_str)
            #  print "table_set_default", entry["table_name"], entry["action_name"], entry["action_params"]["_state"], entry["action_params"]["modifier"]

    default_entry_lst = [ "table_set_default t_get_root_state a_get_root_state "+ str(root_state_ID), \
                        "table_add t_ipv4_lpm a_ipv4_forward 10.0.0.10/32 => 00:04:00:00:00:00 1",\
                        "table_add t_ipv4_lpm a_ipv4_forward 10.0.1.10/32 => 00:04:00:00:00:01 2"]
    
    for idx in default_entry_lst:
        entry_lst.append(idx)

    if filename == '':
        for idx in entry_lst:
            print idx
    else:
        with open(filename, 'w') as f:
            for idx in entry_lst:
                f.write(idx+'\n')

def writeBucketRulesToConfig_from_mat_lst(ruleset, stride,table_id_list,filename=''):

# TO REFACTOR: controller should readfrom the ruleset and pattern-bucket mapping to generate table entries.

    x = NFAMatchEntriesShadowGenerator(pattern_expression = ruleset, stride = stride, table_id_list=table_id_list)
    MAX_STRIDE = SWITCH_BUCKET_CONFIG['max_stride']
    root_state_ID = int(x.SC_ID_tuple[1][0],2)

    print(x.nfa)
    print(x.nfa_mat_entries)

    print(x.nfa_shadow_mat_entries)

    # print x.vstride_nfa_mat_entries
    # print "vstride_nfa_shadow_mat_entries"
    # print x.vstride_nfa_shadow_mat_entries
    # print "*********************************"
    policy_runtime_mat_entries = []
    # x.generate_runtime_mat_entries()
    runtime_nfa_shadow_mat_entries = x.pattern2rule_table.gen_runtime_var_stride_shadow_mat_lst(table_id_list)
    kwargs_1 = {"root_state":root_state_ID}
    runtime_default_entries = x.pattern2rule_table.gen_runtime_default_entries(table_id_list, root_state = root_state_ID, max_stride = stride)
    '''
    {   "action_params": {"_state": 3, "pattern_code": 1},
        "table_name": "t_DFA_match_0", 
        "match": {"hdr.patrns[0].string": [104, 255], "hdr.patrns[1].string": [101, 255], 
        "meta.state": [6, 6]},
    "action_name": "a_set_state_2_b1"},
    '''
    pipeline_name = "MyIngress"
    s1_runtime_config = {}
    s1_runtime_config["target"] = "bmv2"
    s1_runtime_config["p4info"] = "build/bolt.p4.p4info.txt"
    s1_runtime_config["bmv2_json"] = "build/bolt.json"
    s1_runtime_config["table_entries"] = []
    max_priority = len(runtime_nfa_shadow_mat_entries) + 1
    cur_priority = max_priority
    entry_lst = []

    print("runtime nfa shadow mat entries")
    for entry_idx in runtime_nfa_shadow_mat_entries:
        print(entry_idx)
        entry = {}
        entry["table"] = pipeline_name + "." + entry_idx["table"]
        entry["match"] = {key:value for key,value in entry_idx["match"].items() if value[1] != 0} 
        # for key,value in entry_idx.items(): 
        #     # check if mask = 0, omit this field
        #     if value[1] != 0:
        #         entry["match"][key] = value
        entry["action_name"] = pipeline_name + "." + entry_idx["action_name"]
        entry["action_params"] = entry_idx["action_params"]
        entry["priority"] = cur_priority
        cur_priority -= 1
        '''
        {
        "table": "MyIngress.ipv4_lpm",
        "match": {
          "hdr.ipv4.dstAddr": ["10.0.1.1", 32]
        },
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {
          "dstAddr": "08:00:00:00:01:11",
          "port": 1
        }
      },
        '''
        s1_runtime_config["table_entries"].append(entry)
    '''
    # print entry
        if entry_idx["table_name"] == "t_get_stride":
            entry_str = 'table_set_default ' +  entry_idx["table_name"] + ' ' +entry_idx["action_name"] + ' ' + str(entry_idx["action_params"]["_stride"])
            
            # print "table_set_default", entry["table_name"], entry["action_name"], entry["action_params"]["_stride"]
        if entry_idx["table_name"] == "t_policy":
            entry_str = 'table_set_default ' +  entry_idx["table_name"] + ' ' +entry_idx["action_name"]
            
            # print "table_set_default", entry["table_name"], entry["action_name"]
            # print "table_set_default", entry["table_name"], entry["action_name"], entry["match"],"=>", entry["action_params"] 
        elif entry_idx["table_name"][0:-1] == "t_DFA_match_":
            entry_str = 'table_set_default ' +  entry_idx["table_name"] + ' ' +entry_idx["action_name"] + ' ' + str(entry_idx["action_params"]["_state"]) + ' ' + str(entry_idx["action_params"]["modifier"])
            
    '''
    # Default entry 
    # for 
    # entry = {}
    # entry["table"] = "ingress." + entry_idx["table_name"]
    # entry["match"] = entry_idx["match"]
    # # for key,value in entry_idx.items():
    # #     entry["match"][key] = value
    # entry["action_name"] = "ingress." + entry_idx["action_name"]
    # entry["action_params"] = entry_idx["action_params"]
    # entry["priority"] = cur_priority
    # cur_priority = 1
    print("default entries")
    for entry_idx in runtime_default_entries:
        print(entry_idx)
        entry = {}
        entry["table"] = pipeline_name + "." + entry_idx["table"]
        entry["default_action"] = entry_idx["default_action"]
        entry["action_name"] = pipeline_name + "." + entry_idx["action_name"]
        entry["action_params"] = entry_idx["action_params"]
        # entry["priority"] = cur_priority
        s1_runtime_config["table_entries"].append(entry)
    
    rule_table_entry = {}
    rule_table_entry["table"] = pipeline_name + "." + SWITCH_BUCKET_CONFIG["rule_mat_name"]
    rule_table_entry["match"] = {
        "meta.b1": [1,255],
        "meta.b2": [2,255]
    }
    rule_table_entry["action_name"] = pipeline_name + "." + "a_mark_as_to_forward"
    rule_table_entry["action_params"] = {}
    rule_table_entry["priority"] = 2

    s1_runtime_config["table_entries"].append(rule_table_entry)
    # default_rule_table_entry = {}
    # rule_table_entry["table"] = pipeline_name + "." + SWITCH_BUCKET_CONFIG["rule_mat_name"]
    # rule_table_entry["match"] = {
    #     "meta.b1": [1,255],
    #     "meta.b2": [2,255]
    # }
    # rule_table_entry["action_name"] = pipeline_name + "." + "a_mark_as_to_forward"
    # rule_table_entry["action_params"] = {}
    # rule_table_entry["priority"] = 2

    jsio.store(s1_runtime_config)

    with open("test-runtime.json", 'a') as outfile:
        json.dump(s1_runtime_config, outfile, indent=2)
    # with open(, 'w') as fw:
        # json_str = json.dumps(data)
        # fw.write(json_str)
        # 
        
    return 
    runtime_nfa_shadow_mat_entries = x.get_runtime_nfa_shadow_mat_entries()
    runtime_policy_mat_entries = x.get_runtime_policy_mat_entries()
    runtime_mat_default_entries = x.get_runtime_mat_default_entries()
    
    max_priority = len(x.runtime_nfa_shadow_mat_entries) + 1
    cur_priority = max_priority
    entry_lst = []

    print("runtime nfa shadow mat entries: ")
    for entry_idx in runtime_nfa_shadow_mat_entries:
        # print entry_idx
        if entry_idx["table_name"][0:-1] == "t_DFA_match_":
            if entry_idx["action_name"][0:-1] == "a_set_state_":
                entry_str = 'table_add '+ entry_idx["table_name"] +' ' + entry_idx["action_name"] + ' '
                for idx in range(MAX_STRIDE):
                    field_name = SWITCH_CONFIG["received_char"] % idx
                    temp1 = str(entry_idx["match"][field_name][0])
                    temp2 = str(entry_idx["match"][field_name][1])
                    entry_str += temp1 + '&&&' + temp2 + ' '


                temp3 = str(entry_idx["match"]["meta.state"][0])
                temp4 = str(entry_idx["match"]["meta.state"][1])
                entry_str += temp3 + '&&&' + temp4 + ' => ' + str(entry_idx["action_params"]["_state"]) +' ' + str(entry_idx["action_params"]["modifier"]) + ' ' + str(cur_priority)
                cur_priority -=1
                print entry_str
                entry_lst.append(entry_str)
                # f.write("table_add", entry["table_name"], entry["action_name"], temp1+'&&&'+temp2,entry["match"]["meta.state"],"=>", entry["action_params"]["_state"], entry["action_params"]["modifier"])
                # print "table_add", entry["table_name"], entry["action_name"], temp1+'&&&'+temp2, temp3+'&&&'+temp4,"=>", entry["action_params"]["_state"], entry["action_params"]["modifier"],entry["priority"]
            # print "table_add", entry["table_name"], entry["action_name"], entry["match"]["hdr.patrns[0].string"],entry["match"]["meta.state"],"=>", entry["action_params"]["_state"], entry["action_params"]["modifier"]

    normal_priority = 1

    print("runtime_policy_mat_entries ")
    for entry_idx in runtime_policy_mat_entries:
        # print entry

        if entry_idx["table_name"] == "t_policy":
            entry_str = 'table_add ' + entry_idx["table_name"] +' ' + entry_idx["action_name"] + ' '
            temp1 = str(entry_idx["match"]["meta.pattern_state"][0])
            temp2 = str(entry_idx["match"]["meta.pattern_state"][1])
            entry_str += temp1+'&&&'+temp2 + ' => ' +  str(normal_priority)
            print entry_str
            entry_lst.append(entry_str)
            # print "table_add", entry_idx["table_name"], entry_idx["action_name"], temp1+'&&&'+temp2,"=>" , str(normal_priority)
                # f.write("table_add " + entry["table_name"] + ' '+ entry["action_name"] +' '+ entry["match"] + ' '+ "=>"+' '+entry["action_params"] )
    
    print("runtime_mat_default_entries ")
    for entry_idx in runtime_mat_default_entries:
        # print entry
        if entry_idx["table_name"] == "t_get_stride":
            entry_str = 'table_set_default ' +  entry_idx["table_name"] + ' ' +entry_idx["action_name"] + ' ' + str(entry_idx["action_params"]["_stride"])
            
            # print "table_set_default", entry["table_name"], entry["action_name"], entry["action_params"]["_stride"]
        if entry_idx["table_name"] == "t_policy":
            entry_str = 'table_set_default ' +  entry_idx["table_name"] + ' ' +entry_idx["action_name"]
            
            # print "table_set_default", entry["table_name"], entry["action_name"]
            # print "table_set_default", entry["table_name"], entry["action_name"], entry["match"],"=>", entry["action_params"] 
        elif entry_idx["table_name"][0:-1] == "t_DFA_match_":
            entry_str = 'table_set_default ' +  entry_idx["table_name"] + ' ' +entry_idx["action_name"] + ' ' + str(entry_idx["action_params"]["_state"]) + ' ' + str(entry_idx["action_params"]["modifier"])
            
        print entry_str
        entry_lst.append(entry_str)
            #  print "table_set_default", entry["table_name"], entry["action_name"], entry["action_params"]["_state"], entry["action_params"]["modifier"]

    default_entry_lst = [ "table_set_default t_get_root_state a_get_root_state "+ str(root_state_ID), \
                        "table_add t_ipv4_lpm a_ipv4_forward 10.0.0.10/32 => 00:04:00:00:00:00 1",\
                        "table_add t_ipv4_lpm a_ipv4_forward 10.0.1.10/32 => 00:04:00:00:00:01 2"]
    
    print("default_entry_lst ")
    for idx in default_entry_lst:
        entry_lst.append(idx)

    if filename == '':
        for idx in entry_lst:
            print idx
    else:
        with open(filename, 'w') as f:
            for idx in entry_lst:
                f.write(idx+'\n')



if __name__ == '__main__':

    ruleset = "she | his"
    # writeRulesToConfig_from_mat_lst(ruleset,2,[0,1],filename='test.txt')  
    writeBucketRulesToConfig_from_mat_lst(ruleset,2,[0,1],filename='test.txt')  