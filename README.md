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

### Cloning repo
~~~~
cd /opt/
git clone https://github.com/rivoduck/zabbix_monitoring_scripts.git
~~~~
