#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author:Lishuwen
# @Time:2019/5/17 8:18
import json
import os

import requests


def write(path, content):
    with open(path, 'w', encoding='UTF-8') as f:
        f.write(json.dumps(content))


def read(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        result = json.load(f)
        return result


if __name__ == '__main__':
    pass

