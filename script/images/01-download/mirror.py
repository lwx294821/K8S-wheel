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

import requests
import yaml


AVAILABLE_COMMANDS = ['help', 'dockerfile', 'download', 'register', 'load', 'save', 'clearall']
EXTERNAL_REPO = ['k8s.gcr.io/', 'quay.io/',  'gcr.io/']
INTERNAL_REPO = ['docker.io/', 'index.alauda.cn/']

RESULT_INFO = []
FAILURE_INFO = []

_boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
                   '0': False, 'no': False, 'false': False, 'off': False}


def get_var_as_bool(name, default=False):
    return _boolean_states.get(name.lower(), default)


BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

# The background is set with 40 plus the number of the color, and the foreground with 30

# These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"


def formatter_message(message, use_color=True):
    if use_color:
        message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message


COLORS = {
    'WARNING': YELLOW,
    'INFO': GREEN,
    'DEBUG': CYAN,
    'CRITICAL': RED,
    'ERROR': MAGENTA
}


# Custom logger class with multiple destinations
class ColoredLogger(logging.Logger):
    FORMAT = "[%(asctime)s]-[$BOLD%(name)-10s$RESET] ($BOLD%(filename)s$RESET:%(lineno)d)" \
             " [%(levelname)-18s]  %(message)s "
    COLOR_FORMAT = formatter_message(FORMAT, True)

    def __init__(self, name):
        logging.Logger.__init__(self, name, logging.DEBUG)

        color_formatter = ColoredFormatter(self.COLOR_FORMAT)

        console = logging.StreamHandler()
        console.setFormatter(color_formatter)

        self.addHandler(console)


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


