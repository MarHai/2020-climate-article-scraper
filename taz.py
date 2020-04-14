# -*- coding: utf-8 -*-

import time
from selenium import webdriver, common
import mysql.connector
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from _config import db_host, db, db_user, db_password


browser = webdriver.Firefox(executable_path='geckodriver.exe')
browser.implicitly_wait(5)

# Datenbankverbindung herstellen
db = mysql.connector.connect(host=db_host, database=db, user=db_user, password=db_password)
                             

#Prüfen, ob Datenbankverbindung erfolgreich hergestellt wurde
if not db.is_connected():
    print('Fehler bei der Datenbankverbindung')
    exit(1)

#Einzelnen Cursor für Datenbankoperationen deklarieren
cursor = db.cursor(buffered=True)

#Session-Timeout verhindern
cursor.execute('SET session wait_timeout=28800;')


cursor.execute('SELECT url, uid FROM article WHERE outlet = %s AND text IS NULL', ("taz.de",))
if cursor.with_rows:
    articles = cursor.fetchall() #Prüft ob Zeilen leer sind und nimmt nur jene mit Inhalt
    print('%d lose Artikel in Datenbank gefunden' % (len(articles),))

    for article in articles:  
        artikel_url = article[0]#Reihenfolge im Select Statement 
        article_uid = article[1]
        
        #artikel_url="https://taz.de/Programmierer-ueber-Umweltbewegung/!5654010/"
        browser.get(artikel_url)
        print("\n" + "Aktueller Artikel:" + artikel_url)
        
        #Paywall wegklicken
        try:
            paywall = WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.tzi-paywahl__close a')))
            paywall.click()
        except (common.exceptions.NoSuchElementException, common.exceptions.TimeoutException):
            pass
        
        #+++++++++++++++++++++++++ ARTIKEL SCRAPEN +++++++++++++++++++++++++++#  
          
        # Titel
        try:
            article_title = browser.find_element_by_css_selector('.news.article h1:nth-child(1) > span:not(.hide):not(.kicker)').text
        except common.exceptions.NoSuchElementException:
            article_title = ''
            
        # Text
        try:
            article_text = ''
            article_paragraphs = browser.find_elements_by_css_selector('.news.article p.intro, .news.article article > p.article')
            for p in article_paragraphs:
                article_text += p.text + '\n\n'
        except common.exceptions.NoSuchElementException:
            article_text = ''

        # Datum
        try:
            publication_date = browser.find_element_by_css_selector('.news .date')
            try:
                publication_date = publication_date.get_attribute('content')
            except:
                publication_date = publication_date.text
            print('Datum: ' + publication_date)
        except common.exceptions.NoSuchElementException:
            publication_date = ''
            
        # Autoren
        try:
            article_author = []
            article_authors = browser.find_elements_by_css_selector('.news.article .author [itemprop="name"]')
            for author in article_authors:
                if author.text not in article_author:
                    article_author.append(author.text)
            article_author = ', '.join(article_author)
            print("Autoren: " + article_author)
        except common.exceptions.NoSuchElementException:
            article_author = ''
        
        # Darstellungsformen
        try:
            #article_presentation = browser.find_element_by_class_name('secthead').text
            article_presentation = browser.find_element_by_css_selector('.news .rightbar .sect_profile .secthead').text
            if 'KOMMENTAR' in article_presentation:
                article_presentation = "Kommentar"
            elif 'KOLUMNE' in article_presentation:
                article_presentation = "Kolumne"
            elif 'ESSAY' in article_presentation:
                article_presentation = "Essay"
            elif 'INTERVIEW' in article_presentation:
                article_presentation = "Interview"
            else:
                article_presentation = ''
            print("Darstellungsform: " + article_presentation)
        except common.exceptions.NoSuchElementException:
            article_presentation = ''

        cursor.execute('UPDATE article SET scrape_date = %s, title = %s, text = %s, publication_date =%s, author = %s, presentation = %s WHERE uid = %s ',
                       (
                           int(time.time()),  # aktueller Zeitstempel noch nicht umgewandelt
                           article_title,
                           article_text,
                           publication_date,
                           article_author,
                           article_presentation,
                           article_uid
                       ))

        if cursor.rowcount > 0:
            print('Artikel %d für die taz erfolgreich aktualisiert' % (article_uid,))

        #+++++++++++++++++ KOMMENTARE FÜR AKTUELLEN ARTIKEL SCRAPEN (Adaption von Kim) +++++++++++++++++#
        
        #++++++++++++++ HAUPTKOMMENTARE +++++++++++++++++#
        
        comments_main = browser.find_elements_by_xpath('//div/ul/li[starts-with(@id, "bb_message_")]')
        
        for j, comment_main in enumerate(comments_main):
    
            # Hauptkommentar in DB schreiben und neu erstellte ID merken
            try:
                kommentar_autor= comment_main.find_element_by_css_selector('.author.person').get_attribute("textContent")
                #kommentar_autor = comment_main.find_element_by_xpath('/a').text
                # ## !!! Warum funktioniert die XPATH-Angabe an dieser Stelle nicht? Der Pfad verweist auf alle Namen wie der Css-Seclector
            except common.exceptions.NoSuchElementException:
                kommentar_autor = ''
            try:           
                kommentar_text = comment_main.find_element_by_css_selector('.objlink.nolead').get_attribute("textContent")
                # XPATH: kommentar_text = comment_main.find_element_by_xpath('/div').text
                kommentar_titel = ''
            except common.exceptions.NoSuchElementException:
                kommentar_text = ''
                kommentar_titel = ''
                
            cursor.execute('INSERT INTO comment (article_uid, rank , commenter, title, text)'
                            'VALUES (%s, %s, %s, %s, %s)',
                            (article_uid, (j+1), kommentar_autor, kommentar_titel, kommentar_text))
            if cursor.lastrowid:
                comment_main_uid = cursor.lastrowid
                print('Hauptkommentar für die taz gespeichert unter der ID %d' % (comment_main_uid,))
            else:
                comment_main_uid = None
            
             # isreplyto- Variante mit dem Antwortnamen @User; Problem: immer nur der oberste Kommentare werden gespeichert
                    # try:
                    #     comment_isreplyto = browser.find_element_by_css_selector('.reference.person.member').get_attribute("textContent")
                    #     #Variante mit X-Path: comment_isreplyto = browser.find_element_by_xpath('//div/p/span').get_attribute("textContent")
                    # except common.exceptions.NoSuchElementException:
                    #     comment_isreplyto=""
                    
            #+++++ ANTWORTKOMMENTARE ++++++++#
            
            comments_replies = comment_main.find_elements_by_xpath('//*[@class="thread"]')
            print("Anzahl der Antwortkommentare: " + str( len(comments_replies) ) )
            ##!!! PROBLEM: die Threads sind ineinander verschachtelt. Jedes neues @User macht einen eigenen Thread auf und erkennt davon jeweils nur den ersten Kommentar
                   
            for k, comment_reply in enumerate(comments_replies):
            
                try: 
                    kommentar_autor= comment_reply.find_element_by_css_selector('.author.person').get_attribute("textContent")
                    #kommentar_autor = comment_main.find_element_by_xpath('//li/a').text
                    print(kommentar_autor)
                except common.exceptions.NoSuchElementException:
                    print("Autor nicht gefunden")
                try:
                    kommentar_text = comment_reply.find_element_by_css_selector('.objlink.nolead').get_attribute("textContent")
                    #kommentar_text = comment_main.find_element_by_xpath('//li[starts-with(@id, "bb_message_")]/div').text
                    kommentar_titel = ''
                    print (kommentar_text[0:50])
                except common.exceptions.NoSuchElementException:
                    print("Text nicht gefunden")
                    kommentar_titel = ''
    
                #Einfügen in die Datenbank
                cursor.execute('INSERT INTO comment (article_uid, rank , commenter, title, text, is_reply_to)'
                                'VALUES (%s, %s, %s, %s, %s, %s)',
                                (article_uid, (k+1), kommentar_autor, kommentar_titel, kommentar_text, comment_main_uid))
                if cursor.lastrowid:
                    uid = cursor.lastrowid
                    print('Antwortkommentar für die taz gespeichert unter der ID %d' % (uid,))     

         
 #+++++++++ SCREENSHOT +++++++++++#
        #Scrollt runter um eventuelle Kommentare vor dem Screenshot nachzuladen
        try:
            element = browser.find_element_by_xpath('//a[@name="So können Sie kommentieren:"]')
            browser.execute_script("arguments[0].scrollIntoView()", element)
        except common.exceptions.NoSuchElementException:
            pass
        time.sleep(1)
        screenshot_name = 'screenshots/Artikel_' + str(article_uid) + '.png' # baut den Name des Screentshots zusammen
        original_size = browser.get_window_size()
        required_width = browser.execute_script('return document.body.parentNode.scrollWidth')
        required_height = browser.execute_script('return document.body.parentNode.scrollHeight')
        browser.set_window_size(required_width, required_height)
        browser.set_window_size(original_size['width'], original_size['height'])
        with open(screenshot_name + ".png", 'wb') as image_file:
            image_file.write(bytearray(browser.find_element_by_tag_name('body').screenshot_as_png))
            browser.set_window_size(original_size['width'], original_size['height'])
            
browser.close()
