/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;
const bit<8> TABLE_NUM = 1;

const bit<16> ETHER_HEADER_LENGTH = 14;
const bit<16> IPV4_HEADER_LENGTH = 20;
const bit<16> ICMP_HEADER_LENGTH = 8;
const bit<16> TCP_HEADER_LENGTH = 20;
const bit<16> UDP_HEADER_LENGTH = 8;

#define MAX_HOPS 29
#define IP_PROTOCOLS_ICMP 1
#define IP_PROTOCOLS_TCP 6
#define IP_PROTOCOLS_UDP 17
#define MAX_STRIDE 3
#define MARK_RECIR 1
#define MARK_DROP 2
#define MARK_FORWARD 3
#define MARK_SEND_BAK 4
/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<8>  patrn_state_t;
typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;
typedef bit<8> string_t;
typedef bit<16> state_t;
typedef bit<8> bucket_t;
typedef bit<8> bucket_counter_t;
header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header icmp_t {
    bit<8> type;
    bit<8> code;
    bit<16> icmpHdrChecksum;
    bit<16> id;
    bit<16> seq;
}

header tcp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<3>  res;
    bit<3>  ecn;
    bit<6>  ctrl;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> length_;
    bit<16> checksum;
}

header patrn_t {
    bit<8> pattern;
}

header bucket_array_t {
    bucket_t b1;
    bucket_t b2;
    bucket_t b3;
    bucket_counter_t bc1;
    bucket_counter_t bc2;
    bucket_counter_t bc3;
}





struct metadata { 
    state_t state;
    bit<8> pattern_num;
    bit<16> payload_length;
    bit<16> non_payload_length;
    bit<8> flags;// 1 recir 2 drop 3 accept 4 send to backend
    bit<8> one_pass_pattern_num;
    bit<8> stride;
    bit<1> non_first_pass;
  
    // patrn_state_t pattern_state; //for multi-pattern logic
    bucket_t b1;
    bucket_t b2;
    bucket_t b3;
    bucket_counter_t bc1;
    bucket_counter_t bc2;
    bucket_counter_t bc3;
}

struct headers {
    @name("ethernet")
    ethernet_t              ethernet;
    @name("ipv4")
    ipv4_t                  ipv4;
    @name("icmp")
    icmp_t                  icmp;
    @name("tcp")
    tcp_t                   tcp;
    @name("udp")
    udp_t                   udp;
    patrn_t[MAX_HOPS]       patrns;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser ParserImpl(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {
    
    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet); 
        // meta.non_first_pass = 1;
        meta.non_payload_length = ETHER_HEADER_LENGTH;
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        meta.non_payload_length = meta.non_payload_length + IPV4_HEADER_LENGTH;//34
        
        transition select(hdr.ipv4.protocol){
            IP_PROTOCOLS_ICMP: parse_icmp;
            IP_PROTOCOLS_TCP: parse_tcp;
            IP_PROTOCOLS_UDP: parse_udp;
            default: accept;
        }  
    }
    
    state parse_icmp {
        packet.extract(hdr.icmp);
        meta.non_payload_length = meta.non_payload_length + ICMP_HEADER_LENGTH;
        meta.pattern_num = 0;

        meta.payload_length = hdr.ipv4.totalLen + 14 - meta.non_payload_length;
        transition prepare_parse_pattern;
    }

    state parse_tcp {
        packet.extract(hdr.tcp);
        meta.non_payload_length = meta.non_payload_length + TCP_HEADER_LENGTH;
        meta.pattern_num = 0;
        meta.payload_length = hdr.ipv4.totalLen + 14 - meta.non_payload_length;
        transition prepare_parse_pattern;
    }

    state parse_udp {
        packet.extract(hdr.udp);
        meta.non_payload_length = meta.non_payload_length + UDP_HEADER_LENGTH;
        meta.pattern_num = 0;
        meta.payload_length = hdr.ipv4.totalLen + 14 - meta.non_payload_length;
        transition prepare_parse_pattern;
    }

    state prepare_parse_pattern {
        transition select(meta.payload_length) {
            0: accept;         
            default: parse_pattern;
        }
    }

    state parse_pattern{
        packet.extract(hdr.patrns.next);
        meta.pattern_num = meta.pattern_num + 1;
        meta.payload_length = meta.payload_length - 1;
        transition select(meta.payload_length) {
            0: accept;         
            default: parse_pattern;
        }
    }
}


