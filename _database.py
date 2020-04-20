# -*- coding: utf-8 -*-

import time
import mysql.connector
from _config import db, db_host, db_user, db_password


db = mysql.connector.connect(host=db_host, database=db, user=db_user, password=db_password)
if not db.is_connected():
    print('Fehler bei der Datenbankverbindung')
    exit(1)

db.autocommit = True
cursor = db.cursor(buffered=True)
cursor.execute('SET session wait_timeout=28800;')
cursor.execute('SET names utf8;')


def update_article(article_uid, article_title, article_text, publication_date, article_author, article_presentation,
                   failsafe_mode = False):
    try:
        cursor.execute('UPDATE article '
                       'SET scrape_date=%s, title=%s, text=%s, publication_date=%s, author=%s, presentation=%s '
                       'WHERE uid=%s LIMIT 1',
                       (int(time.time()), article_title, article_text, publication_date, article_author,
                        article_presentation, article_uid))
    except mysql.connector.errors.DatabaseError as error:
        print('Datenbank-Fehler bei der Artikel-Aktualisierung: %s' % error)
        if failsafe_mode:
            return False
        else:
            return update_article(article_uid,
                                  article_title.encode('utf-8'),
                                  article_text.encode('utf-8'),
                                  publication_date,
                                  article_author,
                                  article_presentation,
                                  True)
    if cursor.rowcount > 0:
        print('Artikel %d erfolgreich aktualisiert' % article_uid)
        return True
    else:
        print('Artikel nicht erfolgreich aktualisiert, FEHLER!')
        return False


def insert_comment(article_uid, rank, commenter, text, title='', is_reply_to=None, failsafe_mode=False):
    try:
        if is_reply_to is None:
            cursor.execute('INSERT INTO comment (article_uid, rank, commenter, title, text) VALUES (%s, %s, %s, %s, %s)',
                           (article_uid, rank, commenter, title, text))
        else:
            cursor.execute('INSERT INTO comment (article_uid, rank, commenter, title, text, is_reply_to) '
                           'VALUES (%s, %s, %s, %s, %s, %s)',
                           (article_uid, rank, commenter, title, text, is_reply_to))
    except mysql.connector.errors.DatabaseError as error:
        print('Datenbank-Fehler beim Kommentaranlegen: %s' % error)
        if failsafe_mode:
            return None
        else:
            return insert_comment(article_uid,
                                  rank,
                                  commenter,
                                  text.encode('utf-8'),
                                  '' if title is None else title.encode('utf-8'),
                                  is_reply_to,
                                  True)
    if cursor.lastrowid:
        uid = cursor.lastrowid
        print('%skommentar erfolgreich gespeichert unter der ID %d' %
              ('Haupt' if is_reply_to is None else 'Antwort', uid))
        return uid
    else:
        print('Kommentar nicht erfolgreich gespeichert, FEHLER!')
        return None
