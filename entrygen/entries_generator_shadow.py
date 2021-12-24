# coding=utf-8
# Generate an NFA with shadow-coding.
import ahocorasick
import json
import math
import copy
import sys
import math
import string
import random
import Queue
from config import SWITCH_BUCKET_CONFIG, SWITCH_CONFIG,PATTERN_MAX_NUM
from shadow_code_gen import getShadowCodeWithNFA
from shadow_code_gen import getSCIDWithNFA
from bucket_pattern2rule_table import BucketPattern2ruleTable

#Generate an NFA with shadowencoding.


def get_tree(root,tree_son):
    tree = []
    tree.append(root)
    if len(tree_son[root]) == 0:
        return tree
    for child in tree_son[root]:
        tree.append(get_tree(child,tree_son))
    return tree

def postOrderTranverseSort(treeLst,stateLst):
    root = treeLst[0]
    if len(treeLst)== 1:
        # print "postTran End in 2", treeLst, stateLst
        stateLst.append(root)
        return
    else:
        for index in range(1,len(treeLst)):
            postOrderTranverseSort(treeLst[index],stateLst)
        stateLst.append(root)
        # print "bianli End in 4", treeLst, treeLst, parentLst
        return

def reorderTableEntries(raw_mat_lst,defer_tree_lst):
    item = raw_mat_lst[0]
    stateID_bit_length = len(item[0][0])

    stateID_lst = []
    # bianli(8,defer_treee,lst)
    # lst.append(defer_treee[0])
    postOrderTranverseSort(defer_tree_lst,stateID_lst)
    reorder_mat_lst = []
    for stateID in stateID_lst:
        stateID_bin_str = bin(stateID).replace('0b','')
        stateID_bin_str = stateID_bin_str.zfill(int(stateID_bit_length))
        for item in raw_mat_lst:
            if item[0][0] == stateID_bin_str:
                reorder_mat_lst.append(item)

    return reorder_mat_lst
        
def dim(treeLst):
    # treelst = [0, [1], [2, [4]], [3, [5], [6]]]
    root = treeLst[0]
    if len(treeLst) == 1:
        return 0
    else:
        temp=1
        for i in range(1,len(treeLst)):
            temp += (1 << int(dim(treeLst[i])))
        return math.ceil(math.log(temp,2))
    pass

def bianli(stateID, treeLst,parentLst):
    # print "bianli start", stateID, treeLst,parentLst
    root = treeLst[0]
    if root == stateID:
        # parentLst.append(root)
        # print "parentLst appendRoots", root
        # print "bianli End in 1", stateID, treeLst, parentLst
        return True
    if len(treeLst)== 1:
        # print "bianli End in 2", stateID, treeLst, parentLst
        return False
    else:
        for index in range(1,len(treeLst)):
            if bianli(stateID,treeLst[index],parentLst):
                parentLst.append(treeLst[index][0])
                # print "parentLst append", index
                # print "bianli End in 3", stateID, treeLst, parentLst
                return True
        # print "bianli End in 4", stateID, treeLst, parentLst
        return False
    # print "bianli End in 5", stateID, treeLst, parentLst
    return False
def generate_state_value_mask( match_state, state_width):
        #'11*'
        
        max_num_of_bits = (1<< int(state_width)) - 1
        star_num = match_state.count('*')
        exact_state_str = match_state.replace('*','0')
        mask = max_num_of_bits - ((1<<star_num) - 1)
        exact_state = int(exact_state_str,2)
        # print "match_state",match_state,state_width,star_num
        return exact_state,mask

# def selfLoopingUnrolling(sub_lst_s0_1_stride, k):
#     '''
#     (('0000', 'h'), 'goto', ('0001', 0))
#     (('0000', 's'), 'goto', ('0111', 0))
#     (('0000', '*'), 'goto', ('0000', 0))
#     '''
#     k_lst = []
#     for i in range(0,k):
#         for item in sub_lst_s0_1_stride:
#             temp_item = ((item[0][0],i*'\xff'+item[0][1]), item[1],item[2])
#             k_lst.append(temp_item)
#     # item = sub_lst_s0_1_stride[-1]
#     k_lst.append(((item[0][0],(k)*'\xff'), item[1],(item[0][0],0)))
#     return k_lst

class VarStrideState(object):
    def __init__(self, state = 0, stride = 0, depth=0, entries_num =0):
        self.state = state
        self.stride = stride
        self.depth = depth
        self.entries_num = entries_num
    def __lt__(self, other):
        if self.stride < other.stride:
            return True
        elif self.stride == other.stride:
            return self.depth < other.depth
        else:
            return False
    def __str__(self):
        return '('+str(self.state) +', ' + str(self.stride) + ', '+ str(self.depth)+ ', '+str(self.entries_num)+ ')'
