#!bin/bash

#ce script servira a setup notre raspberry automatiquement pour eviter de retaper les commandes de depart
apt-get install -y git hostapd dnsmasq netfilter-persistent iptables-persistent dhcpcd 
#desactiver pour configurer
systemctl stop hostapd
systemctl stop dnsmasq

apt install -y libi2c-dev i2c-tools libcamera-apps libcamera-dev libi2c0 libcap-dev
# Installer les dépendances Python 
apt install -y python3 python3-pip python3-venv
cd ../
# Créer un environnement virtuel Python
python3 -m venv venv
# Activer l'environnement virtuel
source venv/bin/activate
# Installer les dépendances Python
pip install -r ./env-setup/requirements.txt







#================================================================
#Lancer le setup Reseaux
./env-setup/setup_network.sh


#================================================================
# Activer I2C dans /boot/config.txt
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
    echo "dtparam=i2c_arm=on" >> /boot/config.txt
fi
# Charger le module i2c-dev au démarrage
if ! grep -q "^i2c-dev" /etc/modules; then
    echo "i2c-dev" >> /etc/modules
fi
# Charger le module immédiatement
modprobe i2c-dev