/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control verifyChecksum(inout headers hdr, inout metadata meta) {
    apply { }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {


//********** write the root state ID into metadate from table entries ***************  
    action a_get_root_state(state_t root_state){
        meta.state = root_state;
        meta.bc1 = 0;
        meta.bc2 = 0;
        meta.bc3 = 0;
        
    }

    table t_get_root_state{
        key = {}
        actions ={
           a_get_root_state;
        }
    }
//***** k-stride DFA table ****************************************************
    action a_drop() {
        mark_to_drop(standard_metadata);
    }

    action a_nop() {}
   
    // action a_set_state_1(state_t _state, patrn_state_t modifier){
    //     meta.state = _state;
    //     hdr.patrns.pop_front(1);
    //     hdr.ipv4.totalLen = hdr.ipv4.totalLen - 1;
    //     meta.pattern_num = meta.pattern_num - 1;
    //     meta.pattern_state = meta.pattern_state | modifier;
    // }

    // action a_set_state_2(state_t _state, patrn_state_t modifier){
    //     meta.state = _state;
    //     hdr.patrns.pop_front(2);
    //     hdr.ipv4.totalLen = hdr.ipv4.totalLen - 2;
    //     meta.pattern_num = meta.pattern_num - 2;
    //     meta.pattern_state = meta.pattern_state | modifier;

    // }

    // action a_set_state_3(state_t _state, patrn_state_t modifier){
    //     meta.state = _state;
    //     hdr.patrns.pop_front(3);  
    //     hdr.ipv4.totalLen = hdr.ipv4.totalLen - 3;
    //     meta.pattern_num = meta.pattern_num - 3;
    //     meta.pattern_state = meta.pattern_state | modifier;

    // }
    
    


    // table t_DFA_match_0 {
    //     key = {
    //         hdr.patrns[0].pattern: ternary;
    //         hdr.patrns[1].pattern: ternary;

    //         // hdr.patrns[2].pattern: ternary;
    //         meta.state: ternary;
    //     }
    //     actions = {
    //         a_set_state_1;
    //         a_set_state_2;
    //         a_set_state_3;
    //         a_drop;
    //     }
    //     size = 1024;
    // }
    action a_set_state_1(state_t _state)
    {
        meta.state = _state;
        hdr.patrns.pop_front(1);  
        hdr.ipv4.totalLen = hdr.ipv4.totalLen - 1;
        meta.pattern_num = meta.pattern_num - 1;
    }
    action a_set_state_2(state_t _state)
    {
        meta.state = _state;
        hdr.patrns.pop_front(2);  
        hdr.ipv4.totalLen = hdr.ipv4.totalLen - 2;
        meta.pattern_num = meta.pattern_num - 2;
    }
    action a_set_state_3(state_t _state)
    {
        meta.state = _state;
        hdr.patrns.pop_front(3);  
        hdr.ipv4.totalLen = hdr.ipv4.totalLen - 3;
        meta.pattern_num = meta.pattern_num - 3;
    }
    action a_set_state_1_b1(state_t _state, bucket_t pattern_code)
    {
        meta.state = _state;
        hdr.patrns.pop_front(1);  
        hdr.ipv4.totalLen = hdr.ipv4.totalLen - 1;
        meta.pattern_num = meta.pattern_num - 1;
        meta.b1 = pattern_code;
        meta.bc1 = meta.bc1 + 1;
    }
    action a_set_state_1_b2(state_t _state, bucket_t pattern_code)
    {
        meta.state = _state;
        hdr.patrns.pop_front(1);  
        hdr.ipv4.totalLen = hdr.ipv4.totalLen - 1;
        meta.pattern_num = meta.pattern_num - 1;
        meta.b2 = pattern_code;
        meta.bc2 = meta.bc2 + 1;
    }
    action a_set_state_1_b3(state_t _state, bucket_t pattern_code)
    {
        meta.state = _state;
        hdr.patrns.pop_front(1);  
        hdr.ipv4.totalLen = hdr.ipv4.totalLen - 1;
        meta.pattern_num = meta.pattern_num - 1;
        meta.b3 = pattern_code;
        meta.bc3 = meta.bc3 + 1;
    }
    action a_set_state_2_b1(state_t _state, bucket_t pattern_code)
    {
        meta.state = _state;
        hdr.patrns.pop_front(2);  
        hdr.ipv4.totalLen = hdr.ipv4.totalLen - 2;
        meta.pattern_num = meta.pattern_num - 2;
        meta.b1 = pattern_code;
        meta.bc1 = meta.bc1 + 1;
    }
    action a_set_state_2_b2(state_t _state, bucket_t pattern_code)
    {
        meta.state = _state;
        hdr.patrns.pop_front(1);  
        hdr.ipv4.totalLen = hdr.ipv4.totalLen - 2;
        meta.pattern_num = meta.pattern_num - 2;
        meta.b2 = pattern_code;
        meta.bc2 = meta.bc2 + 1;
    }
    action a_set_state_2_b3(state_t _state, bucket_t pattern_code)
    {
        meta.state = _state;
        hdr.patrns.pop_front(2);  
        hdr.ipv4.totalLen = hdr.ipv4.totalLen - 2;
        meta.pattern_num = meta.pattern_num - 2;
        meta.b3 = pattern_code;
        meta.bc3 = meta.bc3 + 1;
    }
    action a_set_state_3_b1(state_t _state, bucket_t pattern_code)
    {
        meta.state = _state;
        hdr.patrns.pop_front(3);  
        hdr.ipv4.totalLen = hdr.ipv4.totalLen - 3;
        meta.pattern_num = meta.pattern_num - 3;
        meta.b1 = pattern_code;
        meta.bc1 = meta.bc1 + 1;
    }
    action a_set_state_3_b2(state_t _state, bucket_t pattern_code)
    {
        meta.state = _state;
        hdr.patrns.pop_front(3);  
        hdr.ipv4.totalLen = hdr.ipv4.totalLen - 3;
        meta.pattern_num = meta.pattern_num - 3;
        meta.b2 = pattern_code;
        meta.bc2 = meta.bc2 + 1;
    }
    action a_set_state_3_b3(state_t _state, bucket_t pattern_code)
    {
        meta.state = _state;
        hdr.patrns.pop_front(3);  
        hdr.ipv4.totalLen = hdr.ipv4.totalLen - 3;
        meta.pattern_num = meta.pattern_num - 3;
        meta.b3 = pattern_code;
        meta.bc3 = meta.bc3+ 1;
    }
    table t_DFA_match_0 {
        key = {
            hdr.patrns[0].pattern: ternary;
            hdr.patrns[1].pattern: ternary;
    
            // hdr.patrns[2].pattern: ternary;
            meta.state: ternary;
        }
        actions = {
            a_set_state_1_b1;
            a_set_state_1_b2;
            a_set_state_1_b3;
            a_set_state_2_b1;
            a_set_state_2_b2;
            a_set_state_2_b3;
            // a_set_state_3;
            a_set_state_1;
            a_set_state_2;
            a_set_state_3;
            a_drop;
            a_nop;
        }
        size = 1024;
    }    
    table t_DFA_match_1 {
        key = {
            hdr.patrns[0].pattern: ternary;
            hdr.patrns[1].pattern: ternary;
    
            // hdr.patrns[2].pattern: ternary;
            meta.state: ternary;
        }
        actions = {
            a_set_state_1_b1;
            a_set_state_1_b2;
            a_set_state_1_b3;
            a_set_state_2_b1;
            a_set_state_2_b2;
            a_set_state_2_b3;
            // a_set_state_3;
            a_set_state_1;
            a_set_state_2;
            a_set_state_3;
            a_drop;
            a_nop;
        }
        size = 1024;
    } 
    table t_DFA_match_2 {
        key = {
            hdr.patrns[0].pattern: ternary;
            hdr.patrns[1].pattern: ternary;
    
            // hdr.patrns[2].pattern: ternary;
            meta.state: ternary;
        }
        actions = {
            a_set_state_1_b1;
            a_set_state_1_b2;
            a_set_state_1_b3;
            a_set_state_2_b1;
            a_set_state_2_b2;
            a_set_state_2_b3;
            // a_set_state_3;
            a_set_state_1;
            a_set_state_2;
            a_set_state_3;
            a_drop;
            a_nop;
        }
        size = 1024;
    } 

//******Rule Table depending on meta.bucket array
    action a_mark_as_to_recirculate(){
        meta.flags = MARK_RECIR;
        meta.non_first_pass = 1;
    }

    action a_mark_as_to_drop(){
        meta.flags = MARK_DROP;
    }
    // action a_set_recir
    action a_mark_as_to_forward() {
        meta.flags = MARK_FORWARD;
    }
    action a_mark_as_to_send_backend() {
        meta.flags = MARK_SEND_BAK;
    }

    table t_pattern2rule {
        key = {
            meta.b1: ternary;
            meta.b2: ternary;
            // meta.b3: ternary;
        }
        actions = {
            a_mark_as_to_drop;
            a_mark_as_to_forward;
            a_mark_as_to_send_backend;
        }
        default_action = a_mark_as_to_send_backend;
    }
// //***** Policy Table depending on meta.Pattern_state ***********************

//     action a_set_lpm(){
//         meta.flags = 3;
//     }
//     table t_policy {
//         key = {
//             meta.pattern_state: ternary;
//         }   
//         actions = {
//             a_drop;
//             a_set_lpm;
//         }
//         size = 1024;
//     }
// ***************** send back 
    action a_send_back()
    {
        standard_metadata.egress_spec = 2;
        hdr.udp.srcPort = 1024;
        // hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        // hdr.ethernet.dstAddr = dstAddr;
        
    }
    table t_send_back {
        actions = {
            a_send_back;
        }
        default_action = a_send_back;
    }
// ***************** send to h2 
    action a_send_h2()
    {
        standard_metadata.egress_spec = 2;
        hdr.udp.srcPort = 2010;
        // hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        // hdr.ethernet.dstAddr = dstAddr;
        
    }
    table t_send_h2 {
        actions = {
            a_send_h2;
        }
        default_action = a_send_h2;
    }
//***** ipv4_lpm table ****************************************************
    action a_ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }
    
    table t_ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            a_ipv4_forward;
            a_drop;
        }
        size = 1024;
    }


