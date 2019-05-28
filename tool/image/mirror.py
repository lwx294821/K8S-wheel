#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author:Lishuwen
# @Time:2019/5/28 8:35


import getopt
import os
import subprocess
import sys

import yaml

AVAILABLE_COMMANDS = ['help', 'dockerfile', 'download', 'register']


class K8SImages(object):
    def __init__(self, command=None):
        if command and command[0] in AVAILABLE_COMMANDS:
            args = options(command[1:])
            self.parse_command(command[0], args)

        else:
            self.show_help()

    def parse_command(self, command, args=None):
        try:
            if command == 'help':
                self.show_help()
            elif command == 'dockerfile':
                self.dockerfile(args)
            elif command == 'download':
                self.download(args)
            elif command == 'build':
                self.build(args)
            elif command == 'register':
                self.register(args)
            else:
                raise Exception("Invalid command specified.")
        except Exception as e:
            print('Check required arguments and format:', e)
            sys.exit(0)

    def show_help(self):
        help_text = '''Usage:python mirror.py download -f config.yaml

        Available commands:
        help - Display this message
        dockerfile - Mkdir and generate Dockerfile to push github. Then you can build images on the DockerHub.
        download - Download all kubespray images from DockerHub
        build - According to the dockerfile which created by dockerfile command to build images.
        register - Read YAML to tag images for push to private registry.
        
        Advanced usage:
        Not Support Now.

        Configurable env vars:
        DEBUG                   Enable debug printing. Default: True
        
        Requirements:
        [*] et-xmlfile==1.0.1
        [*] jdcal==1.4.1
        [*] Jinja2==2.10
        [*] MarkupSafe==1.1.1
        [*] openpyxl==2.6.2
        [*] psutil==5.6.2
        [+] PyYAML==5.1
         
         pip install PyYAML
         
        '''
        print(help_text)

    def dockerfile(self, filename=None):
        try:
            with open(filename, 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except Exception:
            raise Exception("Cannot read %s as JSON, YAML, or CSV",
                            filename)
        root_path = data.get('dockerfile')['root_path']
        images = data.get('images')
        for i in images:
            repo = images.get(i)['repo']
            tag = images.get(i)['tag']
            save = root_path + '/' + i + '/Dockerfile'
            if not os.path.exists(root_path + '/' + i):
                os.makedirs(root_path + '/' + i)
            with open(save, "w", encoding="UTF-8") as f:
                f.write('FROM ' + repo + ':' + str(tag))
        print('Change Directory to "%s"' % root_path)

    def download(self, filename=None):
        try:
            with open(filename, 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except ValueError:
            raise Exception("Cannot read %s as JSON, YAML, or CSV",
                            filename)
        repository = data.get('dockerhub')['repository']
        images = data.get('images')
        for i in images:
            if isinstance(images.get(i), dict):
                if dict(images.get(i)).get('download') and images.get(i)['download']:
                    pull = 'docker pull %s:%s' % (images.get(i)['repo'], str(images.get(i)['tag']))
                    print(pull)
                    (status, output) = subprocess.getstatusoutput(pull)
                    print(status, output)
                else:
                    pull = 'docker pull %s:%s' % (repository, i)
                    print(pull)
                    (status, output) = subprocess.getstatusoutput(pull)
                    print(status, output)

                    old_tag = '%s:%s' % (repository, i)
                    new_tag = '%s:%s' % (images.get(i)['repo'], str(images.get(i)['tag']))
                    tag = 'docker tag %s %s' % (old_tag, new_tag)
                    print(tag)
                    (status, output) = subprocess.getstatusoutput(tag)
                    print(status, output)

                    untag = 'docker rmi %s' % old_tag
                    print(untag)
                    (status, output) = subprocess.getstatusoutput(untag)
                    print(status, output)

    def build(self, filename=None):
        try:
            with open(filename, 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except ValueError:
            raise Exception("Cannot read %s as JSON, YAML, or CSV",
                            filename)
        root_path = data.get('dockerfile')['root_path']
        images = data.get('images')
        for i in images:
            path = root_path + i + '/Dockerfile'
            b = 'docker build -f %s  .' % path
            pout = subprocess.Popen(b, shell=True)
            for line in pout:
                print(line.strip().decode('utf-8'))


def options(argv):
    c = ''
    try:
        opts, args = getopt.getopt(argv, "hf:", ["help", "file-from="])

    except getopt.GetoptError as e:
        print(e)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            pass
        elif opt in ("-f", "--file-from"):
            c = arg
    return c


def main(argv=None):
    if not argv:
        argv = sys.argv[1:]
    K8SImages(argv)


if __name__ == "__main__":
    sys.exit(main())
