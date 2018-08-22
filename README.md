# zabbix_monitoring_scripts
Script for monitoring Xen/XenServer Dom0 and more


## Prerequisites
### Installing git on XenServer 6.5

~~~~
wget http://archives.fedoraproject.org/pub/archive/epel/5/x86_64/epel-release-5-4.noarch.rpm
rpm -Uvh epel-release-5-4.noarch.rpm
yum install git
rpm -ev epel-release
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
commentare la linea
~~~~
Defaults    requiretty
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
