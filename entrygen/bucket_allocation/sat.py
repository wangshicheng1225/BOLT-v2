# coding=utf-8
# please run in python3 
from math import log2
from z3 import *
import numpy as np
import jsonio as jsio

# TODO: the ruledata in json has a pattern lst may containing duplicated patterns,
# such as rule 1156
# the rules should be re-processed

def pre_process_ruleset(ruleset, bucket_num_limit = 8):
    _rule_set = {}
    drop_counter = 0
    i = 0
    for _sid, _pattern_lst in ruleset.items():
        # _rule_set[_sid] = list(set(_pattern_lst))
        _lst = list(set(_pattern_lst))
        if (len(_lst) > bucket_num_limit):
            drop_counter += 1
            continue
        _rule_set[i] = _lst
        i += 1
    print("drop overlimited rules: ", drop_counter)
    return _rule_set

def aggreate_pattern_set(ruleset):
    pattern_list = []
    for _sid, _pattern_lst in ruleset.items():
        # print(_sid, _pattern_lst)
        for pattern in _pattern_lst:
            if not (pattern in pattern_list):
                pattern_list.append(pattern)


    idx_to_pattern_dict = {}
    
    pattern_to_idx_dict = {}
    i = 0
    for pattern in pattern_list:
        idx_to_pattern_dict[i] = pattern
        pattern_to_idx_dict[pattern] = i
        i += 1
    return (idx_to_pattern_dict, pattern_to_idx_dict)
    
def parse_rule(ruleset):
    # return the lower limit of bucket_size
    bucket_num = 0
    for _sid, _pattern_lst in ruleset.items():
        if len(_pattern_lst) > bucket_num:
            bucket_num = len(_pattern_lst)
    return bucket_num
    

def generate_r0(pattern_set, bucket_num):
    clauses = ""
    return clauses

def generate_ri(pattern_set, bucket_num, ruleset):
    clauses = ""

    return clauses

def generate_solution_set(solution_matrix, pattern_set_size, bucket_num, _model):
    solution_set = set()
    for i in range(pattern_set_size):
        for j in range(bucket_num):
            # mat_ele = "x"+str(i)+str(j)
            if is_true(_model[solution_matrix[i][j]]) == True:
                solution_set.add(solution_matrix[i][j] == True)
            elif is_false(_model[solution_matrix[i][j]]):
                solution_set.add(solution_matrix[i][j] == False)
            else:
                pass

    return solution_set

def check_buckets_alloc(solution_matrix, pattern_set_size, bucket_num, 
            _model, idx_to_pattern_dict):
    print("check buckets_alloc ")
    for i in range(pattern_set_size):
        non_zero_counter = 0
        bucket_lst = []
        for j in range(bucket_num):
            if is_true(_model[solution_matrix[i][j]]) == True:
                non_zero_counter += 1
                bucket_lst.append(j)
        
        assert (non_zero_counter != 0), str(idx_to_pattern_dict[i]) + " in no bucket!"
        assert (non_zero_counter == 1), str(idx_to_pattern_dict[i]) + " in multiple bucket!" + str(bucket_lst)
    return True

def check_rules(solution_matrix, bucket_num, 
            ruleset, _model, pattern_to_idx_dict):
    print("check rules ")
    for _sid, _pattern_lst in ruleset.items():
        # print(_sid, _pattern_lst)
        bucket_dict = {}
        for pattern in _pattern_lst:
            i = pattern_to_idx_dict[pattern]
            for j in range(bucket_num):
                if is_true(_model[solution_matrix[i][j]]) == True:
                    assert not (j in bucket_dict.keys()), "rule " + str(_sid) + ": bucket " + str(j) +\
                        " has multiple patterns: "+ str(bucket_dict[j]) + " " + pattern
                    bucket_dict[j] = []
                    bucket_dict[j].append(pattern)
    return True           
def check_clauses(solution_matrix, pattern_set_size, bucket_num, ruleset, patternset,_model):
    # check if there is a pattern in no bucekt
    for i in range(pattern_set_size):
        non_zero_counter = 0
        for j in range(bucket_num):
            if is_true(_model[solution_matrix[i][j]]) == True:
                non_zero_counter += 1
        
        # assert (non_zero_counter != 0), str(idx_to_pattern_dict[i]) + " in no bucket!"
        # assert (non_zero_counter == 1), str(idx_to_pattern_dict[i]) + " in multiple bucket!"


    # check if there is a pattern in multiple bucket

    # check if there is a rule violated

    return False

