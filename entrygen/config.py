# coding=utf-8

PATTERN_MAX_NUM = 16
SWITCH_CONFIG = {
    "stride_mat_name": "t_get_stride",
    "dfa_mat_name": "t_DFA_match_%d",
    "policy_mat_name": "t_policy",
    "received_char": "hdr.patrns[%d].string",
    "current_state": "meta.state",
    "pattern_state": "meta.pattern_state",
    "accept_action_name": "a_accept",
    "goto_action_name": "a_set_state_%d",
    "stride_action_name": "a_get_stride",
    "policy_action_name": "a_set_lpm",
    "drop_action_name": "a_drop",
    "stride_param": "_stride",
    "next_state": "_state",
    "modifier": "modifier",
    "max_stride": 2,
}
SWITCH_BUCKET_CONFIG = {

    "root_state_action_name": "a_get_root_state",
    "root_state_mat_name": "t_get_root_state",
    
    "received_char": "hdr.patrns[%d].pattern",
    "current_state": "meta.state",
    "accept_action_name": "a_set_state_%d_b%d",
    "goto_action_name": "a_set_state_%d",
    "drop_action_name": "a_drop",
    "stride_para": "_stride",
    "next_state_para": "_state",
    "bucekt_id_para": "_bucket_id",
    "pattern_code_para": "pattern_code",

    "dfa_mat_name": "t_DFA_match_%d",

    "bucket1": "meta.b1",
    "bucket2": "meta.b2",
    "mark_as_drop": "a_mark_as_to_drop",
    "mark_as_forward": "a_mark_as_to_forward",
    "mark_as_to_send_backend": "a_mark_as_to_send_backend",

    "rule_mat_name": "t_pattern2rule",
    "max_stride": 2,
    "bucket_num": 2,
    
}
# TOFINO_CONFIG = {
#     "stride_mat_name": "t_get_stride",
#     "dfa_mat_name": "t_DFA_match_%d",
#     "policy_mat_name": "t_policy",
#     "received_char": "idsMeta.w%d",
#     "current_state": "idsMeta.state",
#     "pattern_state": "idsMeta.pattern_state",
#     "accept_action_name": "a_accept",
#     "goto_action_name": "a_set_state_%d",
#     "stride_action_name": "a_get_stride",
#     "policy_action_name": "a_set_lpm",
#     "drop_action_name": "a_drop",
#     "stride_param": "_stride",
#     "next_state": "_state",
#     "modifier": "modifier",
# }


