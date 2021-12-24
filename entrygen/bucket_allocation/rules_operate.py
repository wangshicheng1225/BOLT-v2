# coding=utf-8
# please run in python3 
from scapy.all import *
import jsonio as jsio
import sat as sat



def process_ruleset(file_name = "snort297_ascii_content_ruleset.json"):
    
    # trim out the empty rule only
    
    ruleset = jsio.load(file_name)
    # preprocess the ruleset to remove rules with no pattern

    non_empty_ruleset = {key:pattern_lst for key, pattern_lst in ruleset.items() if (len(pattern_lst) > 0 )} 
    processed_ruleset = non_empty_ruleset
    
    print(processed_ruleset)
    pattern_to_bucket_dict, idx_to_pattern_dict, pattern_to_idx_dict, bucket_num = sat.allocate_bucket(processed_ruleset)
    bucket_num_dict = {}
    bucket_num_dict["bktnum"] = bucket_num
    jsio.store(processed_ruleset, "non_empty_snort297_ascii_content_ruleset.json")
    jsio.store(pattern_to_bucket_dict,filename="non_empty_pattern_to_bucket_dict.json")
    jsio.store(idx_to_pattern_dict, "non_empty_idx_to_pattern_dict.json")
    jsio.store(pattern_to_idx_dict, "non_empty_pattern_to_idx_dict.json")
    jsio.store(bucket_num_dict, "non_empty_bucket_num_dict.json")
    return 0