def generate_mat_table_entries(solution_matrix, _model, pattern_to_idx_dict, bucket_num, ruleset):

    pattern_set_size = len(pattern_to_idx_dict)


    # generate pattern_to_binstr map
    # a = f'{s:0{l}b}'
    pattern_to_binstr_dict = {}
    bit_width = math.ceil(log2(pattern_set_size))
    for pattern, idx in pattern_to_idx_dict.items():
        binstr = f'{idx:0{bit_width}b}'
        pattern_to_binstr_dict[pattern] = binstr
    
    # generate pattern_to_bucket map
    pattern_to_bucket_dict = {}
    for pattern, idx in pattern_to_idx_dict.items():
        non_zero_counter = 0
        for j in range(bucket_num):
            if is_true(_model[solution_matrix[idx][j]]) == True:
                pattern_to_bucket_dict[pattern] = j
                
    print("pattern_to_binstr_dict: ", pattern_to_binstr_dict)
    print("pattern_to_bucket_dict: ", pattern_to_bucket_dict)
    mat_entry_lst = []
    # ( ['110','010','000'], 'sid')
    for _sid, pattern_lst in ruleset.items():
        bucket_dict = {}
        for pattern in pattern_lst:
           pattern_bin_str = pattern_to_binstr_dict[pattern]
           bucket_id = pattern_to_bucket_dict[pattern]
           bucket_dict[bucket_id] =  pattern_bin_str
        
        bucket_lst = []
        for i in range(bucket_num):
            if i in bucket_dict.keys():
                bucket_lst.append(bucket_dict[i])
            else:
                # bucket_lst.append(f'{0:0{bit_width}b}') # TODO: all zero or all * ??
                bucket_lst.append("*"*bit_width)
        entry = (bucket_lst, _sid)
        mat_entry_lst.append(entry)
    return mat_entry_lst


def allocate_bucket(rule_data, para_bucket_num = -1):
    # return pattern_to_bucket_dict

    idx_to_pattern_dict, pattern_to_idx_dict = aggreate_pattern_set(rule_data)
    print(idx_to_pattern_dict)
    print("*****************************")
    
    if para_bucket_num == -1:
        bucket_num = parse_rule(rule_data)
    else:
        bucket_num = para_bucket_num
    pattern_set_size = len(idx_to_pattern_dict)
    
    assert len(idx_to_pattern_dict) == len(pattern_to_idx_dict), \
        "not len(idx_to_pattern_dict) == len(pattern_to_idx_dict)"
    matx =  [[0 for j in range(bucket_num)] for i in range(pattern_set_size)]
    print("pattern_set_size: ", pattern_set_size)
    print("bucket_num: ", bucket_num)
    # print(matx[3][1])
    s = Solver()
    for i in range(pattern_set_size):
        for j in range(bucket_num):
            matx[i][j] =  Bool("x"+str(i)+'_'+str(j)) 
    # r0
    for i in range(pattern_set_size):
        clause_idx = Or([matx[i][ii] for ii in  range(bucket_num)])
        s.add(clause_idx)
        for j in range(bucket_num):
            for k in range(bucket_num):
                # clause_idx=Or()
                if k > j:
                    clause_idx = Or([Not(matx[i][j]), Not(matx[i][k])])
                    s.add(clause_idx)
    # print(s.check())
    # print(s.model())


    # ri

    for _sid, _pattern_lst in rule_data.items():
        pattern_idx_lst = [ pattern_to_idx_dict[pattern] for pattern in _pattern_lst ]
        for pattern_idx in pattern_idx_lst:
            for bucket_jdx in range(bucket_num):
                for pattern_kdx in pattern_idx_lst:
                    if pattern_kdx > pattern_idx:
                        clause_idx = Or( [ Not(matx[pattern_idx][bucket_jdx]), Not(matx[pattern_kdx][bucket_jdx])]) 
                        # print(clause_idx)
                        s.add(clause_idx)
    assert(s.check() == sat)
    print(s.check())
    print(s.model())
    
    check_buckets_alloc(solution_matrix = matx, pattern_set_size = pattern_set_size, bucket_num = bucket_num, 
            _model= s.model(), idx_to_pattern_dict = idx_to_pattern_dict)
    check_rules(solution_matrix = matx, bucket_num = bucket_num,
            ruleset = rule_data,  _model= s.model(), pattern_to_idx_dict = pattern_to_idx_dict)

    # generate pattern_to_bucket map
    pattern_to_bucket_dict = {}
    for pattern, idx in pattern_to_idx_dict.items():
        non_zero_counter = 0
        for j in range(bucket_num):
            if is_true(s.model()[matx[idx][j]]) == True:
                pattern_to_bucket_dict[pattern] = j
                
    # print("pattern_to_binstr_dict: ", pattern_to_binstr_dict)
    print("pattern_to_bucket_dict: ", pattern_to_bucket_dict)
    return pattern_to_bucket_dict, idx_to_pattern_dict, pattern_to_idx_dict, bucket_num
    
