#!bin/bash

#ce script servira a setup notre raspberry automatiquement pour eviter de retaper les commandes de depart

apt-get install -y git
apt install -y hostapd dnsmasq netfilter-persistent iptables-persistent dhcpcd 

#desactiver pour configurer
systemctl stop hostapd
systemctl stop dnsmasq
#     cv2     i2c-tools   libcamera-apps  libcamera-dev
apt install -y libi2c-dev i2c-tools libcamera-apps libcamera-dev 
#   libi2c0    libcap-dev
apt install -y libi2c0 libcap-dev
# Pour installer la dépendance cv2 (OpenCV pour Python), utilisez pip :
apt install -y python3-pip python3-dev python3-setuptools python3-wheel
pip3 install --upgrade pip
pip3 install -r requirements.txt


# activer le i2c

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