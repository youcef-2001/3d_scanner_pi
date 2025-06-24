#!bin/bash

#ce script servira a setup notre raspberry automatiquement pour eviter de retaper les commandes de depart

apt-get install -y git
apt install hostapd dnsmasq netfilter-persistent iptables-persistent -y
apt install dhcpcd -y

#desactiver pour configurer
systemctl stop hostapd
systemctl stop dnsmasq