class VarStrideEnlarger(object):
    '''   
        (('001', 'h'), 'goto', ('010', 0))
        (('010', 'e'), 'goto', ('011', 1))
        (('100', 'i'), 'goto', ('101', 0))
        (('101', 's'), 'goto', ('110', 2))
        (('000', 'h'), 'goto', ('100', 0))
        (('000', 's'), 'goto', ('001', 0))
    '''
    def __init__(self, entries_list = [], nfa = None, defer_tree_lst = [], SC_ID_tuple = None):
        self.entries_list = entries_list
        self.nfa = nfa
        self.defer_tree_lst = defer_tree_lst
        self.SC_ID_tuple = SC_ID_tuple
        self.SC_lst = self.SC_ID_tuple[0]
        self.ID_lst = self.SC_ID_tuple[1]
        self.state_width = len(entries_list[0][0][0])
        self.state_table = self.nfa[0]# {0: 0, 1: 0, 2: 0, 3: 1, 4: 0, 5: 0, 6: 2}
        self.failure_transition_table  = self.nfa[2] #{0: {}, 1: 0, 2: 4, 3: 0, 4: 0, 5: 0, 6: 1}
        self.goto_transition_table = self.nfa[1] #{0: {'h': 4, 's': 1}, 1: {'h': 2}, 2: {'e': 3}, 3: {}, 4: {'i': 5}, 5: {'s': 6}, 6: {}}
        self.var_stride_mat_lst =[]
        self.var_stride_shadow_mat_lst =[]
        self.sub_table_dict = {}
    
        for entry in self.entries_list:
            index = int(entry[0][0],2)
            # print "ENTRY",entry,index,sub_table_dict.has_key(index)
            if self.sub_table_dict.has_key(index):
                self.sub_table_dict[index].append(entry)
            else:
                self.sub_table_dict[index] = []
                self.sub_table_dict[index].append(entry)
        self.depth_dict= {}
        for state in self.sub_table_dict.keys():
            state_itr = state
            self.depth_dict[state] = 0
            # if state_itr == 0:
            #     continue
            while(state_itr != 0):
                state_itr = self.failure_transition_table[state_itr]
                self.depth_dict[state] += 1
        

        
    def _selfLoopUnrolling (self, sub_lst_s0_1_stride, k):
        ''' 
        Tool function in class for unrolling selfloop

    (('11*', 'h'), 'goto', ('000', 0))

    (('000', 'e'), 'goto', ('011', 1))
    (('00*', 'i'), 'goto', ('100', 0))
    (('10*', 's'), 'goto', ('111', 2))
    (('***', 'h'), 'goto', ('001', 0))
    (('***', 's'), 'goto', ('110', 0))
        '''
        k_lst = []
        for i in range(0,k):
            for item in sub_lst_s0_1_stride:
                temp_item = ((item[0][0],i*'\xff'+item[0][1]), item[1],item[2])
                k_lst.append(temp_item)
        # item = sub_lst_s0_1_stride[-1]
        # k_lst.append(((item[0][0],(k)*'\xff'), item[1],(item[0][0],0)))
        return k_lst



    def construct_defer_tree(self, defer_tree_lst):
        defer_tree = defer_tree_lst
        return defer_tree

    def increase_stride(self, sub_lst_si_k, defer_tree, nfa, Si, stride_max):
        
        '''
        For (strs, dst) in T(sp, k-1): # the k-1 stride table
            for sj in defer_path( dst ) – [s0]:   #[s2, s4, s0 ]-  [s0]
                for (char, sd) in T(sj,1): #the Trie
                    if sd  in ACC:
                        ACTION = ACTION || ACTION(Sd)
                    add(  (sp, strs+char,  k/sd)   )


        si should be the initial code, NOT THE SHADOWCODE !!!
        (('001', 'h'), 'goto', ('010', 0))
        (('010', 'e'), 'goto', ('011', 1))
        (('100', 'i'), 'goto', ('101', 0))
        (('101', 's'), 'goto', ('110', 2))
        (('000', 'h'), 'goto', ('100', 0))
        (('000', 's'), 'goto', ('001', 0))
            [0, [1, [6]], [3], [4, [2]], [5]]
        '''
        # si = sub_lst_si[0][0][0] #'0000'
        sub_lst_si_kp1 = []
        
        # out_state_lst = []
        no_larging_flag = 1
        for entry in sub_lst_si_k:
            input_str = entry[0][1]
            dst_state = entry[2][0]
            action_mask = entry[2][1]
            dst_state_code = int(dst_state,2)
            state_code_itr = dst_state_code
            suffix_lst = [] #('a', sj, mask)
            while(state_code_itr!= 0):
                goto_dict = self.goto_transition_table[state_code_itr] #{'h': 4, 's': 1}
                for key in goto_dict.keys():
                    char = key
                    dst_state_1 = goto_dict[key]
                    action_mask_1 = self.state_table[dst_state_1]
                    action_mask_1 = action_mask | action_mask_1
                    # (('0000', 'sh'), 'goto', ('1000', 0))
                    # (('0000', 'she'), 'goto', ('1001', 2))
                    dst_state_str1 = bin(dst_state_1).replace('0b','')
                    dst_state_str1 = dst_state_str1.zfill(self.state_width)
                    temp_suffix_kp1 = (char,(dst_state_str1,action_mask_1))
                    suffix_lst.append(temp_suffix_kp1)
                state_code_itr = self.failure_transition_table[state_code_itr]
            if len(suffix_lst)!=0:
                no_larging_flag = 0
                for suffix in suffix_lst:
                    if len(input_str+suffix[0])>stride_max:
                        temp_entry_kp1 = ((entry[0][0],input_str+suffix[0]),'goto',suffix[1])# suffix[1]==(dst_state_str1,action_mask_1))
                        sub_lst_si_kp1.append(temp_entry_kp1)
            else:
                pass
                # sub_lst_si_kp1.append(entry)
        
        return sub_lst_si_kp1 + sub_lst_si_k,no_larging_flag
                

    def increment_stride(self, sub_lst_si_k, defer_tree, nfa, Si, stride_max):
     
        '''
        For (strs, dst) in T(sp, k-1): # the k-1 stride table
            for sj in defer_path( dst ) – [s0]:   #[s2, s4, s0 ]-  [s0]
                for (char, sd) in T(sj,1): #the Trie
                    if sd  in ACC:
                        ACTION = ACTION || ACTION(Sd)
                    add(  (sp, strs+char,  k/sd)   )


           si should be the initial code, NOT THE SHADOWCODE !!!
            (('001', 'h'), 'goto', ('010', 0))
            (('010', 'e'), 'goto', ('011', 1))
            (('100', 'i'), 'goto', ('101', 0))
            (('101', 's'), 'goto', ('110', 2))
            (('000', 'h'), 'goto', ('100', 0))
            (('000', 's'), 'goto', ('001', 0))
                [0, [1, [6]], [3], [4, [2]], [5]]
        '''
        # si = sub_lst_si[0][0][0] #'0000'
        sub_lst_si_kp1 = []
        
        # out_state_lst = []
        no_larging_flag = 1
        for entry in sub_lst_si_k:
            input_str = entry[0][1]
            dst_state = entry[2][0]
            action_mask = entry[2][1]
            dst_state_code = int(dst_state,2)
            state_code_itr = dst_state_code
            suffix_lst = [] #('a', sj, mask)
            while(state_code_itr!= 0):
                goto_dict = self.goto_transition_table[state_code_itr] #{'h': 4, 's': 1}
                for key in goto_dict.keys():
                    char = key
                    dst_state_1 = goto_dict[key]
                    action_mask_1 = self.state_table[dst_state_1]
                    action_mask_1 = action_mask | action_mask_1
                    # (('0000', 'sh'), 'goto', ('1000', 0))
                    # (('0000', 'she'), 'goto', ('1001', 2))
                    dst_state_str1 = bin(dst_state_1).replace('0b','')
                    dst_state_str1 = dst_state_str1.zfill(self.state_width)
                    temp_suffix_kp1 = (char,(dst_state_str1,action_mask_1))
                    suffix_lst.append(temp_suffix_kp1)
                state_code_itr = self.failure_transition_table[state_code_itr]
            if len(suffix_lst)!=0:
                no_larging_flag = 0
                for suffix in suffix_lst:
                    temp_entry_kp1 = ((entry[0][0],input_str+suffix[0]),'goto',suffix[1])# suffix[1]==(dst_state_str1,action_mask_1))
                    sub_lst_si_kp1.append(temp_entry_kp1)
            else:
                sub_lst_si_kp1.append(entry)
        
        return sub_lst_si_kp1,no_larging_flag
                

    def test_increment_stride(self):
               
        pass

    def increase_root_stride(self,root_lst, var_root_stride=2):
        var_root_lst = []
        root_stride_max = 1
        # for i in range(3):
        var_root_lst = root_lst
        for i in range(1,var_root_stride):
            var_root_lst,no_larging_flag = self.increase_stride(var_root_lst,self.defer_tree_lst,self.nfa,0,i)
            
        # print var_root_lst
        # print no_larging_flag
        
        return var_root_lst
        
    def simple_increment_table(self, sub_lst_si_k, defer_tree, nfa, Si, K):
        encounter_acc = False 
        sub_lst_si_kp1 = []
        
    #     no_larging_flag = 1
        stride = 1
        for k in range(1,K):
            
            if encounter_acc:
                break
            else :
                sub_lst_si_kp1=[]
                for entry in sub_lst_si_k:
                    # (('0000', 'sh'), 'goto', ('1000', 0))
                    # (('0000', 'she'), 'goto', ('1001', 2))
                    input_str = entry[0][1]
                    dst_state_str = entry[2][0]
                    action_mask = entry[2][1] # shoul
                    if action_mask !=0 : 
                        encounter_acc=True
                        return sub_lst_si_k,stride
                    dst_state= int(dst_state_str,2)
                    
                    suffix_lst = [] #('a', sj, mask)
                    goto_dict = self.goto_transition_table[dst_state]
                    for key in goto_dict.keys():
                        char = key
                        dst_state_1 = goto_dict[key]
                        action_mask_1 = self.state_table[dst_state_1]
                        # action_mask_1 = action_mask | action_mask_1
                        # (('0000', 'sh'), 'goto', ('1000', 0))
                        # (('0000', 'she'), 'goto', ('1001', 2))
                        dst_state_str1 = bin(dst_state_1).replace('0b','')
                        dst_state_str1 = dst_state_str1.zfill(self.state_width)
                        temp_suffix_kp1 = (char,(dst_state_str1,action_mask_1))
                        suffix_lst.append(temp_suffix_kp1)
                        if action_mask_1 != 0:#ACC ENCOUNTER
                            encounter_acc = True
                    if len(suffix_lst)!=0:
                        no_larging_flag = 0
                        for suffix in suffix_lst:
                            temp_entry_kp1 = ((entry[0][0],input_str+suffix[0]),'goto',suffix[1])# suffix[1]==(dst_state_str1,action_mask_1))
                            sub_lst_si_kp1.append(temp_entry_kp1)
                    
                sub_lst_si_k = copy.deepcopy(sub_lst_si_kp1)
                stride = k + 1
        return sub_lst_si_k,stride

    def simple_increase_root_table(self, root_lst, defer_tree, nfa, Si, K):

        encounter_acc = False  
        
        '''
        For (strs, dst) in T(sp, k-1): # the k-1 stride table
            for sj in defer_path( dst ) – [s0]:   #[s2, s4, s0 ]-  [s0]
                for (char, sd) in T(sj,1): #the Trie
                    if sd  in ACC:
                        ACTION = ACTION || ACTION(Sd)
                    add(  (sp, strs+char,  k/sd)   )
        '''
        # si = sub_lst_si[0][0][0] #'0000'
        
        
        root_lst_k = copy.deepcopy(root_lst)
        var_root_lst = copy.deepcopy(root_lst)
        # out_state_lst = []
        no_larging_flag = 1
        stride = 1
        for k in range(1,K):
            # print "k", k
            # print "stride",stride
            if encounter_acc == True:
                break
            else:
                root_lst_kp1 = []
                for entry in root_lst_k:
                    input_str = entry[0][1]
                    dst_state_str = entry[2][0]
                    action_mask = entry[2][1]
                    if action_mask !=0 : 
                        encounter_acc=True
                        return var_root_lst,stride
                    dst_state = int(dst_state_str,2)
                    # state_code_itr = dst_state
                    suffix_lst = [] #('a', sj, mask)
                    
                    goto_dict = self.goto_transition_table[dst_state] #{'h': 4, 's': 1}
                    for key in goto_dict.keys():
                        char = key
                        dst_state_1 = goto_dict[key]
                        action_mask_1 = self.state_table[dst_state_1]
                        if action_mask_1 != 0:
                            encounter_acc = True
                        # action_mask_1 = action_mask | action_mask_1
                        # (('0000', 'sh'), 'goto', ('1000', 0))
                        # (('0000', 'she'), 'goto', ('1001', 2))
                        dst_state_str1 = bin(dst_state_1).replace('0b','')
                        dst_state_str1 = dst_state_str1.zfill(self.state_width)
                        temp_suffix_kp1 = (char,(dst_state_str1,action_mask_1))
                        suffix_lst.append(temp_suffix_kp1)
                    if len(suffix_lst)!=0:
                        no_larging_flag = 0
                        for suffix in suffix_lst:
                            temp_entry_kp1 = ((entry[0][0],input_str+suffix[0]),'goto',suffix[1])# suffix[1]==(dst_state_str1,action_mask_1))
                            root_lst_kp1.append(temp_entry_kp1)

                var_root_lst = root_lst_kp1 + var_root_lst
                root_lst_k = root_lst_kp1
                stride = k+1
                # sub_lst_si_kp1.append(entry)
        
        
        return var_root_lst,stride
                    

    def var_striding_simple_main_procedure(self ,K=3):
        stateLst = []
        postOrderTranverseSort(self.defer_tree_lst, stateLst)
        print stateLst
        root_lst = self.sub_table_dict[0]
        vroot_lst = []
        #1. vroot_lst = self_looping_unrolling(K)
        '''
        (('0000', 'h*'), 'goto', ('1001', 2))
        (('0000', 's*'), 'goto', ('1001', 2))
        (('0000', '*s*'), 'goto', ('1000', 0))
        (('0000', '*h*'), 'goto', ('1000', 0))
        (('0000', '**h'), 'goto', ('1000', 0))
        (('0000', '**s'), 'goto', ('1000', 0))
        (('0000', '***'), 'goto', ('1000', 0))
        '''
        #2. vroot_lst = simple_increase(K)
        vroot_lst,k = self.simple_increase_root_table(root_lst=root_lst,defer_tree=self.defer_tree_lst,\
            nfa=self.nfa,Si=0,K=K)

        '''
        (('0000', 'his'), 'goto', ('1001', 2))
        (('0000', 'she'), 'goto', ('1001', 2))
        (('0000', '*sh'), 'goto', ('1000', 0))
        (('0000', '*hi'), 'goto', ('1000', 0))
        (('0000', '**h'), 'goto', ('1000', 0))
        (('0000', '**s'), 'goto', ('1000', 0))
        (('0000', '***'), 'goto', ('1000', 0))
        '''
        v_self_unloop_root_lst = self.self_var_root_looping_unrolling(vroot_lst,K=K)
        self.sub_table_dict[0] = v_self_unloop_root_lst
        # print "vroot_lst"
        # for entry in vroot_lst:
        #     print entry
        # print k 
        # print "v_self_unloop_root_lst"
        # for entry in v_self_unloop_root_lst:
        #     print entry
        # print k 
        for key in self.sub_table_dict.keys():
            if key == 0:
                continue
            # print "KEY ",key

            var_K_state_lst,k_state = self.simple_increment_table(sub_lst_si_k= self.sub_table_dict[key],defer_tree=self.defer_tree_lst,\
                nfa=self.nfa,Si=key,K=K)
            # print var_K_state_lst,k_state
           
            self.sub_table_dict[key] = var_K_state_lst
        #get non-root
        for i in stateLst:
            if self.sub_table_dict.has_key(i):
                # var_mat_lst_si = sub_table_dict[i]
                self.var_stride_mat_lst += self.sub_table_dict[i]
    
       
    def var_striding_main_procedure(self, var_root_stride = 1, N=30,K=3):

        entries_num = len(self.entries_list)
        stateLst = []
        postOrderTranverseSort(self.defer_tree_lst, stateLst)
        print stateLst
        root_lst = self.sub_table_dict[0]
        var_root_lst=self.increase_root_stride(root_lst,var_root_stride)
        # var_root_lst,no_larging_flag = self.increase_stride(var_root_lst,self.defer_tree_lst,self.nfa,0,2)
        # print var_root_lst
        # print no_larging_flag
        # if no_larging_flag ==1:# no enlarging
        #     pass
        # else:# no enlarging
        #     root_stride_max +=1

        # var_root_lst,no_larging_flag = self.increase_stride(var_root_lst,self.defer_tree_lst,self.nfa,0,3)
        
        # print var_root_lst
        # print no_larging_flag
        # if no_larging_flag ==1:# no enlarging
        #     pass
        # else:# no enlarging
        #     root_stride_max +=1

        # print "VAR ROOT LST"
        # print root_stride_max
        # for i in var_root_lst:
        #     print i
        # print "***********"
        
        k_root_lst = self._selfLoopUnrolling(var_root_lst,K)
        entries_num = entries_num - len(root_lst) + len(k_root_lst)
        self.sub_table_dict[0] = k_root_lst

        pque = Queue.PriorityQueue()
        for state in self.sub_table_dict.keys():
            if state == 0:
                continue #live state_0 alone
            pque.put(VarStrideState(state = state,\
                stride = 1,depth = self.depth_dict[state],\
                    entries_num=len(self.sub_table_dict[state])))
        
        # while not pque.empty():
        #     print pque.get()
        # print entries_num
        
        
        while(entries_num < N and not pque.empty()):
            state_tuple = pque.get() # state , stride , depth, entries_num
            si = state_tuple.state
            ki = state_tuple.stride
             
            depthi = state_tuple.depth
            # si_entries_num = state_tuple.entries_num
            # print state_tuple
            current_table_size = len(self.sub_table_dict[si])
            sub_lst_si_kp1,no_larging_flag = self.increment_stride(self.sub_table_dict[si], self.defer_tree_lst,self.nfa, si,ki)
            '''
            if return_table no enlarging:
                cannot enlarge without defering to s0
                do nothing
            else:
                if table num exceeds N:
                    not apply incrementing this subtable
                    not put into pque
                else
                    apply incrementing this subtable
                    if k+1 == K:
                        put into pque
            '''
            if no_larging_flag ==1:# no enlarging
                pass
            else:# no enlarging
                temp_num = entries_num - current_table_size + len(sub_lst_si_kp1)
                if temp_num <= N:
                    self.sub_table_dict[si] = sub_lst_si_kp1
                    entries_num = temp_num
                    if ki+1 < K:
                        pque.put(VarStrideState(state = si,\
                            stride = ki+1,depth = depthi,\
                                entries_num=len(self.sub_table_dict[si])))

        # self.var_stride_mat_lst =[]
        # self.var_stride_shadow_mat_lst =[]
        for i in stateLst:
            if self.sub_table_dict.has_key(i):
                # var_mat_lst_si = sub_table_dict[i]
                self.var_stride_mat_lst += self.sub_table_dict[i]
    
          
    def self_var_root_looping_unrolling(self,var_root_lst, K):
        '''
        (('000', 'his'), 'goto', ('110', 2))
        (('000', 'she'), 'goto', ('011', 1))
        (('000', 'hi'), 'goto', ('101', 0))
        (('000', 'sh'), 'goto', ('010', 0))
        (('000', 'h'), 'goto', ('100', 0))
        (('000', 's'), 'goto', ('001', 0))
        '''
        # stateLst = []
        # temp_lst=[]
        # postOrderTranverseSort(self.defer_tree_lst, stateLst)
        # root_lst = self.sub_table_dict[0]
        v_self_unloop_root_lst=[]
        for entry in var_root_lst:
            input_str = entry[0][1]
            self_unloop_input_str = '\xff'*(K-len(input_str))+input_str
            tempentry = ((entry[0][0],self_unloop_input_str),entry[1],entry[2])
            v_self_unloop_root_lst.append(tempentry)
        return v_self_unloop_root_lst
        
    def self_looping_unrolling(self,K=3):
        stateLst = []
        temp_lst=[]
        postOrderTranverseSort(self.defer_tree_lst, stateLst)
        root_lst = self.sub_table_dict[0]
        k_root_lst = self._selfLoopUnrolling(root_lst,K)
        self.sub_table_dict[0] = k_root_lst
        for i in stateLst:
            if self.sub_table_dict.has_key(i):
                # var_mat_lst_si = sub_table_dict[i]
                self.var_stride_mat_lst += self.sub_table_dict[i]
        pass
        # for i in sub_lst_s1_kp1:
        #     print i
        # print "*******"
        # for i in sub_lst_s4_kp1:
        #     print i

        # for key in sub_table_dict.keys():
        #     print key
        #     for i in sub_table_dict[key]:
        #         print i
        #     print "*************"
    def allocate_shadowcode(self):
        # shadow_coded_var_mat_lst = []
        for item in self.var_stride_mat_lst:#:
            shadow_state_ID = self.SC_lst[int(item[0][0],2)] 
            ID_state_ID = self.ID_lst[int(item[2][0],2)]
            # print "reorder compress lst item", item, item[0][0], "SC",int(item[0][0],2), shadow_state_ID, "ID", item[2][0], int(item[2][0],2),ID_state_ID
            temp_item = ((shadow_state_ID,item[0][1]),item[1],(ID_state_ID,item[2][1]))
            self.var_stride_shadow_mat_lst.append(temp_item)  
        return self.var_stride_shadow_mat_lst
        

    def dump_sub_table(self):
        stateLst = []
        temp_lst=[]
        postOrderTranverseSort(self.defer_tree_lst, stateLst)
        print stateLst
        for i in stateLst:
            if self.sub_table_dict.has_key(i):
                # var_mat_lst_si = sub_table_dict[i]
                temp_lst += self.sub_table_dict[i]
        for i in temp_lst:
            print i

    def dump_var_stride_mat(self):
        print "******dump_var_stride_mat********"
        for i in self.var_stride_mat_lst:
            print i
        print "**************"
    def dump_var_stride_shadow_mat(self):
        print "******SC_ID********"
        print self.SC_lst 
        print self.ID_lst 
        
        print "******dump_var_stride_shadow_mat_lst********"
        for i in self.var_stride_shadow_mat_lst:
            print i
        print "**************"

