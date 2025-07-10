# zabbix_monitoring_scripts
Script for monitoring Xen/XenServer Dom0 and more


## Prerequisites
### Installing git

#### XCP 8
~~~~
yum install git
~~~~

#### XenServer 7.2
~~~~
yum --enablerepo base install git
~~~~

#### XenServer 6.5
~~~~
wget http://archives.fedoraproject.org/pub/archive/epel/5/x86_64/epel-release-5-4.noarch.rpm
rpm -Uvh epel-release-5-4.noarch.rpm
yum install git
rpm -ev epel-release
~~~~

### Installing Zabbix agent
#### XCP 8
~~~~
rpm -Uvh https://repo.zabbix.com/zabbix/6.4/rhel/7/x86_64/zabbix-release-6.4-1.el7.noarch.rpm
rpm -Uvh http://mirror.centos.org/centos/7/os/x86_64/Packages/pcre2-10.23-2.el7.x86_64.rpm
yum clean all
yum install zabbix-agent
~~~~


#### XenServer
~~~~
rpm -Uvh http://repo.zabbix.com/zabbix/3.4/rhel/7/x86_64/zabbix-agent-3.4.9-1.el7.x86_64.rpm
~~~~

### Configuring IPtables

~~~~
vi /etc/sysconfig/iptables
~~~~
add line (before REJECT)
~~~~
# Zabbix-Agent
-A RH-Firewall-1-INPUT -m conntrack --ctstate NEW -m tcp -p tcp --dport 10050 -j ACCEPT
~~~~
restart iptables
~~~~
systemctl stop iptables
systemctl start iptables
~~~~

### Configure Zabbix Agent to use PSK (pre-shared key)
generate a PSK:
~~~~
sh -c "openssl rand -hex 32 > /etc/zabbix/zabbix_agentd.psk"
~~~~

aggiungere PSK alla configurazione dell'agente
~~~~~
vi /etc/zabbix/zabbix_agentd.conf
~~~~~
modificare:
~~~~~
Server=host.domain
TLSConnect=psk
TLSAccept=psk
TLSPSKIdentity=<unique_id>
TLSPSKFile=/etc/zabbix/zabbix_agentd.psk
~~~~~

configurare la stessa chiave/identità in zabbix

### Cloning repo
~~~~
cd /opt/
git clone https://github.com/rivoduck/zabbix_monitoring_scripts.git
~~~~

### Install scripts
~~~~
cd /opt/zabbix_monitoring_scripts
./install.sh
~~~~

nel file /etc/sudoers
commentare le linee (quelle presenti)
~~~~
Defaults    requiretty
~~~~
~~~~
Defaults    use_pty
~~~~
aggiungere la linea in fondo
~~~~
zabbix ALL=(ALL) NOPASSWD: ALL
~~~~


### Install StorCLI
for intel RAID controllers
~~~~
https://downloadcenter.intel.com/download/27654/StorCLI-Standalone-Utility
~~~~


# Docker compose monitoring scripts
Script for monitoring docker compose project

- **docker_compose_container_discovery.sh**: Monitor the state of containers by grouping them based on the Compose project
- **docker_project_discovery.sh**: Performs discovery of Compose projects
- **compose_status.sh**: Creates items with the status of Compose projects.

# Template files

The template directory contains the templates related to the scripts to be added to Zabbix:
- **zbx_topix_docker_compose_container_status.xml**: Discovery of Docker containers and Compose projects.
- **zbx_topix_docker_compose_status.xml**: Compose Project Status Monitoring.

# Configuration to be added to zabbix_agent2.conf
File **zabbix_agent.conf.d/topix_docker_compose.conf"**

UserParameter=docker.compose.container.discovery,/opt/zabbix/docker_compose_container_discovery.sh
UserParameter=docker.container.status[*],docker inspect --format '{{.State.Status}}' "$1"
UserParameter=docker.discovery.projects,/opt/zabbix/docker_project_discovery.sh
UserParameter=docker.project.status[*],/opt/zabbix/compose_status.sh "$1"
