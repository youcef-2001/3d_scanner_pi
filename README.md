# 3d_scanner_pi


ceci est l'arborescence du projet de creation d'un scanneur 3d avec un raspberypi 3

l'application front qui s'occupera de piloter l'appareil hardware est dans un autre repository qui sera ajouter ici bientot


en ce qui concerne ce code il contientn pour le moment des bourt de code pour communiquer avec les composants  hardware et aussi un serveur flask preparatif pour faire le back end
a noter egalement qu'une base de donne qui contient les tables utilisateurs et ficheirs est sur supabase contenant egalement les ficheirs en tant que .stl

quelques commandes utiles :


le raspberry est cense etre a la fois un AP et un Client wifi  :
- pour lancer l'ap il faudra run cette commande 
depuis ce dossier ```/home/pi/network-setup/log```:

``` sudo netStart```

- pour l'arreter dans le mem dossier faite 

```sudo netStop.sh```
