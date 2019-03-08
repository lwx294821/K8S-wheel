**离线安装指南**

步骤
--------------------

-   安装requirements
```shell 
# sudo pip install -r requirements.txt 
```
-  Setting
   -  支持IPV4
   - ssh key拷贝到所有节点
   - 关闭防火墙


-  配置修改和执行部署
```shell
# 移动样例文件夹
cp -rfp inventory/sample inventory/mycluster
# 定义IPS集群节点环境变量
declare -a IPS=(10.10.1.3 10.10.1.4 10.10.1.5)
# 生成资源清单 
CONFIG_FILE=inventory/mycluster/hosts.ini python3 contrib/inventory_builder/inventory.py ${IPS[@]}
# 修改k8s参数
cat inventory/mycluster/group_vars/all/all.yml
cat inventory/mycluster/group_vars/k8s-cluster/k8s-cluster.yml
# 开始部署
ansible-playbook -i inventory/mycluster/hosts.ini --become --become-user=root cluster.yml
```
