#! /bin/bash

# Author: Youcef BALEH

#Copied from  Github
# Email: pankaj.shelare@gmail.com

# This script is modified to apply to my need and it was the script created by pankaj enhanced using the thoughts of the below given link reference.
# REFERENCE: https://lb.raspberrypi.org/forums/viewtopic.php?t=211542
# Although, the script is created using the thought process of the above link,
# there are many enhancements made to solve BUGS (occurred during evaluation and testing phase) 
# and to promote many advanced features to automate and setup the single WiFi chip of
# Raspberry Pi as an Access Point(AP) and Station(STA) Network both (and hence, supporting
# HOTSPOT feature in Raspberry Pi using the execution of this script).

apIpDefault="192.168.13.1"
apDhcpRangeDefault="192.168.13.2,192.168.13.254,24h"
apSetupIptablesMasqueradeDefault="iptables -t nat -A POSTROUTING -s 192.168.13.0/24 ! -d 192.168.13.0/24 -j MASQUERADE"
apCountryCodeDefault="FR"
apChannelDefault="1"

apIp="$apIpDefault"
apDhcpRange="$apDhcpRangeDefault"
apSetupIptablesMasquerade="$apSetupIptablesMasqueradeDefault"
apCountryCode="$apCountryCodeDefault"
apChannel="$apChannelDefault"
apSsid="Scanner_3D"
apPassphrase="12345678*"
apPasswordConfig=""

workDir="/home/pi"
installDir="$workDir/network-setup"
logDir="$installDir/log"
execDir="$installDir/bin"
downloadDir="$installDir/downloads"
netStartFile="$execDir/netStart.sh"
netStopFile="$execDir/netStop.sh"
netLogFile="$logDir/network.log"
netStopServiceFile="/etc/systemd/system/netStop.service"
netStationConfigFile="/etc/network/interfaces.d/station"
netShutdownFlagFile="$logDir/netShutdownFlag"
shutdownRecoveryFile="$execDir/shutdownRecovery.sh"
rcLocalLogFile="$logDir/rc.local.log"

rebootFlag=true
wlanInterfaceNameValid=true

# Defined common WLAN and AP Interface names here as in the recent and future versions of Debian based OS 
# may change the Networking Interface name.
wlanInterfaceNameDefault="wlan0"
wlanInterfaceName="$wlanInterfaceNameDefault"
apInterfaceName="uap0"
hostNameDefault="raspberrypi"
hostName="$hostNameDefault"

# FIX: for https://github.com/idev1/rpihotspot/issues/12#issuecomment-605552834
if [ ! -z "$( hostname )" ]; then 
    hostName="$( hostname )"
fi

echo "[INFO]: Hostname is: $hostName"

function setWlanDetails()
{
    # Set Country Code:
    wlanCountryCode="$( cat /etc/wpa_supplicant/wpa_supplicant.conf | grep -i 'country=' | awk -F '=' '{print $2}' )"
    # FIX: #12, trimming spaces and carriage return for WLAN Country code if there are any.
    wlanCountryCode="$( echo $wlanCountryCode | tr -d '\r' )"
    if [[ ! -z "${wlanCountryCode}" && \
	("${countryCodeArray[@]}" =~ "${wlanCountryCode}") ]]; then
	    apCountryCode="$wlanCountryCode"
	    apCountryCodeDefault="$wlanCountryCode"
    fi

    # Read WiFi Station(${wlanInterfaceName}) IP, Mask and Broadcast addresses:
    read wlanIpAddr wlanIpMask wlanIpCast <<< $( echo $( ifconfig ${wlanInterfaceName} | grep 'inet ' ) | awk -F " " '{print $2" "$4" "$6}' )

    # Set AP Channel:
    wlanChannel="$( iwlist ${wlanInterfaceName} channel | grep 'Current Frequency:' | awk -F '(' '{gsub("\)", "", $2); print $2}' | awk -F ' ' '{print $2}' )"
    if [ ! -z "${wlanChannel}" ]; then
	    apChannel="$wlanChannel"
	    apChannelDefault="$wlanChannel"
    fi
}

setWlanDetails

