# -*- coding: utf-8 -*-

import mysql.connector
from _config import db, db_host, db_user, db_password


db = mysql.connector.connect(host=db_host, database=db, user=db_user, password=db_password)
if not db.is_connected():
    print('Fehler bei der Datenbankverbindung')
    exit(1)

cursor = db.cursor(buffered=True)
cursor.execute('SET session wait_timeout=28800;')
cursor.execute('SET names utf8;')