class VarStrideMatchTable(object):
    def __init__(self, entries_list = None,max_stride=1, ID_lst=[] , defer_tree_lst = []):
    # ('0000', 'hi'), 'goto', ('0010', 0))
    # (('0000', 'he'), 'goto', ('0100', 2))
    # (('0000', 'sh'), 'goto', ('1000', 0))
    # (('0000', '\xffh'), 'goto', ('0001', 0))
    # (('0000', '\xffs'), 'goto', ('0111', 0)
        self._entries_list = []    
        self.default_entry = None
        self.mat_stride = 0
        self.max_stride = max_stride #int
        self.state_width = len(entries_list[0][0][0])
        self.defer_tree_lst = defer_tree_lst
        # print "stateWidth",self.state_width
        if entries_list != None:
            for entry in entries_list:
                state_value, state_mask = self.generate_state_value_mask(entry[0][0],self.state_width)
                match_char = entry[0][1]
                match_char_len = len(match_char)
                self._entries_list.append(
                    ( (state_value,  state_mask, match_char) ,(entry[2][0],match_char_len, entry[2][1]))  )
                # self._entries_list.append((entry[0],(entry[2][0],match_char_len))) 
        self.root_ID = ID_lst[0]
        self.default_entry = ((0, 0, '\xff'*self.max_stride) ,(self.root_ID, match_char_len,0))
        self._entries_list.append(
            ((0, 0, '\xff'*self.max_stride) ,(self.root_ID, match_char_len,0))
        )

    def generate_state_value_mask(self, match_state, state_width):
        #'11*'
        
        max_num_of_bits = (1<<state_width) - 1
        star_num = match_state.count('*')
        exact_state_str = match_state.replace('*','0')
        mask = max_num_of_bits - ((1<<star_num) - 1)
        exact_state = int(exact_state_str,2)
        # print "match_state",match_state,state_width,star_num
        return exact_state,mask

    def get_match_decision(self, input_state, input_str):
        input_len = len(input_str)
        
        for entry in self._entries_list:
            # print entry
            # temp_match_masked = entry.match_field[0] & entry.match_field[1]
            # if temp_match_masked == input_str & entry.match_field[1]:
            # if int(entry[0][0],2)== int(input_state,2):# and entry[0][1] == input_str:


            if (entry[0][0] & entry[0][1]) == (int(input_state,2) & entry[0][1]):
                if len(input_str) < len(entry[0][2]):
                    match_str = input_str + '\xff'*(len(entry[0][2])-len(input_str))
                    match_len = len(match_str)
                else:
                    match_str = input_str[0: len(entry[0][2])]
                    match_len = len(match_str)
                flag = 1

                for i in range(0,match_len):
                    if entry[0][2][i] == '\xff':
                        continue
                    elif entry[0][2][i] == match_str[i]:
                        continue
                    else:
                        flag = 0
                        break
                if flag == 1: 
                    # print "match ",entry
                    return entry[1]
                else:
                    # print "loss match ",'0000',match_len
                    continue
        # print "loss match"
        # ((6, 6, 'h'), ('000', 1, 0)))
        return self.default_entry[1]

    def match(self, pair):
        src_state = pair[0]
        input_str = pair[1]
        match_entry = self.get_match_decision(src_state, input_str)     
        # print "MATCH", match_entry  
        # ((6, 6, 'h'), ('000', 1, 0)))
        #match_entry ('000', 1, 0))
        # if type(self.max_stride) == int:
        self.mat_stride = match_entry[1]
        if type(self.mat_stride) == int:
            rest_str = input_str[self.mat_stride:]
        else:
            rest_str = input_str
        return  match_entry[0], rest_str, match_entry[1] #dst_state, rest_str, stride 

    def remove_last_action(self):
        # to debug, compare whether last ele in list is default_entry
        self._entries_list.pop(-1)

    def dump(self):
        if len(self._entries_list) == 0:
            print("EMPTY_TABLE")
        else:
            for entry in self._entries_list:
                print( "< match, action_name, paramlist> ", entry)
    def get_len(self):
        return len(self._entries_list)





