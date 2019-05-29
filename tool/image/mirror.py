#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author:Lishuwen
# @Time:2019/5/28 8:35


import getopt
import logging
import os
import subprocess
import sys
import time

import yaml

from colorlog import ColoredLogger

AVAILABLE_COMMANDS = ['help', 'dockerfile', 'download', 'register', 'load', 'save', 'clearall']
REMOTE_REPOSITORY = ['k8s.gcr.io/', 'quay.io/', 'docker.io/', 'gcr.io/']

_boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                   '0': False, 'no': False, 'false': False, 'off': False}


def get_var_as_bool(name, default=False):
    return _boolean_states.get(name.lower(), default)


logging.setLoggerClass(ColoredLogger)
color_log = logging.getLogger(__name__)
color_log.setLevel(logging.DEBUG)


class K8SImages(object):
    def __init__(self, command=None):
        if command and command[0] in AVAILABLE_COMMANDS:
            args = options(command[1:])
            color_log.debug(args)
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
            elif command == 'load':
                self.load(args)
            elif command == 'save':
                self.save(args)
            elif command == 'register':
                self.register(args)
            elif command == 'clearall':
                self.clearall(args)
            else:
                color_log.warning("Invalid command specified.")
        except Exception as e:
            color_log.critical('Check required arguments and format:' + str(e))
            sys.exit(0)

    def show_help(self):
        help_text = '''Usage:python mirror.py download -f config.yaml

        Available commands:
        help - Display this message.
        dockerfile - Mkdir and generate Dockerfile to push github. Then you can build images on the DockerHub.
        download - Download all kubespray images from DockerHub.
        load - load all images tar to Docker.
        save - save all images to local.
        register - Read YAML to tag images for push to private registry.
        clearall - Remove all images.
        
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
        [+] colorama
         
         pip install PyYAML colorama
         
        '''

        color_log.debug(help_text)

    def dockerfile(self, args=None):
        try:
            with open(args.get('file'), 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except Exception:
            raise Exception("Cannot read %s as JSON, YAML, or CSV",
                            args.get('file'))
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
        color_log.info('Change Directory to "%s"' % root_path)

    def download(self, args=None):
        try:
            with open(args.get('file'), 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except ValueError:
            raise Exception("Cannot read %s as JSON, YAML, or CSV",
                            args.get('file'))
        repository = data.get('dockerhub')['repository']

        images = data.get('images')
        for i in images:
            if isinstance(images.get(i), dict):
                if dict(images.get(i)).get('download') and images.get(i)['download']:
                    pull = 'docker pull %s:%s' % (images.get(i)['repo'], str(images.get(i)['tag']))
                    exec_command(pull, raise_exception=True, timeout=60)
                else:
                    pull = 'docker pull %s:%s' % (repository, i)
                    if not exec_command(pull, raise_exception=True, timeout=120):
                        continue
                    old_tag = '%s:%s' % (repository, i)
                    new_tag = '%s:%s' % (hide_remote_repository(images.get(i)['repo']), str(images.get(i)['tag']))
                    tag = 'docker tag %s %s' % (old_tag, new_tag)
                    color_log.info(tag)
                    subprocess.getstatusoutput(tag)
                    untag = 'docker rmi %s' % old_tag
                    color_log.info(untag)
                    subprocess.getstatusoutput(untag)

    def save(self, args=None):
        try:
            with open(args.get("file"), 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except ValueError:
            raise Exception("Cannot read %s as JSON, YAML, or CSV",
                            args.get("file"))
        images_save_path = data.get('images_save_path')
        if not images_save_path:
            return
        if not os.path.exists(images_save_path):
            os.makedirs(images_save_path)
        images = data.get('images')
        for i in images:
            if isinstance(images.get(i), dict):
                save_name = images_save_path + i + '.' + str(images.get(i)['tag']) + '.tar'
                image_name = hide_remote_repository(images.get(i)['repo']) + ':' + str(images.get(i)['tag'])
                cmd = 'docker save -o %s %s' % (save_name, image_name)
                if not args.get('debug'):
                    exec_command(cmd, raise_exception=True, timeout=0)
                else:
                    color_log.debug(cmd)

    def load(self, args=None):
        try:
            with open(args.get('file'), 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except ValueError:
            raise Exception("Cannot read %s as JSON, YAML, or CSV",
                            args.get('file'))
        images_load_path = data.get('images_load_path')
        if not images_load_path:
            return
        images = data.get('images')
        for i in images:
            if isinstance(images.get(i), dict):
                save_name = images_load_path + i + '.' + str(images.get(i)['tag']) + '.tar'
                image_name = hide_remote_repository(images.get(i)['repo']) + ':' + str(images.get(i)['tag'])
                l = 'docker load -i %s' % save_name
                if args.get('debug'):
                    color_log.debug(l)
                    continue
                else:
                    exec_command(l, raise_exception=True, timeout=0)
                image_id = check_image_id(image_name)
                if image_id:
                    t = 'docker tag %s %s' % (image_id, image_name)
                    if args.get('debug'):
                        color_log.debug(t)
                    else:
                        exec_command(t, raise_exception=True, timeout=0)

    def clearall(self, filename=None):
        color_log.critical('remove all kubespray images')

    def register(self, args=None):
        '''
           REMOTE_REPOSITORY = ['k8s.gcr.io', 'k8s.gcr.io', 'docker.io']
        '''
        try:
            with open(args.get('file'), 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except ValueError:
            raise Exception("Cannot read %s as JSON, YAML, or CSV",
                            args.get('file'))
        host = data.get('registry')['host']
        tag = 'docker images -q |xargs docker inspect -f "{{index .RepoTags 0}}"'
        color_log.info(tag)
        (status, output) = subprocess.getstatusoutput(tag)
        arr = output.split('\n')
        if host:
            images = data.get('images')
            for i in images:
                if isinstance(images.get(i), dict):
                    repo = images.get(i)['repo']
                    flag = repo + ':' + str(images.get(i)['tag'])
                    tag = ''
                    push = ''
                    if flag in arr:
                        new_tag = '%s/%s' % (host, hide_remote_repository(flag))
                        tag = 'docker tag %s %s' % (flag, new_tag)
                        push = 'docker push %s' % new_tag
                    else:
                        if isinstance(repo, str):
                            r = repo.replace('docker.io/', '') + ':' + str(images.get(i)['tag'])
                            if r in arr:
                                new_tag = '%s/%s' % (host, r)
                                tag = 'docker tag %s %s' % (r, new_tag)
                                push = 'docker push %s' % new_tag
                    if tag and push:
                        if args.get('debug'):
                            color_log.debug(tag)
                            color_log.debug(push)
                        else:
                            color_log.info(tag)
                            color_log.info(push)
                            (status, output) = subprocess.getstatusoutput(tag)
                            color_log.info(output)
                            (status, output) = subprocess.getstatusoutput(push)
                            color_log.info(output)


def check_image_id(name=None):
    if name:
        check_id = 'docker inspect %s -f "{{ .Id }}"' % name
        (status, output) = subprocess.getstatusoutput(check_id)
        if status == 0:
            if isinstance(output, str):
                check_repo_tags = 'docker inspect %s -f "{{ .RepoTags }}"' % name
                (tag_status, tag_output) = subprocess.getstatusoutput(check_repo_tags)
                if isinstance(tag_output, str):
                    tags = tag_output.replace('[', '').replace(']', '').split(' ')
                    if name in tags:
                        return ''
                return output.replace('sha256:', '')
        else:
            color_log.error('status:%s\nimage:%s\nid:%s' % (status, name, output))
            return ''


def hide_remote_repository(arg):
    for i in REMOTE_REPOSITORY:
        if isinstance(arg, str) and arg.startswith(i):
            return arg.replace(i, '')


def options(argv):
    c = {'debug':True}
    try:
        opts, args = getopt.getopt(argv, "hf:d:", ["help", "file-from=", "debug="])

    except getopt.GetoptError as e:
        color_log.error(e)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            pass
        elif opt in ("-f", "--file-from"):
            c.update(file=arg)
        elif opt in ("-d", "--debug"):
            c.update(debug=get_var_as_bool(arg))

    return c


def exec_command(cmd, raise_exception=False, timeout=5):
    color_log.info(cmd)
    if timeout == 0:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        (stdoutdata, stderrdata) = p.communicate()
        if raise_exception and p.returncode != 0:
            color_log.error('Execute cmd:%s failed.\nstdout:%s\nstderr:%s\n' % (cmd, stdoutdata, stderrdata))
            return False
        else:
            return True
    else:
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        t_begin = time.time()
        while True:
            if p.poll() is not None:
                color_log.info('Time consume: \033[1;34;40m %ss \033[0m' % int(time.time() - t_begin))
                color_log.info(p.stdout.read().decode('UTF-8'))
                break
            seconds_passed = int(time.time() - t_begin)
            if timeout and timeout < seconds_passed:
                color_log.debug('Timeout:\033[1;34;40m %ss \033[0m,'
                                ' Seconds_passed: \033[1;33;40m %ss \033[0m' % (timeout, seconds_passed))
                p.terminate()
                return False
        return True


def main(argv=None):
    if not argv:
        argv = sys.argv[1:]
    K8SImages(argv)


if __name__ == "__main__":
    sys.exit(main())
