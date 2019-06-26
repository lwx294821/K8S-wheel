#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Author:Lishuwen
# @Time:2019/4/23 11:05
import os
import sys

from jinja2 import FileSystemLoader, Environment


def render_and_write(template_dir, path, out_file, content):
    """Renders the specified template into the file.
    :param out_file: the file out put path
    :param template_dir: the directory to load the template from
    :param path: the path to write the templated contents to
    :param content: the parameters to pass to the rendering engine
    """
    try:
        env = Environment(loader=FileSystemLoader(template_dir))
        template_file = os.path.basename(path)
        template = env.get_template(template_file)
        rendered_content = template.render(content)
        if rendered_content:
            write(out_file, rendered_content)
    except Exception as e:
        print(e)


def write(path, content):
    dir_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), path)
    print(dir_name)
    with open(dir_name, 'w') as output:
        output.write(content)


def main():
    render_and_write('template', 'env.j2', 'initAppEnv.yml', {'os_name': 'CentOS 7.5'})


if __name__ == "__main__":
    main()