logging.setLoggerClass(ColoredLogger)
color_log = logging.getLogger(__name__)
color_log.setLevel(logging.DEBUG)


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
        
        DockerHub+Github
        grep -r -E  '\<FROM k8s.gcr.io|\<FROM gcr.io|\<FROM quay.io' ./dockerfile/
        
        
        Available commands:
        help - Display this message.
        dockerfile - Mkdir and generate Dockerfile to push github. Then you can build images on the DockerHub.
        download - Download all kubespray images from DockerHub.
        load - load all images tar to Docker.
        save - save all images to local.
        register - Read YAML to tag images for push to private registry.
        clearall - Remove all images.
        
        Advanced usage:
        -f --file-from config.yaml
        -w --way 0,1,true,false
        -d True 

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
        except Exception as e:
            color_log.error(e)
            raise Exception("Cannot read %s as JSON, YAML, or CSV" % args.get('file'))
        root_path = data.get('dockerfile')['root_path']
        component = data.get('component')
        for i in component:
            item = dict(component.get(i))
            if item.get("container"):
                repo = item['repo']
                tag = item['tag']
                if args.get('debug'):
                    RESULT_INFO.append({'repo': repo, 'tag': tag})
                    continue
                save = root_path + '/' + i + '/Dockerfile'
                if not os.path.exists(root_path + '/' + i):
                    os.makedirs(root_path + '/' + i)
                try:
                    with open(save, "w", encoding="UTF-8") as f:
                        f.write('FROM ' + repo + ':' + str(tag))
                    RESULT_INFO.append({'repo': repo, 'tag': tag})
                except Exception:
                    FAILURE_INFO.append({'repo': repo, 'tag': tag})
        if args.get('debug'):
            color_log.debug(
                'Change Directory to \033[1;33;40m %s \033[0m,Dockerfile:'
                'count= \033[1;33;40m %s \033[0m ,list= %s' % (root_path, len(RESULT_INFO), RESULT_INFO))
        else:
            color_log.info(
                'Change Directory to \033[1;33;40m %s \033[0m,Dockerfile:\r\n'
                '\033[1;36;40m success:\033[0m count=\033[1;33;40m %s \033[0m,list=%s,\r\n'
                '\033[1;36;40m failure:\033[0m count=\033[1;33;40m %s \033[0m,list=%s'
                % (root_path, len(RESULT_INFO), RESULT_INFO, len(FAILURE_INFO), FAILURE_INFO))

    def download(self, args=None):
        try:
            with open(args.get('file'), 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except ValueError:
            raise Exception("Cannot read %s as JSON, YAML, or CSV",
                            args.get('file'))
        repository = data.get('dockerhub')['repository']

        component = data.get('component')
        for i in component:
            if isinstance(component.get(i), dict):
                item = dict(component.get(i))
                container = item.get('container')
                file = item.get('file')
                if container:
                    if str(item['repo']).split('/')[0]+'/' in INTERNAL_REPO:
                        pull = 'docker pull %s:%s' % (item['repo'], str(item['tag']))
                        if args.get('debug'):
                            color_log.debug(pull)
                            RESULT_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                        else:
                            r = exec_command(pull, raise_exception=True, timeout=30)
                            if r:
                                RESULT_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                            else:
                                FAILURE_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                    else:
                        pull = 'docker pull %s:%s' % (repository, i)
                        if args.get('debug'):
                            color_log.debug(pull)
                            RESULT_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                        else:
                            if not exec_command(pull, raise_exception=True, timeout=30):
                                FAILURE_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                                continue
                            else:
                                RESULT_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                        old_tag = '%s:%s' % (repository, i)
                        new_tag = '%s:%s' % (hide_remote_repository(item['repo']), str(item['tag']))
                        tag = 'docker tag %s %s' % (old_tag, new_tag)
                        if not args.get('debug'):
                            (code, output) = subprocess.getstatusoutput(tag)
                        untag = 'docker rmi %s' % old_tag
                        if not args.get('debug'):
                            subprocess.getstatusoutput(untag)

                way = args.get("way")
                if way and file:
                    dest = item.get('dest')
                    url = item.get('url')
                    if args.get('debug'):
                        RESULT_INFO.append({'file': url, 'dest': dest})
                        continue
                    if filefromuri(url, 100, dest):
                        RESULT_INFO.append({'file': url, 'dest': dest})
                    else:
                        FAILURE_INFO.append({'file': url, 'dest': dest})
        color_log.info(
            'Download Container and File:\r\n'
            '\033[1;36;40m success:\033[0m count=\033[1;33;40m %s \033[0m,list=%s,\r\n'
            '\033[1;36;40m failure:\033[0m count=\033[1;33;40m %s \033[0m,list=%s'
            % (len(RESULT_INFO), RESULT_INFO, len(FAILURE_INFO), FAILURE_INFO))

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
        component = data.get('component')
        for i in component:
            item = component.get(i)
            if isinstance(item, dict):
                if item.get('container'):
                    save_name = images_save_path + i + '.' + str(item['tag']) + '.tar'
                    color_log.debug(hide_remote_repository(item['repo']))
                    image_name = hide_remote_repository(item['repo']) + ':' + str(item['tag'])
                    cmd = 'docker save -o %s %s' % (save_name, image_name)
                    if not args.get('debug'):
                        r = exec_command(cmd, raise_exception=True, timeout=0)
                        if r:
                            RESULT_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                        else:
                            FAILURE_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                    else:
                        color_log.debug(cmd)
                        RESULT_INFO.append({'repo': item['repo'], 'tag': item['tag']})
        color_log.info('Save Contaiers Result:\r\n '
                       '\033[1;36;40m success:\033[0m count=\033[1;33;40m %s \033[0m,list=%s,\r\n'
                       '\033[1;36;40m failure:\033[0m count=\033[1;33;40m %s \033[0m,list=%s'
                       % (len(RESULT_INFO), RESULT_INFO, len(FAILURE_INFO), FAILURE_INFO))

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
        component = data.get('component')
        for i in component:
            item = component.get(i)
            if isinstance(item, dict):
                if item.get('container'):
                    save_name = images_load_path + i + '.' + str(item['tag']) + '.tar'
                    image_name = hide_remote_repository(item['repo']) + ':' + str(item['tag'])
                    l = 'docker load -i %s' % save_name
                    if args.get('debug'):
                        color_log.debug(l)
                        RESULT_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                    else:
                        if not exec_command(l, raise_exception=True, timeout=0):
                            FAILURE_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                        else:
                            RESULT_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                    if args.get('debug'):
                        continue
                    image_id = check_image_id(image_name)
                    if image_id:
                        t = 'docker tag %s %s' % (image_id, image_name)
                        if args.get('debug'):
                            color_log.debug(t)
                        else:
                            exec_command(t, raise_exception=True, timeout=0)
        color_log.info('Load Contaiers Result:\r\n'
                       '\033[1;36;40m success:\033[0m  count=\033[1;33;40m %s \033[0m,list=%s,\r\n'
                       '\033[1;36;40m failure:\033[0m  count=\033[1;33;40m %s \033[0m,list=%s'
                       % (len(RESULT_INFO), RESULT_INFO, len(FAILURE_INFO), FAILURE_INFO))

    def clearall(self, args=None):
        color_log.critical('remove all kubespray images and cannot undo!!!')
        try:
            with open(args.get('file'), 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except ValueError:
            raise Exception("Cannot read %s as JSON, YAML, or CSV",
                            args.get('file'))
        component = data.get('component')
        for i in component:
            item = component.get(i)
            if isinstance(item, dict):
                if item.get('container'):
                    image_name = hide_remote_repository(item['repo']) + ':' + str(item['tag'])
                    cmd = 'docker inspect  %s -f "{{ .Id }}" | sed "s/sha256://g" | xargs docker rmi -f ' % image_name
                    if args.get('debug'):
                        color_log.debug(cmd)
                        RESULT_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                    else:
                        color_log.info(cmd)
                        (status, output) = subprocess.getstatusoutput(cmd)
                        if status == 0:
                            RESULT_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                        else:
                            FAILURE_INFO.append({'repo': item['repo'], 'tag': item['tag']})
        color_log.info('Clear Containers Result:\r\n' 
                       '\033[1;36;40m success:\033[0m  count=\033[1;33;40m %s \033[0m,list=%s,\r\n'
                       '\033[1;36;40m failure:\033[0m  count=\033[1;33;40m %s \033[0m,list=%s'
                       % (len(RESULT_INFO), RESULT_INFO, len(FAILURE_INFO), FAILURE_INFO))

    def register(self, args=None):
        '''
           REMOTE_REPOSITORY = ['k8s.gcr.io', 'k8s.gcr.io', 'docker.io']
        '''
        try:
            with open(args.get('file'), 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except ValueError:
            raise Exception("Cannot read %s as JSON, YAML, or CSV" % args.get('file'))
        host = data.get('registry')['host']
        if host:
            component = data.get('component')
            for i in component:
                item = component.get(i)
                if isinstance(item, dict):
                    if item.get('container'):
                        repo = item['repo']
                        flag = hide_remote_repository(repo + ':' + str(item['tag']))
                        tag = ''
                        push = ''
                        if flag:
                            new_tag = '%s/%s' % (host, flag)
                            tag = 'docker tag %s %s' % (flag, new_tag)
                            push = 'docker push %s' % new_tag
                        if tag and push:
                            if args.get('debug'):
                                color_log.debug(tag)
                                color_log.debug(push)
                                RESULT_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                            else:
                                (st, ot) = subprocess.getstatusoutput(tag)
                                color_log.info(ot)
                                (sp, op) = subprocess.getstatusoutput(push)
                                color_log.info(op)
                                if sp == 0:
                                    RESULT_INFO.append({'repo': item['repo'], 'tag': item['tag']})
                                else:
                                    FAILURE_INFO.append({'repo': item['repo'], 'tag': item['tag']})
            color_log.info(
                'Register Containers Result:\r\n'
                '\033[1;36;40m success:\033[0m  count=\033[1;33;40m %s \033[0m,list=%s,\r\n'
                '\033[1;36;40m failure:\033[0m  count=\033[1;33;40m %s \033[0m,list=%s'
                % (len(RESULT_INFO), RESULT_INFO, len(FAILURE_INFO), FAILURE_INFO))


def check_image_tag(name=None):
    cmd = 'docker inspect  %s -f "{{ .RepoTags }}"' % hide_remote_repository(name)
    color_log.info(cmd)
    (status, output) = subprocess.getstatusoutput(cmd)
    if isinstance(output, str):
        tags = output.replace('[', '').replace(']', '').split(' ')
        if hide_remote_repository(name) in tags:
            return True
    return False


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
                    # 镜像tag满足格式规范，不需重新打tag
                    if name in tags:
                        return ''
                return output.replace('sha256:', '')
        else:
            return ''


def hide_remote_repository(arg):
    if isinstance(arg, str):
        for i in EXTERNAL_REPO:
            if not arg.startswith(i):
                continue
            else:
                return arg.replace(i, '')
        for i in INTERNAL_REPO:
            if not arg.startswith(i):
                continue
            else:
                return arg.replace(i, '')
    return None


def filefromuri(url, timeout, filename):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    try:
        r = requests.get(url, timeout=timeout)
        with open(filename, "wb") as code:
            code.write(r.content)
        return True
    except Exception:
        return False


def options(argv):
    c = {'debug': False}
    try:
        opts, args = getopt.getopt(argv, "hf:d:w:", ["help", "file-from=", "debug=", "way="])

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
        elif opt in ("-w", "--way"):
            c.update(way=get_var_as_bool(arg))

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
