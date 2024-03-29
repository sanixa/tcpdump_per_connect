#!/usr/bin/python3
from __future__ import print_function
import subprocess
import multiprocessing as mp
import os

import time

def tcpdump(dic, name, dev):
    s = 'sudo tcpdump -i ' + dev + ' -G 5 -w ./log/' + name + '-%b-%d-%Y-%H-%M-%S \''
    for item in dic[name]:
        s = s + 'port ' + str(item) + ' or '
    s = s[:-5] + '\''
    print(s)
    os.system(s)

def tcp_update(proc, dic, new, changed, delete, dev):
    if not new:
        pass
    else:
        for item in new:
            proc[str(item)] = mp.Process(target=tcpdump, args=(dic, item, dev))
            proc[str(item)].start()

    if not changed:
        pass
    else:
        for item in changed:
            proc[str(item)].terminate()
            proc[str(item)].join()
            del proc[str(item)]
            proc[str(item)] = mp.Process(target=tcpdump, args=(dic, item, dev))
            proc[str(item)].start()

    if not delete:
        pass
    else:
        for item in delete:
            proc[str(item)].terminate()
            proc[str(item)].join()
            del proc[str(item)]


def data_update(dic, new, changed, delete):
    t = subprocess.check_output('sudo netstat -atpn |grep ESTABLISHED | awk \'{print $4,$7;}\'', shell=True)
    if t == b'':
        return dic, [], [], []
    t = t[:-1].decode('utf-8').split("\n") #ip:port PID/program_name

    new = []      #to create new tcpdump process
    changed = []  #update list for changed program_name to kill old process and create new
    delete = []   #to kill old process
    curr_dic = {} #compare to dic and help to find which port is not needed to trace
    for i in t:
        temp = i.split(" ")
        port = temp[0][temp[0].find(':')+1:]
        program_name = temp[1][temp[1].find('/')+1:]
        if program_name not in curr_dic:
            curr_dic[program_name] = list()
            curr_dic[program_name].append(port)
        else:
            curr_dic[program_name].append(port)

    print('-------------------------')
    print('ori dic ==> program map to port: ')
    for k,v in dic.items():
        print(k,v)

    for k,l in curr_dic.items():
        for v in l:
            if k in curr_dic and k not in dic and k not in new: # new program_name create connection
                new.append(k)
            if k in curr_dic and k in dic and v in curr_dic[k] and v not in dic[k] and k not in changed: # program_name have new port
                changed.append(k)

    for k,l in dic.items():
        for v in l:
            if k in dic and k not in curr_dic and k not in delete: # this program_name no longer to create connection
                delete.append(k)
            if k in curr_dic and k in dic and v in dic[k] and v not in curr_dic[k] and k not in changed: #this port is no longer to be used
                changed.append(k)

    print('new dic ==> program map to port: ')
    for k,v in curr_dic.items():
        print(k,v)
    print('new = ' , new[:])
    print('changed = ' , changed[:])
    print('delete = ' , delete[:])
    print('----------------------------------------')
    return curr_dic, new, changed, delete

def main(dev):
    
    dic = {}      #store program_name map to port
    proc = {}     #store program_name map to process
    new = []      #need to create new tcpdump process
    changed = []  #update list for changed program_name to kill old process and create new
    delete = []   #need to kill old process

    #p1 = mp.Process(target=data_update, args(dic, new, changed, delete))
    while True:
        dic, new, changed, delete = data_update(dic, new, changed, delete)
        tcp_update(proc, dic, new, changed, delete, dev)
        time.sleep(5)

if __name__ == '__main__':
    main(dev='ens33')
