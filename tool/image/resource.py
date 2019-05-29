#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author:Lishuwen
# @Time:2019/5/17 10:47


import os
import sys

import time
import psutil

# https://www.cnblogs.com/weihengblog/p/9656257.html
from util.file import *

time.sleep(3)
line_num = 1


# function of Get CPU State;
def cpu(interval=1):
    return dict(percent=str(psutil.cpu_percent(interval)) + "%", logicalcount=psutil.cpu_count(),
                physicalcount=psutil.cpu_count(logical=False))


# function of Get Memory
def memo():
    phymem = psutil.virtual_memory()
    return {'percent': str(phymem.percent) + '%', 'used': str(int(phymem.used / 1024 / 1024)) + "M",
            'total': str(int(phymem.total / 1024 / 1024)) + "M"}


def bytes2human(n):
    """
    >>> bytes2human(10000)
    '9.8 K'
    >>> bytes2human(100001221)
    '95.4 M'
    """
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.2f %s' % (value, s)
    return '%.2f B' % n


def poll(interval):
    """Retrieve raw stats within an interval window."""
    tot_before = psutil.net_io_counters()
    pnic_before = psutil.net_io_counters(pernic=True)
    # sleep some time
    time.sleep(interval)
    tot_after = psutil.net_io_counters()
    pnic_after = psutil.net_io_counters(pernic=True)
    # get cpu state
    cpu_state = cpu(interval)
    # get memory
    memory_state = memo()
    return tot_before, tot_after, pnic_before, pnic_after, cpu_state, memory_state


def refresh_window(tot_before, tot_after, pnic_before, pnic_after, cpu_state, memory_state):
    context = {}
    print("-" * 50)
    print('OSType:', sys.platform)
    context.update(ostype=sys.platform)
    # print current time #cpu  #memory
    print('Time', time.asctime())
    context.update(time=time.asctime())
    print('CPU', cpu_state)
    context.update(cpu=cpu_state)
    print('Memory', memory_state)
    context.update(memo=memory_state)
    print("-" * 50)
    # totals
    templnetwork = "%-15s %15s %15s"
    print(templnetwork % ("Network", "Sent", "Received"))
    print(templnetwork % ("Bytes", bytes2human(tot_after.bytes_sent), bytes2human(tot_after.bytes_recv)))
    print(templnetwork % ("Packets", tot_after.packets_sent, tot_after.packets_recv))
    network = {}
    network.update(bytes={'send': bytes2human(tot_after.bytes_sent), 'recv': bytes2human(tot_after.bytes_recv)})
    network.update(packets={'send': tot_after.packets_sent, 'recv': tot_after.packets_recv})
    context.update(network=network)
    # per-network interface details: let's sort network interfaces so
    # that the ones which generated more traffic are shown first
    print("-" * 50)
    nic_names = pnic_after.keys()
    # nic_names.sort(key=lambda x: sum(pnic_after[x]), reverse=True)
    nic = []
    for name in nic_names:
        stats_before = pnic_before[name]
        stats_after = pnic_after[name]
        templ = "%-15s %15s %15s"
        print(templ % (name, "TOTAL", "PER-SEC"))
        print(templ % (
            "bytes-sent",
            bytes2human(stats_after.bytes_sent),
            bytes2human(stats_after.bytes_sent - stats_before.bytes_sent) + '/s',
        ))

        print(templ % (
            "bytes-recv",
            bytes2human(stats_after.bytes_recv),
            bytes2human(stats_after.bytes_recv - stats_before.bytes_recv) + '/s',
        ))
        print(templ % (
            "pkts-sent",
            stats_after.packets_sent,
            stats_after.packets_sent - stats_before.packets_sent,
        ))
        print(templ % (
            "pkts-recv",
            stats_after.packets_recv,
            stats_after.packets_recv - stats_before.packets_recv,
        ))
        print("-" * 50)

        n = {}
        n.update(bytesend={'total': bytes2human(stats_after.bytes_sent),
                           'persec': bytes2human(stats_after.bytes_sent - stats_before.bytes_sent)})
        n.update(byterecv={'total': bytes2human(stats_after.bytes_recv),
                           'persec': bytes2human(stats_after.bytes_recv - stats_before.bytes_recv)})

        n.update(pktssend={'total': stats_after.packets_sent,
                           'persec': stats_after.packets_sent - stats_before.packets_sent})
        n.update(pktsrecv={'total': stats_after.packets_recv,
                           'persec': stats_after.packets_recv - stats_before.packets_recv})
        nic.append({'name': name, 'value': n})

    context.update(nic=nic)
    write("resource.json", context)


def monitor(interval=1):
    try:
        args = poll(interval)
        refresh_window(*args)
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == '__main__':
    monitor(1)