class NFAMatchEntriesShadowGenerator():
    def __init__(self, pattern_expression, stride=1, table_id_list=[0]):
        # Init and configure the automaton
        self.stride = stride
        self.table_id_list = table_id_list
        self.pattern_list, self.policies = \
                self.parse_pattern_expression(pattern_expression)
        self.automaton = self.generate_automaton(self.pattern_list)
        # Gegerate dfa descriptor according to the automaton
        
        self.nfa = self.generate_nfa(self.automaton.dump())
        self.defer_tree = self.generate_defer_tree(self.nfa)
        
        # self.shadow_code = getShadowCodeWithNFA(self.nfa)
        # self.dfa = self.generate_dfa(self.automaton.dump())
        # self.fulldfa = self.generate_fulldfa(self.automaton.dump())
        # self.shadow_code = getShadowCodeWithDFA(self.dfa)
        # self.ID_code = 
        print("PRINT PATTERNLEST")
        print(self.pattern_list)
        print("PRINT POLICIES")
        print( self.policies)
        print("END FOR POLICIES")
        self.SC_ID_tuple = getSCIDWithNFA(self.nfa, self.defer_tree)
        self.cover_code_length = self.get_cover_code_length(self.nfa, self.defer_tree)
        self.nfa_mat_entries = self.generate_nfa_mat_entreis(self.nfa, self.defer_tree)
        self.nfa_shadow_mat_entries = self.generate_nfa_shadow_mat_entries(self.nfa_mat_entries, self.defer_tree, self.SC_ID_tuple)
        self.nfa_shadow_default_entry = self.generate_default_shadow_mat_entry(self.nfa_mat_entries, self.defer_tree, self.SC_ID_tuple)
        # # self.dfa = self.recode_dfa(self.dfa, self.shadow_code)
        # # stride should always be 1, msdfa no use now
        # self.msdfa = self.generate_multi_stride_dfa(self.dfa, self.stride)
        # self.dfa_mat_entries = self.generate_dfa_mat_entries(self.msdfa)
        
        
        

        ## TODO & doing now integrate vstride_entreis_generator in this class, implementing k-stride mat entries
        self.vstride_table = VarStrideEnlarger(entries_list= self.nfa_mat_entries,nfa=self.nfa,defer_tree_lst=self.defer_tree, SC_ID_tuple=self.SC_ID_tuple)

        # var_stride_mat_lst = vtable.var_strding_enlarge()
        # var_stride_shadow_mat_lst = vtable.allocate_shadowcode()
        # for i in var_stride_shadow_mat_lst:
        #     print i
        # var_strding_enlarge\
        self.vstride_table.dump_sub_table()
        # print "************"

        self.vstride_table.var_striding_simple_main_procedure(K=stride)

        self.vstride_table.allocate_shadowcode()
        self.vstride_table.dump_var_stride_mat()
        self.vstride_table.dump_var_stride_shadow_mat()

        self.vstride_nfa_mat_entries = self.vstride_table.var_stride_mat_lst
        self.vstride_nfa_shadow_mat_entries =  self.vstride_table.var_stride_shadow_mat_lst 

        self.runtime_nfa_shadow_mat_entries = self.generate_runtime_nfa_shadow_mat_entries(
            self.vstride_nfa_shadow_mat_entries,  self.table_id_list
        )
        self.runtime_policy_mat_entries = \
                self.generate_runtime_policy_mat_entries(self.policies)
        self.runtime_mat_default_entries = \
                self.generate_runtime_mat_default_entries(self.nfa_shadow_default_entry,\
                     self.table_id_list)
        
        self.runtime_mat_entries = \
                self.runtime_nfa_shadow_mat_entries + self.runtime_policy_mat_entries + \
                    self.runtime_mat_default_entries
        
        
        self.pattern2rule_table = \
            BucketPattern2ruleTable(var_stride_shadow_mat_lst= self.vstride_nfa_shadow_mat_entries,\
                pattern_list= self.pattern_list, SC_ID_tuple= self.SC_ID_tuple,\
                    switch_config= SWITCH_BUCKET_CONFIG, cover_code_length = self.cover_code_length)

        self.pattern2rule_table.gen_var_stride_shadow_mat_bucket_lst()
        self.pattern2rule_table.gen_bucket_pattern2rule_mat_lst()

        print("bucket_var_stride_shadow_mat_lst")
        for i in self.pattern2rule_table.bucket_var_stride_shadow_mat_lst:
            print(i)
        print( "..............................")
        print("bucket_var_stride_shadow_mat_lst")
        for i in self.pattern2rule_table.bucket_pattern2rule_mat_lst:
            print(i)
        print( "..............................")
        # self.bucket_runtime_nfa_shadow_mat_entries = \
        
        # self.pattern2rule_table.gen_runtime_var_stride_shadow_mat_lst()
        # self.bucket_runtime_rule_mat_entries = \
        # self.pattern2rule_table.gen_runtime_bucket_pattern2rule_mat_lst()
        
        

        
    def get_cover_code_length(self, nfa, defer_tree):
        #[0, [1], [2, [4]], [3, [5], [6]]]
        return dim(defer_tree)
        
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
        return pattern_list, policies

    def generate_automaton(self, pattern_list): # 
        automaton = ahocorasick.Automaton(ahocorasick.STORE_LENGTH)
        for pattern in pattern_list:
            automaton.add_word(pattern)
        automaton.make_automaton()
        return automaton

    def generate_nfa(self, automaton_graph_descriptor):
        '''

        return (
            nfa_nodes, nfa_goto_function, nfa_failure_function, \
            nfa_next_nodes, default_code
            ) 
        '''
        nodes = automaton_graph_descriptor[0]
        goto_transitions = automaton_graph_descriptor[1]
        failure_transitions = automaton_graph_descriptor[2]
        converse_dict = {}

        nfa_nodes = {}
        nfa_goto_function = {}
        nfa_failure_function = {}
        default_code = []
        pattern_idx = 0
        for node_id in range(len(nodes)):
            origin_node_id = nodes[node_id][0]
            converse_dict[origin_node_id] = node_id
            accept_flag = nodes[node_id][1]
            if accept_flag == 1:
                pattern_idx += 1
                accept_flag = pattern_idx
            nfa_nodes[node_id] = accept_flag
            # nfa_next_nodes[node_id] = []
            nfa_goto_function[node_id] = {}
            nfa_failure_function[node_id] = {}

        for edge in goto_transitions:
            start_node_id = converse_dict[edge[0]]
            transfer_char = edge[1]
            end_node_id = converse_dict[edge[2]]
            nfa_goto_function[start_node_id][transfer_char] = end_node_id
        
        for failure_link in failure_transitions:
            start_node_id = converse_dict[failure_link[0]]
            intermediate_node_id = converse_dict[failure_link[1]]
            # dfa_failure_links.append((start_node_id, intermediate_node_id))
            nfa_failure_function[start_node_id] = intermediate_node_id
        
        


        bit_width = math.ceil(math.log(len(nfa_nodes), 2))
        for nfa_node_id in nfa_nodes:
            str1 = bin(nfa_node_id).replace('0b','')
            str1 = str1.zfill(int(bit_width))
            # print str1
            default_code.append(str1)


        nfa_next_nodes = []
        return (
            nfa_nodes, nfa_goto_function, nfa_failure_function, \
            nfa_next_nodes, default_code
        )

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

    def generate_defer_tree(self, nfa):
        '''
        {0: 0, 1: 0, 2: 0, 3: 1, 4: 0, 5: 0, 6: 2}
        {0: {'h': 4, 's': 1}, 1: {'h': 2}, 2: {'e': 3}, 3: {}, 4: {'i': 5}, 5: {'s': 6}, 6: {}}
        {0: {}, 1: 0, 2: 4, 3: 0, 4: 0, 5: 0, 6: 1}
        '''
        failure_transitions = nfa[2]
        
        tree_son = {}
        for i in failure_transitions.keys():
            tree_son[i] = []
        for j in failure_transitions.keys():
            if j == 0:
                continue
            tree_son[failure_transitions[j]].append(j)
        
        root = 0
        # print failure_transitions
        # print "Tree son"
        # print tree_son
        tree = []
        tree = get_tree(root,tree_son)
        return tree

        # tree = [0]
        # q = Queue.Queue()
        # q.put(0)
        
        # current_tree = tree
        # while not q.empty():
        #     sub_root = q.get()
        #     lst = tree_son[sub_root]
        #     for i in lst:
        #         tree.append([i])
       
        

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
    
    def generate_nfa_mat_entreis(self, nfa, defer_tree):
        '''
        nfa:
        {0: 0, 1: 0, 2: 0, 3: 1, 4: 0, 5: 0, 6: 2}
        {0: {'h': 4, 's': 1}, 1: {'h': 2}, 2: {'e': 3}, 3: {}, 4: {'i': 5}, 5: {'s': 6}, 6: {}}
        {0: {}, 1: 0, 2: 4, 3: 0, 4: 0, 5: 0, 6: 1}
        '''
        #reorder entries
        nfa_nodes = nfa[0]
        goto_transitions= nfa[1]
        failure_transitions = nfa[2]
        default_code = nfa[4]
        mat_entries = []
        stateLst = []
        postOrderTranverseSort(defer_tree, stateLst)
        # print "default_code"
        # print default_code
        # print 'stateLst'
        # print stateLst
        for current_state in stateLst:
            for received_chars in goto_transitions[current_state].keys():
                match = (default_code[current_state], received_chars)
                next_state = goto_transitions[current_state][received_chars]
                action = 'goto'
                modifier = 0
                if nfa_nodes[next_state] != 0:
                    modifier = 1 << (nfa_nodes[next_state] - 1)
                action_params = (default_code[next_state], modifier)
                mat_entries.append((match, action, action_params))

        return mat_entries
    def generate_nfa_shadow_mat_entries(self, mat_entries_lst, defer_tree,SC_ID_tuple):
        '''
        (('001', 'h'), 'goto', ('010', 0))

        (('010', 'e'), 'goto', ('011', 1))
        (('100', 'i'), 'goto', ('101', 0))
        (('101', 's'), 'goto', ('110', 2))
        (('000', 'h'), 'goto', ('100', 0))
        (('000', 's'), 'goto', ('001', 0))
        '''
        shadow_code = SC_ID_tuple[0]
        ID_code = SC_ID_tuple[1]
        shadow_coded_lst = []
        for item in mat_entries_lst:#:
            shadow_state_ID = shadow_code[int(item[0][0],2)] 
            ID_state_ID = ID_code[int(item[2][0],2)]
            # print "reorder compress lst item", item, item[0][0], "SC",int(item[0][0],2), shadow_state_ID, "ID", item[2][0], int(item[2][0],2),ID_state_ID
            temp_item = ((shadow_state_ID,item[0][1]),item[1],(ID_state_ID,item[2][1]))
            shadow_coded_lst.append(temp_item)  
        return shadow_coded_lst
    def generate_default_shadow_mat_entry(self, mat_entries_lst, defer_tree,SC_ID_tuple):
        """
        return a default shadow mat entry  
        (('***', '*'), 'goto', ('ROOT_EXACT_CODE', 0))
        """
        shadow_code = SC_ID_tuple[0]
        ID_code = SC_ID_tuple[1]
        temp_item = mat_entries_lst[-1]
        default_entry = ((shadow_code[0],'*'),temp_item[1],(ID_code[0],0))
        return default_entry
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
    
    def generate_runtime_mat_default_entries(self, default_entry, table_id_list):
        mat_default_entries = []
        # stride_mat_default_entry = {}
        # stride_mat_default_entry["table_name"] = \
        #                 SWITCH_CONFIG["stride_mat_name"]
        # stride_mat_default_entry["default_action"]= True
        # stride_mat_default_entry["action_name"]= \
        #                 SWITCH_CONFIG["stride_action_name"]
        # stride_mat_default_entry["action_params"]= {
        #     SWITCH_CONFIG["stride_param"]: 1,
        # }
        # mat_default_entries.append(stride_mat_default_entry)
        for table_id in table_id_list:
            dfa_mat_default_entry = {}
            dfa_mat_default_entry["table_name"] = \
                    SWITCH_CONFIG["dfa_mat_name"] % table_id
            dfa_mat_default_entry["default_action"]= True
            dfa_mat_default_entry["action_name"]= \
                    SWITCH_CONFIG["goto_action_name"] % self.stride
            dfa_mat_default_entry["action_params"]= {
                SWITCH_CONFIG["next_state"]: \
                    generate_state_value_mask(default_entry[2][0], int(self.cover_code_length))[0],
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
    
    def generate_runtime_nfa_shadow_mat_entries(self, mat_entries, table_id_list):
        '''
        Generate runtime nfa mat entries (default entry included)
        
        (('011', 'h'), 'goto', ('110', 0))
        (('110', 'e'), 'goto', ('000', 1))
        (('11*', 'e'), 'goto', ('001', 2))
        (('00*', 'r'), 'goto', ('100', 4))
        (('***', 'h'), 'goto', ('111', 0))
        (('***', 's'), 'goto', ('011', 0))
        (('***', '*'), 'goto', ('010', 0))
        '''
        MAX_STRIDE = SWITCH_CONFIG['max_stride']
        runtime_nfa_shadow_mat_entries = []
        for table_id in table_id_list:
            for (match, action, action_params) in mat_entries:
                runtime_mat_entry = {}
                runtime_mat_entry["table_name"] = \
                        SWITCH_CONFIG["dfa_mat_name"] % table_id
                
                state, mask = generate_state_value_mask(match[0], int(self.cover_code_length))
                
                runtime_mat_entry["match"] = {
                    SWITCH_CONFIG["current_state"]: [state, mask]
                        
                }
                                    
                if len(match[1]) > MAX_STRIDE:
                    print "MAX_STRIDE EXCEED ERROR"
                    exit(1)
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
                    else:
                        field_name = SWITCH_CONFIG["received_char"] % idx
                        runtime_mat_entry["match"][field_name] \
                                = [0, 0]
                if len(match[1]) < MAX_STRIDE:# padding the match str field
                    for idx in range(len(match[1]),MAX_STRIDE):
                        field_name = SWITCH_CONFIG["received_char"] % idx
                        runtime_mat_entry["match"][field_name] \
                                = [0, 0]
                if action == "goto":
                    runtime_mat_entry["action_name"] = \
                            SWITCH_CONFIG["goto_action_name"] % self.stride
                    runtime_mat_entry["action_params"] = {
                        SWITCH_CONFIG["next_state"]: generate_state_value_mask(action_params[0], int(self.cover_code_length))[0],
                        SWITCH_CONFIG["modifier"]: action_params[1],
                    }
                # elif action == "accept":
                    # runtime_mat_entry["action_name"] = \
                            # SWITCH_CONFIG["accept_action_name"]
                    # runtime_mat_entry["action_params"] = {
                        # SWITCH_CONFIG["next_state"]: action_params[0],
                    # }
                runtime_nfa_shadow_mat_entries.append(runtime_mat_entry)

                
        
        return runtime_nfa_shadow_mat_entries
        
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

    def get_runtime_nfa_shadow_mat_entries(self):
        return self.runtime_nfa_shadow_mat_entries
    def get_runtime_policy_mat_entries(self):
        return self.runtime_policy_mat_entries

    def get_runtime_mat_default_entries(self):
        return self.runtime_mat_default_entries

    def get_runtime_mat_entries(self):
        return self.runtime_mat_entries

    

    def get_runtime_mat_entries_json(self):
        return json.dumps(
            self.runtime_mat_entries, indent=4, separators=(',', ': ')
        )

    def get_runtime_mat_default_entries_json(self):
        return json.dumps(
            self.runtime_mat_default_entries, indent=4, separators=(',', ': ')
        )


if __name__ == '__main__':


    # get_tree
    x = NFAMatchEntriesShadowGenerator("she | his", stride=2,table_id_list=[0,1,2])

    print("XXXXXXXXXXXXXXXXXXXXXXXXXXXx")
    print x.nfa[0]
    print x.nfa[1]
    print x.nfa[2]
    print x.defer_tree
    #[0, [1, [6]], [3], [4, [2]], [5]]
    print x.SC_ID_tuple[0]
    print x.SC_ID_tuple[1]
    print x.cover_code_length
    print len(x.nfa_mat_entries)
    for i in x.nfa_mat_entries:
        print i 
    print("***************************************")
    for i in x.nfa_shadow_mat_entries:
        print i 
    print x.nfa_shadow_default_entry

    print("***************************************")
    mat_lst = x.nfa_shadow_mat_entries

    vtable0 = VarStrideEnlarger(entries_list= x.nfa_mat_entries,nfa=x.nfa,defer_tree_lst=x.defer_tree, SC_ID_tuple=x.SC_ID_tuple)

    
    vtable0.dump_sub_table()
    print "************"

    vtable0.var_striding_simple_main_procedure(K=4)
    
    vtable0.allocate_shadowcode()
    vtable0.dump_var_stride_mat()
    vtable0.dump_var_stride_shadow_mat()
    
    print "************"
 
  