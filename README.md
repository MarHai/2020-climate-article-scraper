# Datenerhebung Forschungsseminar

Um die Skripten überhaupt auf einen Server zu bekommen, bietet es sich an, per (1) Git auf das hier vorliegende Repository zurückzugreifen. Für die Lauffähigkeit selbst, benötigt der Server (2) Firefox, (3) die Möglichkeit, Firefox visuell darzustellen, (4) Python und (5) die genutzten Python-Bibliotheken. Soll die Datenbank aus Performance-Gründen lokal laufen, braucht der Server auch (6) MySQL. Zuletzt benötigt die Laufumgebung noch (7) eine korrekte Konfiguration.

Wir gehen von einem Unix-Server mit apt-get aus, also beispielsweise Ubuntu. 

1. Installation von Git und anschließendes Herunterladen unserer Skripte:
  ```
  sudo apt-get install -y git
  git clone https://github.com/MarHai/2020-climate-article-scraper.git
  cd 2020-climate-article-scraper/
  ```
1. Installation von Firefox: 
  ```
  sudo apt-get install -y firefox
  ```
1. Installation eines simulierten visuellen Displays, weil der Server keine Grafikkarte besitzt: 
  ```
  sudo apt-get install -y xvfb
  ```
1. Installation der genutzten Python-Bibliotheken (die wir in [requirements.txt](requirements.txt) gelistet haben):
  ```
  pip3 install -r requirements.txt
  ```
1. Installation und Einrichtung einer lokalen Datenbank:
  ```
  sudo apt-get install -y mysql-server
  sudo mysql_secure_installation utility
  sudo systemctl enable mysql
  sudo systemctl start mysql
  ```
1. Konfiguration korrekt setzen:
  ```
  nano _config.py
  ```

Jetzt sind wir startklar und können die einzelnen Dateien ausführen:
```
python3 faz.py
python3 taz.py
python3 welt.py
python3 zeit.py
```
