# Scanner 3D basé sur Raspberry Pi

## Vue d'ensemble

Ce projet est un scanner 3D complet utilisant un Raspberry Pi 3 comme unité de traitement principale. Le système permet de numériser des objets physiques en 3D à l'aide d'une combinaison de caméra, laser et capteur LiDAR, puis de reconstruire et de visualiser ces objets sous forme de modèles 3D.

## Caractéristiques principales

- **Numérisation par triangulation laser**: Utilisation d'un laser et d'une caméra pour capturer la géométrie des objets
- **Mesure de distance précise**: Intégration d'un capteur TF-Luna LiDAR pour la premiere mesure par rapport a la platforme tournante
- **Interface Mobile Flutter**: API RESTful Flask pour contrôler toutes les fonctionnalités du scanner à distance
- **Streaming vidéo en direct**: Flux MJPEG en temps réel pour visualiser le processus de numérisation
- **Traitement automatisé**: Pipeline complet de l'acquisition à la création du modèle 3D
- **Stockage cloud**: Intégration avec Supabase pour le stockage des modèles et l'authentification des utilisateurs


## Architecture du système

### Matériel requis

- Raspberry Pi 3 
- Caméra compatible Raspberry Pi (utilisant Picamera2)
- Module laser 5 Volt (contrôlé par GPIO)
- Capteur TF-Luna LiDAR (connecté via I²C)
- Plateforme rotative pour la numérisation à 360°
- Shield pour battery Raspberry PI 3
- 2 piles 18650 pour l'autonomie

### Structure du projet

```
src/
├── services/               # Contrôle des composants matériels
│   ├── acquisition.py      
│   ├── cameraManager.py    # Gestion de la caméra (singleton)
│   ├── laserService.py     # Contrôle du laser via GPIO
│   └── TfLunaI2C.py        # Interface avec le capteur LiDAR (lib Tf-Luna)
├── reconstruction/         # Traitement et création du modèle 3D
│   ├── build3d.py          # Construction du nuage de points
│   ├── mesh_speed.py       # Génération du maillage 3D
│   ├── utils.py            # Utilitaires de calcul et de transformation en repere 3D
│   └── visualise_cloud_points.py # Visualisation du nuage de points
├── uploadstl/              # Gestion du stockage cloud
│   └── upload_stl.py       # Envoi des modèles vers Supabase
├── env-setup/              # Scripts de configuration
│   ├── setup.sh            # Configuration initiale du Raspberry Pi
│   ├── network_setup.sh    # Configuration du réseau (point d'accès WiFi)
│   └── requirements.txt    # Dépendances Python
├── flaskServeur.py         # Serveur API principal
├── run_full_pipeline.py    # Coordination du workflow complet
└── .env                    # Variables d'environnement (non versionné)
```

## Installation

### Configuration du Raspberry Pi

1. Clonez ce dépôt sur votre Raspberry Pi:
```bash
git clone https://github.com/youcef-2001/3d_scanner_pi.git
cd 3d_scanner_pi
```

2. Exécutez le script de configuration:
```bash
sudo bash src/env-setup/setup.sh
```

Ce script effectue les opérations suivantes:
- Installation des dépendances système ( hostapd, dnsmasq, etc.).
- Configuration des interfaces I²C et GPIO.
- Création d'un environnement virtuel Python. (assurez-vous d'utiliser les librairies system pour cet environnement)
- Installation des bibliothèques Python requises.
- Configuration du point d'accès WiFi.

### Variables d'environnement

Créez un fichier .env dans le répertoire src avec les informations suivantes:
```
# === CONFIGURATION SUPABASE ===
SUPABASE_URL = 'votre_url_supabase'
SUPABASE_KEY = 'votre_clé_api_supabase'

```

## Utilisation

### Démarrage du scanner

1. Activez le point d'accès WiFi:
```bash
cd ~/network-setup/bin
sudo ./netStart
```

2. Lancez le serveur Flask:
```bash
cd ~/3d_scanner_pi/
source ./venv/bin/activate

cd ./src

sudo ../venv/bin/python flaskServeur.py
```

