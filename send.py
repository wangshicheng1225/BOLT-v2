#!/usr/bin/env python3
import argparse
import sys
import socket
import random
import struct

from scapy.all import sendp, send, get_if_list, get_if_hwaddr
from scapy.all import Packet
from scapy.all import Ether, IP, UDP, TCP, ICMP

def get_if():
    ifs=get_if_list()
    iface=None # "h1-eth0"
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface

def main():

    if len(sys.argv)<4:
        print('pass 3 arguments: <destination> <T/I/U> <payload>')
        exit(1)

    addr = socket.gethostbyname(sys.argv[1])
    iface = get_if()

    print("sending on interface %s to %s" % (iface, str(addr)))
    # pkt =  Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')
    #pkt = pkt /IP(dst=addr) / TCP(dport=1234, sport=random.randint(49152,65535)) / sys.argv[2]
    # pkt = pkt /IP(dst=addr, proto=244) / sys.argv[2]
    
    pkt = Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')/IP(dst=addr)
    if sys.argv[2] == 'T':
        pkt = pkt / TCP(sport = 1234, dport = 6666)
    elif sys.argv[2] == 'I':
        pkt = pkt / ICMP(code = 6)
    elif sys.argv[2] == 'U':
        pkt = pkt / UDP(sport = 1234, dport = 6666)  
    else:
        pass
    
    pkt = pkt/ sys.argv[3]
    pkt.show2()
    sendp(pkt, iface=iface, verbose=False)


if __name__ == '__main__':
    main()