# REFERENCE: https://en.wikipedia.org/wiki/Private_network#Private_IPv4_addresses
# Visit above site to know more about Reserved Private IP Address for LAN/WLAN communication.
function validIpAddress()
{
    local  ip=$1
    local  status=1
    if [[ $ip =~ ^(10|172|192)\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        
        IFS='.' read ipi1 ipi2 ipi3 ipi4 <<< "$ip"
        IFS='.' read -r -a wlanIpMaskArr <<< "$wlanIpMask"
        IFS='.' read -r -a wlanIpAddrArr <<< "$wlanIpAddr"
        
        wlanIpStartWith=""
        wlanIpStartWithCount=0
        
        for i in ${!wlanIpMaskArr[@]}; do
	        mskVal=${wlanIpMaskArr[$i]}
            if [ $mskVal == 255 ]; then
                if [ -z "$wlanIpStartWith" ]; then
                    wlanIpStartWith="${wlanIpAddrArr[$i]}"
                else
                    wlanIpStartWith="$wlanIpStartWith.${wlanIpAddrArr[$i]}"
                fi
                wlanIpStartWithCount=$((wlanIpStartWithCount+1))
            fi
        done
        
        wlanIpStartWith="$wlanIpStartWith."
        
        case $ipi1 in
        10) 
            [[ ( $ip != $wlanIpAddr && ! $ip =~ ${wlanIpStartWith}* ) && \
                ((${#ipi2} -eq 1 && ${ipi2} -le 255) || (${#ipi2} -gt 1 && "${ipi2}" != 0* && ${ipi2} -le 255)) && \
                ((${#ipi3} -eq 1 && ${ipi3} -le 255) || (${#ipi3} -gt 1 && "${ipi3}" != 0* && ${ipi3} -le 255)) && \
                ((${#ipi4} -eq 1 && ${ipi4} -le 255) || (${#ipi4} -gt 1 && "${ipi4}" != 0* && ${ipi4} -le 255))
             ]]
            status=$?
        ;;
        172) 
            [[  ( $ip != $wlanIpAddr && ! $ip =~ ${wlanIpStartWith}* ) && \
                ("${ipi2}" != 0* && ${ipi2} -ge 16 && ${ipi2} -le 31) && \
                ((${#ipi3} -eq 1 && ${ipi3} -le 255) || (${#ipi3} -gt 1 && "${ipi3}" != 0* && ${ipi3} -le 255)) && \
                ((${#ipi4} -eq 1 && ${ipi4} -le 255) || (${#ipi4} -gt 1 && "${ipi4}" != 0* && ${ipi4} -le 255))
             ]]
            status=$?
        ;;
        192) 
            [[  ( $ip != $wlanIpAddr && ! $ip =~ ${wlanIpStartWith}* ) && \
                ("${ipi2}" != 0* && ${ipi2} -eq 168) && \
                ((${#ipi3} -eq 1 && ${ipi3} -le 255) || (${#ipi3} -gt 1 && "${ipi3}" != 0* && ${ipi3} -le 255)) && \
                ((${#ipi4} -eq 1 && ${ipi4} -le 255) || (${#ipi4} -gt 1 && "${ipi4}" != 0* && ${ipi4} -le 255))
             ]]
            status=$?
        ;;
        esac
    fi
    return $status
}

# Check first if a valid --wifi-interface name option is provided or not. 
# If a valid --wifi-interface name option is provided then, reset the WLAN details
# by calling the function: setWlanDetails.
for i in ${!options[@]}; do
    
    option="${options[$i]}"
    
    if [[ "$option" == --wifi-interface=* ]]; then
        wlanInterfaceNameTemp="$(echo $option | awk -F '=' '{print $2}')"
        if [ ! -z "$wlanInterfaceNameTemp" ]; then
            if [ "$(iwlist $wlanInterfaceNameTemp scan 2>/dev/null)" ]; then
                wlanInterfaceNameValid=true
                wlanInterfaceName="$wlanInterfaceNameTemp"
                setWlanDetails
            else
                wlanInterfaceNameValid=false
                wlanInterfaceName="$wlanInterfaceNameDefault"
            fi
        fi
    fi
	
done



# Process AP Password encryption:
apWpaPsk="$( wpa_passphrase ${apSsid} ${apPassphrase} | awk '{$1=$1};1' | grep -P '^psk=' | awk -F '=' '{print $2}' )"
apPasswordConfig="wpa_psk=$apWpaPsk"


doRemoveDisableIPv6Setup() {
    result=$(sed -n '/^#__IPv6_SETUP_START__/,/^#__IPv6_SETUP_END__/p' /etc/sysctl.conf)
    if [ ! -z "$result" ]; then
        echo "[Remove]: IPv6 config from /etc/sysctl.conf"
        sed '/^#__IPv6_SETUP_START__/,/^#__IPv6_SETUP_END__/d' /etc/sysctl.conf > ./tmp.conf
        rm -f /etc/sysctl.conf
        mv ./tmp.conf /etc/sysctl.conf
        rm -f ./tmp.conf
    fi
}

doAddDisableIPv6Setup() {
    doRemoveDisableIPv6Setup
    cat >> /etc/sysctl.conf <<EOF

#__IPv6_SETUP_START__
net.ipv6.conf.all.disable_ipv6=1
net.ipv6.conf.default.disable_ipv6=1
net.ipv6.conf.lo.disable_ipv6=1
net.ipv6.conf.eth0.disable_ipv6=1
net.ipv6.conf.${wlanInterfaceName}.disable_ipv6=1
#__IPv6_SETUP_END__
EOF

}

# FIX: Raspbian Buster OS creating problem while reloading dhcpcd.service after cleanup.
# This is causing because of IPv6 and hence, disabling IPv6.
# You can enable IPv6 again by calling doRemoveDisableIPv6Setup() function.
# doAddDisableIPv6Setup

# Create initial directories:
mkdir -p $installDir
mkdir -p $logDir
mkdir -p $execDir
mkdir -p $downloadDir

doRemoveDhcpdApSetup() {
    # May work with this pattern also: /^#__AP_SETUP_START__/,/^#__AP_SETUP_END__/p;/^#__AP_SETUP_END__/q
    result=$(sed -n '/^#__AP_SETUP_START__/,/^#__AP_SETUP_END__/p' /etc/dhcpcd.conf)
    if [ ! -z "$result" ]; then
        echo "[Remove]: AP config from /etc/dhcpcd.conf"
        sed '/^#__AP_SETUP_START__/,/^#__AP_SETUP_END__/d' /etc/dhcpcd.conf > ./tmp.conf
        rm -f /etc/dhcpcd.conf
        mv ./tmp.conf /etc/dhcpcd.conf
        rm -f ./tmp.conf
    fi
}

doAddDhcpdApSetup() {
    doRemoveDhcpdApSetup
    cat >> /etc/dhcpcd.conf <<EOF

#__AP_SETUP_START__
interface ${apInterfaceName}
static ip_address=$apIp
nohook wpa_supplicant
#__AP_SETUP_END__
EOF

}

doRemoveRcLocalNetStartSetup() {
    if [ $(cat /etc/rc.local 2>/dev/null | grep -c "$netStartFile") -gt 0 ]; then
        echo "[Remove]: entry -> '$netStartFile' from /etc/rc.local"
        sed '/netStart/d' /etc/rc.local > ./tmp.conf
        rm -f /etc/rc.local
        mv ./tmp.conf /etc/rc.local
        rm -f ./tmp.conf
    fi
}

doAddRcLocalNetStartSetup() {
    doRemoveRcLocalNetStartSetup
    sed '/exit 0/d' /etc/rc.local > ./tmp.conf
    echo "/bin/bash $netStartFile
exit 0" >> ./tmp.conf
    rm -f /etc/rc.local
    mv ./tmp.conf /etc/rc.local
    rm -f ./tmp.conf
}

doRemoveApIpEntriesFromHostFile() {
     if [ `cat /etc/hosts | grep -c ^10.` -gt 0 -o \
     `cat /etc/hosts | grep -c ^172.` -gt 0 -o \
     `cat /etc/hosts | grep -c ^192.168.` -gt 0 ]; then
        sed '/^10./d;/^172./d;/^192.168./d' /etc/hosts > ./tmp.conf
        mv ./tmp.conf /etc/hosts
        rm -f ./tmp.conf
        echo "[Cleanup]: Cleaned all AP IP entries from /etc/hosts file."
     fi
}

doAddApIpEntriesToHostFile() {

    cat > /etc/hosts <<EOF 
127.0.0.1       localhost
::1             localhost ip6-localhost ip6-loopback
ff02::1         ip6-allnodes
ff02::2         ip6-allrouters

127.0.1.1       $hostName
$apIp    $hostName
EOF

}

doRemoveIpTableNatEntries() {
    # Clean other network entries:
    #iw dev uap0 del
    apDelCmd='iw dev '${apInterfaceName}' del'
    bash -c '$apDelCmd'
    iptables -F
    iptables -t nat -F
    bash -c 'cat /dev/null > /etc/iptables.ipv4.nat'
    bash -c 'cat /dev/null > /proc/sys/net/ipv4/ip_forward'
    sed -i 's/^net.ipv4.ip_forward=.*$/#net.ipv4.ip_forward=1/' /etc/sysctl.conf
    echo "[Cleanup]: Cleaned all NAT IP Table entries."
}

doRestartSysDaemon() {
    if [ ! `sudo systemctl status dhcpcd 2> /dev/null | grep "systemctl daemon-reload"` ]; then
        systemctl daemon-reload
        echo "[Restart]: System Daemon restarted!"
    fi
}

doAptClean() {
    apt-get clean
    apt-get autoclean -y
    apt-get autoremove -y
    echo "[Cleanup]: apt-get clean/autoremove done."
}

doCleanup() {
    echo "[Cleanup]: cleaning ..."

    # Do apt-get clean:
    doAptClean

    # Cleanup: /etc/dhcpcd.conf
    doRemoveDhcpdApSetup

    # Cleanup: /etc/rc.local
    doRemoveRcLocalNetStartSetup

    if [ $(dpkg-query -W -f='${Status}' hostapd 2>/dev/null | grep -c "ok installed") -eq 1 ]; then
        echo "[Remove]: hostapd"
        apt-get purge -y hostapd
        # FIX: broken link if purge did not remove the dirctory as the dirctory is not empty and the directory has user-data.
        if [ -d "/etc/hostapd" ]; then
            rm -rf /etc/hostapd*
            echo "[Remove]: Forcibly removed directory: /etc/hostapd."
        fi
    fi

    if [ $(dpkg-query -W -f='${Status}' dnsmasq 2>/dev/null | grep -c "ok installed") -eq 1 ]; then
        echo "[Remove]: dnsmasq"
        apt-get purge -y dnsmasq
        # FIX: broken link if purge did not remove the dirctory as the dirctory is not empty and the directory has user-data.
        if [ -d "/etc/dnsmasq.d" ]; then
            rm -rf /etc/dnsmasq*
            echo "[Remove]: Forcibly removed directory: /etc/dnsmasq.d and all related dnsmasq files."
        fi
    fi

    # FIX: In Buster OS, dns-root-data creating problem while installing dnsmasq and hence, purge required for dns-root-data:
    if [ $(dpkg-query -W -f='${Status}' dns-root-data 2>/dev/null | grep -c "ok installed") -eq 1 ]; then
        echo "[Remove]: dns-root-data"
        apt-get purge -y dns-root-data
    fi

    if [ $(dpkg-query -W -f='${Status}' iptables-persistent 2>/dev/null | grep -c "ok installed") -eq 1 ]; then
        echo "[Remove]: iptables-persistent"
        apt-get purge -y iptables-persistent
    fi

    if [ -f "$netStationConfigFile" ]; then
        echo "[Remove]: $netStationConfigFile"
        rm -f $netStationConfigFile
    fi

    if [ -f "/etc/dnsmasq.conf" ]; then
        echo "[Remove]: /etc/dnsmasq.conf"
        rm -f /etc/dnsmasq.conf
    fi
    
    if [ -f "/etc/dnsmasq.conf.orig" ]; then
        echo "[Remove]: /etc/dnsmasq.conf.orig"
        rm -f /etc/dnsmasq.conf
    fi

    if [ -f "/etc/hostapd/hostapd.conf" ]; then
        echo "[Remove]: /etc/hostapd/hostapd.conf"
        rm -f /etc/hostapd/hostapd.conf
    fi

    if [ -f "/etc/default/hostapd" ]; then
        echo "[Remove]: /etc/default/hostapd"
        rm -f /etc/default/hostapd
    fi

    if [ $(systemctl list-unit-files --type=service 2>/dev/null | grep -c 'netStop.service') -gt 0 ]; then
        systemctl stop netStop.service
        systemctl disable netStop.service
        echo "[Remove]: stop/disable service -> netStop"
    fi
    
    if [ -f "$netStopServiceFile" ]; then
        echo "[Remove]: $netStopServiceFile"
        rm -f $netStopServiceFile
    fi
    
    if [ -f "$netStartFile" ]; then
        echo "[Remove]: $netStartFile"
        rm -f $netStartFile
    fi
    
    if [ -f "$netStopFile" ]; then
        echo "[Remove]: $netStopFile"
        rm -f $netStopFile
    fi
    
    if [ -f "$netLogFile" ]; then
        echo "[Remove]: $netLogFile"
        rm -f $netLogFile
    fi
    
    if [ -f "$rcLocalLogFile" ]; then
        echo "[Remove]: $rcLocalLogFile"
        rm -f $rcLocalLogFile
    fi
    
    if [ -f "$shutdownRecoveryFile" ]; then
        echo "[Remove]: $shutdownRecoveryFile"
        rm -f $shutdownRecoveryFile
    fi
    
    if [ -f "$netShutdownFlagFile" ]; then
        echo "[Remove]: $netShutdownFlagFile"
        rm -f $netShutdownFlagFile
    fi
    
    doRemoveIpTableNatEntries

    # FIX: for https://github.com/idev1/rpihotspot/issues/12#issuecomment-605552834
    doRemoveApIpEntriesFromHostFile
    
    # Clean and auto remove the previously install dependant component if they exists by improper purging.
    doAptClean

    #Restart DHCPCD service:
    # FIX: it seems daemon-reload required on Buster OS+ as the dhcpcd don't start by default 
    # if the dhcpcd service unit is changed and then, it wait for sometime indicating that a 
    # daemon-restart is required.
    doRestartSysDaemon
    systemctl restart dhcpcd
    # FIX: For Buster OS, forcibly enabling dhcpcd if its previously disabled.
    if [ $OS_VERSION == 10 ]; then
        systemctl enable dhcpcd
        echo "[Cleanup]: Forcibly enabled dhcpcd."
    fi
    sleep 5
    
    echo "[Cleanup]: DONE"
}

downloadReqDependancies() {
    apt-get update --fix-missing
    apt-get upgrade -y --fix-missing
    apt-get install -y hostapd dnsmasq iptables-persistent
}

isAvailableReqDependancies() {
    [ $(dpkg-query -W -f='${Status}' hostapd 2>/dev/null | grep -c "ok installed") -eq 1 -a \
     $(dpkg-query -W -f='${Status}' dnsmasq 2>/dev/null | grep -c "ok installed") -eq 1 -a \
     $(dpkg-query -W -f='${Status}' iptables-persistent 2>/dev/null | grep -c "ok installed") -eq 1 ]
    status=$?
    return $status
}

doInstall() {

echo ""
echo "[WLAN]: ${wlanInterfaceName} IP address: $wlanIpAddr"
echo "[WLAN]: ${wlanInterfaceName} IP Mask address: $wlanIpMask"
echo "[WLAN]: ${wlanInterfaceName} IP Broadcast address: $wlanIpCast"
echo "[WLAN]: ${wlanInterfaceName} Country Code: $wlanCountryCode"
echo "[WLAN]: ${wlanInterfaceName} Channel: $wlanChannel"

doCleanup 

touch $netLogFile
chmod ug+w $netLogFile

#Silent install iptables:
echo iptables-persistent iptables-persistent/autosave_v4 boolean true | debconf-set-selections
echo iptables-persistent iptables-persistent/autosave_v6 boolean true | debconf-set-selections
echo "[Install]: installing: hostapd dnsmasq iptables-persistent from net ..."
downloadReqDependancies


# FIX: For issue #13, Raspbian Buster OS unable to correct nameserver entry in /etc/resolv.conf hence,
# need to correct this entry for downloading the files again:
if ! isAvailableReqDependancies; then
    if [ ! `sudo cat /etc/resolv.conf 2>/dev/null | grep "8.8.8.8"` ]; then
        echo "nameserver 8.8.8.8" >> /etc/resolv.conf
        echo "[Install]: Google nameserver 8.8.8.8 added into /etc/resolv.conf."
        echo "[Install]: Now retrying 2nd time to download required dependancies ..."
        downloadReqDependancies
    fi
fi 

if ! isAvailableReqDependancies; then
    echo "[Install]: Required dependancies: hostapd, dnsmasq and iptables-persistent are not available. Please check your internet connection!"
    echo "[Install]: Installation FAILED! Exiting installation now.."
    exit 0
fi

systemctl stop hostapd
systemctl stop dnsmasq

doAddDhcpdApSetup

if [ ! -f "/etc/dnsmasq.conf.orig" ]; then
    echo "[Move]: /etc/dnsmasq.conf to /etc/dnsmasq.conf.orig"
    mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
fi

cat > /etc/dnsmasq.conf <<EOF
interface=lo,${apInterfaceName}               #Use interfaces lo and ${apInterfaceName}
no-dhcp-interface=lo,${wlanInterfaceName}
bind-interfaces                 #Bind to the interfaces
server=8.8.8.8                  #Forward DNS requests to Google DNS
#domain-needed                  #Don't forward short names
bogus-priv                      #Never forward addresses in the non-routed address spaces
dhcp-range=$apDhcpRange
EOF

cat > /etc/hostapd/hostapd.conf <<EOF
channel=$apChannel
ssid=$apSsid
$apPasswordConfig
country_code=$apCountryCode
interface=${apInterfaceName}
# Use the 2.4GHz band (I think you can use in ag mode to get the 5GHz band as well, but I have not tested this yet)
hw_mode=g
# Accept all MAC addresses
macaddr_acl=0
# Use WPA authentication
auth_algs=1
# Require clients to know the network name
ignore_broadcast_ssid=0
# Use WPA2
wpa=2
# Use a pre-shared key
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
#driver=nl80211
# I commented out the lines below in my implementation, but I kept them here for reference.
# Enable WMM
#wmm_enabled=1
# Enable 40MHz channels with 20ns guard interval
#ht_capab=[HT40][SHORT-GI-20][DSSS_CCK-40]
EOF

sed -i 's/^#DAEMON_CONF=.*$/DAEMON_CONF="\/etc\/hostapd\/hostapd.conf"/' /etc/default/hostapd

cat > $netStationConfigFile <<EOF 
allow-hotplug ${wlanInterfaceName}
EOF

# Create shutdown recovery script when last time shutdown did not go well.
cat > $shutdownRecoveryFile <<EOF
# ----------------------------------------------------------------------------------------------
# IMPORTANT: 
# ----------------------------------------------------------------------------------------------
# Improper shutdown/reboot by directly switching of the device or taking off the power plug
# may result in malfuctioning of Access Point (AP) Network setup or may harm other
# functionalies of the application. Hence, below script will ensure improper shutdown recovery.
# You can disable this feature by setting: 'rebootFlag=false' or 'rebootFlag=n' in this script
# or in main script: 'setup-network.sh'.
# ----------------------------------------------------------------------------------------------

if [ ! -f "$netShutdownFlagFile" ]; then
    #sudo bash -c 'echo "\$(date +"%Y-%m-%d %T") - [WARNING]: Last time shutdown did not happen properly!" >> $netLogFile'
    echo "[WARNING]: Last shutdown errors may affect Access Point(AP) Network to become non-functional!"
    echo "[SOLUTION]: Reboot system to solve the shutdown errors."
    #read -n 1 -p "Reboot System [y/n]: " "rebootFlag"
    if [ "$rebootFlag" = "y" -o "$rebootFlag" = true ]; then
        sudo $netStopFile
        echo "Rebooting in 5 seconds ..."
        sleep 5
        sudo reboot
    fi
elif [ -f "$netShutdownFlagFile" ]; then
    sudo rm -f $netShutdownFlagFile
fi

EOF

chmod ug+x $shutdownRecoveryFile

# Create startup script
cat > $netStartFile <<EOF

# Check shutdown flag file exists for proper last time shutdown 
# and if last time shutdown did not happen properly then reboot to make sure that, 
# netStop.service properly do the necessary things before shutdown:

# Output the standard errors and messages of rc.local executions to rc.local.log file.
exec 2> $rcLocalLogFile
exec 1>&2

# Attach script for improper shutdown recovery:
source $shutdownRecoveryFile


#Make sure no ${apInterfaceName} interface exists (this generates an error; we could probably use an if statement to check if it exists first)
echo "Removing ${apInterfaceName} interface..."
iw dev ${apInterfaceName} del

#Add ${apInterfaceName} interface (this is dependent on the wireless interface being called ${wlanInterfaceName}, which it may not be in Stretch)
echo "Adding ${apInterfaceName} interface..."
iw dev ${wlanInterfaceName} interface add ${apInterfaceName} type __ap

#Modify iptables (these can probably be saved using iptables-persistent if desired)
echo "IPV4 forwarding: setting..."
#sysctl net.ipv4.ip_forward=1
#echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sed -i 's/^#net.ipv4.ip_forward=.*$/net.ipv4.ip_forward=1/' /etc/sysctl.conf
echo "Editing IP tables..."
echo 1 > /proc/sys/net/ipv4/ip_forward
iptables -F
iptables -t nat -F
sleep 2
$apSetupIptablesMasquerade
iptables -t nat -A POSTROUTING -o ${wlanInterfaceName} -j MASQUERADE
iptables -A FORWARD -i ${wlanInterfaceName} -o ${apInterfaceName} -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i ${apInterfaceName} -o ${wlanInterfaceName} -j ACCEPT
#iptables-save > /etc/iptables/rules.v4
iptables-save > /etc/iptables.ipv4.nat
#iptables-restore < /etc/iptables.ipv4.nat

# Bring up ${apInterfaceName} interface. Commented out line may be a possible alternative to using dhcpcd.conf to set up the IP address.
#ifconfig ${apInterfaceName} 10.0.0.1 netmask 255.255.255.0 broadcast 10.0.0.255
ifconfig ${apInterfaceName} up

# Start hostapd. 10-second sleep avoids some race condition, apparently. It may not need to be that long. (?) 
echo "Starting hostapd service..."
systemctl start hostapd.service
sleep 10

#Start dhcpcd. Again, a 5-second sleep
echo "Starting dhcpcd service..."
systemctl start dhcpcd.service
sleep 20

echo "Starting dnsmasq service..."
systemctl restart dnsmasq.service
#systemctl start dnsmasq.service

echo "Enabling netStop service..."
systemctl enable netStop.service
systemctl start netStop.service

echo "netStart DONE"
bash -c 'echo "\$(date +"%Y-%m-%d %T") - Started: hostapd, dnsmasq, dhcpcd" >> $netLogFile'
EOF

chmod ug+x $netStartFile

doAddRcLocalNetStartSetup

doAddApIpEntriesToHostFile

# Disable regular network services:
# The netStart script handles starting up network services in a certain order and time frame. Disabling them here makes sure things are not run at system startup.
systemctl unmask hostapd

cat > $netStopFile <<EOF
#! /bin/bash

sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
sudo systemctl stop dhcpcd
sudo systemctl disable hostapd
sudo systemctl disable dnsmasq
sudo systemctl disable dhcpcd

sudo bash -c 'echo "\$(date +"%Y-%m-%d %T") - Stopped: hostapd, dnsmasq, dhcpcd" >> $netLogFile'

# Handle proper shutdown by touching a empty shutdown flag file:
sudo touch $netShutdownFlagFile

EOF

chmod ug+x $netStopFile

# REFERENCE: https://raspberrypi.stackexchange.com/questions/89732/run-a-script-at-shutdown-on-raspbian
cat > $netStopServiceFile <<EOF
[Unit]
Description=Stops all the WiFi dependencies: hostapd, dnsmasq and dhcpcd.

[Service]
Type=oneshot
RemainAfterExit=true
ExecStart=$netStartFile
ExecStop=$netStopFile

[Install]
WantedBy=multi-user.target
EOF

echo "[Install]: enabling netStop.service ..."

systemctl enable netStop.service
systemctl start netStop.service

chmod ug+x /etc/rc.local

echo "[Install]: DONE"

}


doInstall
# Sleep for 10s before restarting:
echo "[Reboot]: In 10 seconds ..."
sleep 10
reboot

