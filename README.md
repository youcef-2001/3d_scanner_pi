# 3d_scanner_pi

Ce projet vise à créer un scanner 3D basé sur un Raspberry Pi 3.

## Description

Ce dépôt contient le code backend pour la gestion du matériel du scanner 3D, ainsi qu'un serveur Flask pour la partie API.  
L'application frontend permettant de piloter l'appareil se trouve dans un autre dépôt (lien à venir).

Une base de données Supabase est utilisée pour stocker les utilisateurs et les fichiers 3D (au format `.stl`).

## Fonctionnalités

- Communication avec les composants hardware du scanner 3D
- Serveur Flask pour l'API backend
- Stockage des utilisateurs et fichiers sur Supabase

## Commandes utiles

Le Raspberry Pi agit à la fois comme point d'accès (AP) et client Wi-Fi.

- Pour lancer le point d'accès, exécutez depuis le dossier `/home/pi/network-setup/log` :
  ```bash
  sudo netStart
  ```

- Pour arrêter le point d'accès, exécutez dans le même dossier :
  ```bash
  sudo netStop.sh
  ```

## À venir

- Ajout du lien vers le dépôt frontend
- Documentation détaillée sur l'installation et l'utilisation

---
N'hésitez pas à proposer des améliorations en nous contactons via nos addresses mails respectives :
``` ybaleh13@gmail.com|```