//*****************************************************************************
    apply {
        if (hdr.patrns[0].isValid())
        { 
            
            if(meta.non_first_pass == 0)
            {
                t_get_root_state.apply();
            }
            
            if (meta.bc1>1 || meta.bc2>1 || meta.bc3 > 1)
            {
                a_mark_as_to_send_backend();
            }
            else {
                if (meta.pattern_num > 0)
                {
                    t_DFA_match_0.apply();
                }
                
            }

            if (meta.bc1>1 || meta.bc2>1 || meta.bc3 > 1)
            {
                a_mark_as_to_send_backend();
            }
            else {
                if (meta.pattern_num > 0)
                {
                    t_DFA_match_1.apply();
                }
            }
        
            if (meta.bc1>1 || meta.bc2>1 || meta.bc3 > 1)
            {
                a_mark_as_to_send_backend();
            }
            else  if (meta.flags != MARK_SEND_BAK)
            {
                if (meta.pattern_num > 0)
                {
                    a_mark_as_to_recirculate();
                }
                else {
                    t_pattern2rule.apply();
                }
            }
            else{
                a_mark_as_to_send_backend();
            }
            // else{
                
            // }
            

        }

        if (meta.flags == MARK_DROP)
        {
            a_drop();
        }
        if (meta.flags == MARK_FORWARD)
        {
            // t_send.apply()
            t_send_h2.apply();
        } 
        if ( meta.flags == MARK_SEND_BAK)
        {
            t_send_back.apply();
        }

        // if (meta.flags == 3)
        // {
        //      t_ipv4_lpm.apply();
        // }   
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {

    apply {  
        if (hdr.ipv4.isValid())
        {
            if (meta.flags == MARK_RECIR )
            {
                recirculate(meta);
            }       
        }     
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control computeChecksum(inout headers  hdr, inout metadata meta) {
    apply {
    update_checksum(
        hdr.ipv4.isValid(),
        { 
            hdr.ipv4.version,
            hdr.ipv4.ihl,
            hdr.ipv4.diffserv,
            hdr.ipv4.totalLen,
            hdr.ipv4.identification,
            hdr.ipv4.flags,
            hdr.ipv4.fragOffset,
            hdr.ipv4.ttl,
            hdr.ipv4.protocol,
            hdr.ipv4.srcAddr,
            hdr.ipv4.dstAddr 
        },
        hdr.ipv4.hdrChecksum,
        HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control DeparserImpl(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/
V1Switch(ParserImpl(), verifyChecksum(), MyIngress(), MyEgress(), computeChecksum(), DeparserImpl()) main;