if __name__=='__main__':

    # rule_data = {
    #     1: ["p1","p2"],
    #     2: ["p3","p2"],
    #     3: ["p4","p5"]
    # }
    # rule_data = {
    #     1: ["p0","p1","p2"],
    #     2: ["p3","p4"],
    #     # 2: ["p3","p2"],
    #     # 3: ["p4","p5"]
    # }
    # rule_data = {
    #     "1": [], "105": ["2|00 00 00 06 00 00 00|Drives|24 00|"], "108": ["qazwsx.hsq"],
    # }

    # rule_data = {
    #     1: ["p1","p2"],
    #     2: ["p3","p2"],
    #     # 3: ["p1","p3"]
    # }
    raw_rule_data = jsio.load("snort297_ruleset.json")
    # raw_rule_data = jsio.load("suricata500_ruleset.json")

    rule_data = pre_process_ruleset(raw_rule_data, bucket_num_limit=100)
    # exit(0)
    print(rule_data)
    # exit(0)
    idx_to_pattern_dict, pattern_to_idx_dict = aggreate_pattern_set(rule_data)
    print(idx_to_pattern_dict)
    print("*****************************")
    
    bucket_num = parse_rule(rule_data)
    pattern_set_size = len(idx_to_pattern_dict)
    
    assert len(idx_to_pattern_dict) == len(pattern_to_idx_dict), \
        "not len(idx_to_pattern_dict) == len(pattern_to_idx_dict)"
    matx =  [[0 for j in range(bucket_num)] for i in range(pattern_set_size)]
    print("pattern_set_size: ", pattern_set_size)
    print("bucket_num: ", bucket_num)
    # print(matx[3][1])
    s = Solver()
    for i in range(pattern_set_size):
        for j in range(bucket_num):
            matx[i][j] =  Bool("x"+str(i)+'_'+str(j)) 
    # r0
    for i in range(pattern_set_size):
        clause_idx = Or([matx[i][ii] for ii in  range(bucket_num)])
        s.add(clause_idx)
        for j in range(bucket_num):
            for k in range(bucket_num):
                # clause_idx=Or()
                if k > j:
                    clause_idx = Or([Not(matx[i][j]), Not(matx[i][k])])
                    s.add(clause_idx)
    # print(s.check())
    # print(s.model())


    # ri

    for _sid, _pattern_lst in rule_data.items():
        pattern_idx_lst = [ pattern_to_idx_dict[pattern] for pattern in _pattern_lst ]
        for pattern_idx in pattern_idx_lst:
            for bucket_jdx in range(bucket_num):
                for pattern_kdx in pattern_idx_lst:
                    if pattern_kdx > pattern_idx:
                        clause_idx = Or( [ Not(matx[pattern_idx][bucket_jdx]), Not(matx[pattern_kdx][bucket_jdx])]) 
                        # print(clause_idx)
                        s.add(clause_idx)
    assert(s.check() == sat)
    print(s.check())
    print(s.model())
    
    check_buckets_alloc(solution_matrix = matx, pattern_set_size = pattern_set_size, bucket_num = bucket_num, 
            _model= s.model(), idx_to_pattern_dict = idx_to_pattern_dict)
    check_rules(solution_matrix = matx, bucket_num = bucket_num,
            ruleset = rule_data,  _model= s.model(), pattern_to_idx_dict = pattern_to_idx_dict)

    mat_entries_lst = generate_mat_table_entries(solution_matrix = matx, _model= s.model(),
            pattern_to_idx_dict = pattern_to_idx_dict, bucket_num = bucket_num,
            ruleset = rule_data)

    print(mat_entries_lst)