3. Connectez-vous au réseau WiFi `Scanner_3D` avec le mot de passe `12345678*`

4. Accédez à l'interface via un navigateur à l'adresse: `http://192.168.13.1` si vous voulez testez les routes.
5. Ou via l'application, vous pourrez facilement avoir accès à toutes les fonctionnalités dans le panneau "Live View".


### API REST

Le scanner expose les endpoints suivants:

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/appairer` | POST | Authentifie et appaire un utilisateur avec le scanner |
| `/laser/on` | POST | Active le laser |
| `/laser/off` | POST | Désactive le laser |
| `/tfluna/read` | GET | Récupère une mesure du capteur LiDAR |
| `/start-acquisition` | POST | Démarre une numérisation 3D |
| `/acquisition-status` | GET | Vérifie l'état d'une numérisation en cours |
| `/camera/video_feed` | GET | Flux vidéo en direct (MJPEG) |
| `/camera/status` | GET | Informations sur l'état de la caméra |
| `/camera/rgb-filter` | POST | Modifie les valeurs du filtre choisis manuellement |

### Processus de numérisation

Le processus complet de numérisation comprend les étapes suivantes:
1. **Acquisition**: Capture des images en rotation avec le laser activé pour scanner l'objet
2. **Traitement d'images**: Application des filtres sur chaque image pour isoler les pixels illuminés par le laser
3. **Construction du nuage de points**: Calcul des coordonnées 3D réelles à partir des pixels détectés
4. **Génération du maillage**: Transformation du nuage de points en maillage 3D lissé (format STL)
5. **Sauvegarde et téléchargement**: Enregistrement local du modèle 3D et téléchargement vers le dossier utilisateur sur Supabase

## Paramètres de configuration

### Paramètres du scanner

Vous pouvez ajuster les paramètres du scanner dans utils.py:

- `DISTANCE_CAMERA_LASER`: Distance entre la caméra et le laser
- `HORIZONTAL_FOV`: Champ de vision horizontal de la caméra
- `VERTICAL_FOV`: Champ de vision vertical de la caméra
 d'autres constante peuvent etre retrouver dans le fichier utils.py

### Paramètres de reconstruction 3D

Les paramètres de la reconstruction du maillage peuvent être ajustés dans run_full_pipeline.py:
```python
config = {
    'voxel_size': 0.0004,      # Taille des voxels (plus petit = plus de détails)
    'nb_neighbors': 15,         # Nettoyage des points aberrants
    'std_ratio': 2.0,           # Rapport d'écart-type pour le nettoyage
    'normal_knn': 16,           # Estimation des normales
    'poisson_depth': 10,        # Profondeur de la reconstruction Poisson
    'density_threshold': 0.15,  # Seuil de densité
    'smooth_iterations': 2      # Nombre d'itérations de lissage
}
```

### Configuration réseau

Le point d'accès WiFi est configuré avec les paramètres suivants :
- SSID: `Scanner_3D`
- Mot de passe: `12345678*`
- Adresse IP: `192.168.13.1`

## Dépannage

### Problèmes de communication I2C pour la camera
- Assurez-vous que le câble est correctement connecté
- Vérifiez que l'interface I²C est activée: `sudo raspi-config`
- Testez la détection du TF-Luna: `sudo i2cdetect -y 1`
- vous devez avoir un 10 


### Problèmes de réseau
- Pour redémarrer le point d'accès: `sudo netStop.sh` puis `sudo netStart`
- Vérifiez l'état des services: `systemctl status hostapd dnsmasq`
- vous devrez retrrouver un service netStop en cours de fonctionnement
- ou ip a  une interface `uap0` devra etre lister en plus du `wlan0`

## Performances

Les performances du scanner dépendent de:
- La résolution de la caméra (configurable dans cameraManager.py)
- La luminosité ambiante (affecte la détection du laser)
- La complexité de l'objet numérisé
- Les paramètres de reconstruction 3D



## Contact

Pour toute question ou suggestion concernant ce projet, n'hésitez pas à contacter:
- Emails: `ybaleh13@gmail.com` | `jas.gagnard@gmail.com`|`ansumdinesaidcombo@gmail.com`