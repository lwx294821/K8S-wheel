# K8S-wheel
 1. 生成镜像和安装文件清单，以时间格式前缀 ${yyyy-MM-dd}-inventory.yaml
 
 ``` shell
 ansible-playbook local.yaml 
 ```
 2. 下载镜像和文件，基于模板配置文件，其中模板配置文件的component取${yyyy-MM-dd}-inventory.yaml
 ``` shell
 python3 mirror.py download -f config.yaml -w 1
 ```
 Depend:
  * ansible
  * python
  * DockerHub
  * GitHub
  
