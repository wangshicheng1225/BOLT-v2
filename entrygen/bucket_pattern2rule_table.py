
NULL_PATTERN_CODE = "NAN"
NULL_BUCEKT_ID = -1
from config import SWITCH_BUCKET_CONFIG, SWITCH_CONFIG

class BucketPattern2ruleTable(object):
    '''   
******SC_ID********
['***', '11*', '000', '011', '00*', '10*', '111']
['010', '110', '000', '011', '001', '100', '111']
******dump_var_stride_shadow_mat_lst********
(('11*', 'he'), 'goto', ('011', 1))
(('000', 'e'), 'goto', ('011', 1))
(('00*', 'is'), 'goto', ('111', 2))
(('10*', 's'), 'goto', ('111', 2))
(('***', 'hi'), 'goto', ('100', 0))
(('***', 'sh'), 'goto', ('000', 0))
(('***', '\xffh'), 'goto', ('001', 0))
(('***', '\xffs'), 'goto', ('110', 0))

return
(('11*', 'he'), 'goto', ('011', (1, '01')))
(('000', 'e'), 'goto', ('011', (1, '01')))
(('00*', 'is'), 'goto', ('111', (2, '10')))
(('10*', 's'), 'goto', ('111', (2, '10')))
(('***', 'hi'), 'goto', ('100', (-1, 'NAN')))
(('***', 'sh'), 'goto', ('000', (-1, 'NAN')))
(('***', '\xffh'), 'goto', ('001', (-1, 'NAN')))
(('***', '\xffs'), 'goto', ('110', (-1, 'NAN')))
    '''
    def __init__(self, var_stride_shadow_mat_lst, pattern_list, SC_ID_tuple,\
            switch_config, cover_code_length, \
                ruleset = None, bucket_num = None,
            pattern2bucekt_dict = None, pattern2code_dict = None , nfa = None):
        self.var_stride_shadow_mat_lst = var_stride_shadow_mat_lst
        self.nfa = nfa
        # self.defer_tree_lst = defer_tree_lst
        print("INIT BUCKET RULE TABLE")
        print(self.var_stride_shadow_mat_lst)

        print(pattern_list)
        print(SC_ID_tuple)
        print("END FOR BUCKET RULE TABLE PARAMETERS")
        # bucke ruleset 
        '''
        r1 "she" "his"
        r2 "cat"
        '''
        # some dirty codes for strawman validation
        if pattern2bucekt_dict == None or pattern2code_dict == None:
            self.pattern2bucekt_dict = {"she": 1, "his": 1, "cat":2}  
            self.pattern2code_dict = {"she": "01", "his": "10", "cat":"11"}
        else:
            self.pattern2bucekt_dict = pattern2bucekt_dict
            self.pattern2code_dict = pattern2code_dict
        
        if pattern_list == None:
            self.pattern_list = ["she","his","cat"]
        else:
            self.pattern_list = pattern_list

        if ruleset == None:
            self.ruleset = {"r1":["she"],"r2":["his"]}
            self.bucket_num = 2
        else:
            self.ruleset = ruleset
            self.bucket_num - bucket_num
        self.SC_ID_tuple = SC_ID_tuple
        self.SC_lst = self.SC_ID_tuple[0]
        self.ID_lst = self.SC_ID_tuple[1]
        self.cover_code_length = cover_code_length
        self.state_width = len(var_stride_shadow_mat_lst[0][0][0])
        
        # self.state_table = self.nfa[0]# {0: 0, 1: 0, 2: 0, 3: 1, 4: 0, 5: 0, 6: 2}
        # self.failure_transition_table  = self.nfa[2] #{0: {}, 1: 0, 2: 4, 3: 0, 4: 0, 5: 0, 6: 1}
        # self.goto_transition_table = self.nfa[1] #{0: {'h': 4, 's': 1}, 1: {'h': 2}, 2: {'e': 3}, 3: {}, 4: {'i': 5}, 5: {'s': 6}, 6: {}}

        self.bucket_var_stride_shadow_mat_lst = []
        self.bucket_pattern2rule_mat_lst =[]

        self.switch_config = switch_config
        self.runtime_nfa_shadow_mat_entries = []
        self.runtime_default_mat_entries = []
        pass



    def gen_var_stride_shadow_mat_bucket_lst(self):
        
        for entry in self.var_stride_shadow_mat_lst:
            match_state, match_chars = entry[0]
            goto_str = entry[1]
            dst_state, acc_pattern_idx = entry[2]
            if acc_pattern_idx > 0:
                acc_pattern = self.pattern_list[acc_pattern_idx-1]
                bucket_idx = self.pattern2bucekt_dict[acc_pattern]
                pattern_code = self.pattern2code_dict[acc_pattern]
            else:
                bucket_idx = NULL_BUCEKT_ID
                pattern_code = NULL_PATTERN_CODE
            new_entry = ( (match_state, match_chars), entry[1], \
                (dst_state, (bucket_idx, pattern_code)))
            
            self.bucket_var_stride_shadow_mat_lst.append(new_entry)
        

    def gen_bucket_pattern2rule_mat_lst(self):
        
        '''
        ( ("01", "10"), send)
        '''
        for sid, pattern_lst in self.ruleset.items():
            bucket_match_field = []
            for i in range(self.bucket_num):
                bucket_match_field.append("*")
            for pattern in pattern_lst:
                bucket_idx = self.pattern2bucekt_dict[pattern]
                pattern_code = self.pattern2code_dict[pattern]
                bucket_match_field[bucket_idx-1] = pattern_code
            newentry = ( tuple(bucket_match_field), "forward")
            self.bucket_pattern2rule_mat_lst.append(newentry)
        
        
    def gen_runtime_var_stride_shadow_mat_lst(self, table_id_list):
        '''
        bucket_var_stride_shadow_mat_lst
        (('11*', 'he'), 'goto', ('011', (1, '01')))
        (('000', 'e'), 'goto', ('011', (1, '01')))
        (('00*', 'is'), 'goto', ('111', (2, '10')))
        (('10*', 's'), 'goto', ('111', (2, '10')))
        (('***', 'hi'), 'goto', ('100', (-1, 'NAN')))
        (('***', 'sh'), 'goto', ('000', (-1, 'NAN')))
        (('***', '\xffh'), 'goto', ('001', (-1, 'NAN')))
        (('***', '\xffs'), 'goto', ('110', (-1, 'NAN')))
        ............................
        '''
        
        MAX_STRIDE = self.switch_config['max_stride']
        self.runtime_nfa_shadow_mat_entries = []
        for table_id in table_id_list:
            for (match, action, action_params) in self.bucket_var_stride_shadow_mat_lst:
                runtime_mat_entry = {}
                runtime_mat_entry["table"] = \
                        self.switch_config["dfa_mat_name"] % table_id
                
                state, mask = self.__generate_state_value_mask(match[0], int(self.state_width))
                
                runtime_mat_entry["match"] = {
                    SWITCH_BUCKET_CONFIG["current_state"]: [state, mask]
                        
                }
                                    
                cur_entry_stride = len(match[1])
                if len(match[1]) > MAX_STRIDE:
                    print("MAX_STRIDE EXCEED ERROR")
                    exit(1)
                for idx in range(len(match[1])):
                    received_char = match[1][idx]
                    # Follow systement is for difference 
                    # between python2 and python3
                    if type(received_char) != int:
                        received_char = ord(match[1][idx])
                    if ord(b'\xff') != received_char:
                        field_name = SWITCH_BUCKET_CONFIG["received_char"] % idx
                        runtime_mat_entry["match"][field_name] \
                                = [received_char, 255]
                    else:
                        field_name = SWITCH_BUCKET_CONFIG["received_char"] % idx
                        runtime_mat_entry["match"][field_name] \
                                = [0, 0]
                if len(match[1]) < MAX_STRIDE:# padding the match str field
                    for idx in range(len(match[1]),MAX_STRIDE):
                        field_name = SWITCH_BUCKET_CONFIG["received_char"] % idx
                        runtime_mat_entry["match"][field_name] \
                                = [0, 0]
                dst_state, (bucket_id, pattern_code)= action_params
                if bucket_id == NULL_BUCEKT_ID:
                    runtime_mat_entry["action_name"] = \
                            SWITCH_BUCKET_CONFIG["goto_action_name"] % cur_entry_stride
                    runtime_mat_entry["action_params"] = {
                        SWITCH_BUCKET_CONFIG["next_state_para"]: self.__generate_state_value_mask(dst_state, int(self.state_width))[0],
                        
                    }
                else:
                    runtime_mat_entry["action_name"] = \
                            SWITCH_BUCKET_CONFIG["accept_action_name"] % (cur_entry_stride, bucket_id)
                    runtime_mat_entry["action_params"] = {
                        SWITCH_BUCKET_CONFIG["next_state_para"]: self.__generate_state_value_mask(dst_state, int(self.state_width))[0],
                        
                        SWITCH_BUCKET_CONFIG["pattern_code_para"]: self.__generate_state_value_mask(pattern_code, len(pattern_code))[0],
                    }
                # if action == "goto":
                #     runtime_mat_entry["action_name"] = \
                #             SWITCH_CONFIG["goto_action_name"] % self.stride
                #     runtime_mat_entry["action_params"] = {
                #         SWITCH_CONFIG["next_state"]: self.__generate_state_value_mask(action_params[0], int(self.cover_code_length))[0],
                #         SWITCH_CONFIG["modifier"]: action_params[1],
                #     }
                # elif action == "accept":
                    # runtime_mat_entry["action_name"] = \
                            # SWITCH_CONFIG["accept_action_name"]
                    # runtime_mat_entry["action_params"] = {
                        # SWITCH_CONFIG["next_state"]: action_params[0],
                    # }
                self.runtime_nfa_shadow_mat_entries.append(runtime_mat_entry)

                
        
        return self.runtime_nfa_shadow_mat_entries
       
        pass
    def gen_runtime_default_entries(self, table_id_lst, **kwargs):
        '''
        kwargs = {
            "root_state":2;
        }
        '''
        # get root state
        # pattern_table default action
        '''
        get_state_default_entry
        {
            "table": "MyIngress.t_get_root_state",
            "default_action": true,
            "action_name": "MyIngress.a_get_root_state",
            "action_params": {"_state":3, "pattern_code":1}
    
        }
        
        '''
        self.runtime_default_mat_entries = []
        root_state = kwargs["root_state"]
        max_stride = kwargs["max_stride"]
        t_get_state_default_entry = {}
        t_get_state_default_entry["table"] = SWITCH_BUCKET_CONFIG["root_state_mat_name"]
        t_get_state_default_entry["action_name"] = SWITCH_BUCKET_CONFIG["root_state_action_name"]
        t_get_state_default_entry["action_params"] = {"root_state": root_state}
        t_get_state_default_entry["default_action"] = True

        self.runtime_default_mat_entries.append(t_get_state_default_entry)
        for table_id in table_id_lst:
            
            t_dfa_match_default_entry = {}

            t_dfa_match_default_entry["table"] = SWITCH_BUCKET_CONFIG["dfa_mat_name"] % table_id
            t_dfa_match_default_entry["action_name"] = SWITCH_BUCKET_CONFIG["goto_action_name"] % max_stride
            t_dfa_match_default_entry["action_params"] = {"_state": root_state}
            t_dfa_match_default_entry["default_action"] = True
            self.runtime_default_mat_entries.append(t_dfa_match_default_entry)

        return self.runtime_default_mat_entries
        
        pass
    def gen_runtime_bucket_pattern2rule_mat_lst(self):
        '''
        ..............................
        bucket_pattern2rule_mat_lst
        (('01', '10'), 'send')
        '''
        pass

    def __generate_state_value_mask(self, match_state, state_width):
        #'11*'
        
        max_num_of_bits = (1<< int(state_width)) - 1
        star_num = match_state.count('*')
        exact_state_str = match_state.replace('*','0')
        mask = max_num_of_bits - ((1<<star_num) - 1)
        exact_state = int(exact_state_str,2)
        # print "match_state",match_state,state_width,star_num
        return exact_state,mask
    