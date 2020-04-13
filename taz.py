# -*- coding: utf-8 -*-

import time
from selenium import webdriver, common
import mysql.connector
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

browser = webdriver.Firefox()
#+++++++++++++++++ DATENBANK ++++++++++++++++++#

#Datenbankverbindung herstellen
db = mysql.connector.connect(host='haim.it',
                             database='d0306a8e',
                             user='d0306a8e',
                             password='p3LNz3DgsRX7zMnh'
                             )
                             

#Prüfen, ob Datenbankverbindung erfolgreich hergestellt wurde
if not db.is_connected():
    print('Fehler bei der Datenbankverbindung')
    exit(1)

#Einzelnen Cursor für Datenbankoperationen deklarieren
cursor = db.cursor(buffered=True)

#Session-Timeout verhindern
cursor.execute('SET session wait_timeout=28800;')


cursor.execute('SELECT url, uid FROM article WHERE outlet = %s  ', ("taz.de",)) #AND text IS NULL
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
            paywall = WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 'tzi-paywahl__close')))
            paywall.click()
        except (common.exceptions.NoSuchElementException, common.exceptions.TimeoutException):
            pass
        
        #+++++++++++++++++++++++++ ARTIKEL SCRAPEN +++++++++++++++++++++++++++#  
          
        # Titel
        try:
            article_title = browser.find_element_by_css_selector('article.sectbody > h1:nth-child(1) > span:nth-child(3)').text
        except common.exceptions.NoSuchElementException:
            article_title = ''
            
        # Text
        try:
            article_text = browser.find_element_by_class_name('body').text
        except common.exceptions.NoSuchElementException:
            
            article_text = ''
        # Datum
        try:
            publication_date = browser.find_element_by_class_name('date').text
        except common.exceptions.NoSuchElementException:
            article_text = ''
            
        # Autor
        try:
            article_author = browser.find_element_by_class_name('author').text
            article_author = article_author.replace('von ' , '').strip()
        except common.exceptions.NoSuchElementException:
            article_author = browser.find_element_by_css_selector('.article.first.odd').text 
        print("Autor: " + article_author)
        
        # Darstellungsformen
        kom = 'KOMMENTAR'
        kol = 'KOLUMNE'
        ess = 'ESSAY'
        inter = 'INTERVIEW'
        try:
            #article_presentation = browser.find_element_by_class_name('secthead').text
            article_presentation = browser.find_element_by_css_selector('.odd.sect.sect_profile.big.pictured ').text
            if kom in article_presentation:
                article_presentation = "Kommentar"
            elif kom in article_presentation:
                article_presentation = "Protokoll"
            elif ess in article_presentation: 
                article_presentation = "Essay"
            elif inter in article_presentation:
                article_presentation = "Interview"
            else: 
                  article_presentation = ''
            print ("Darstellungsform: " + article_presentation) 
        except common.exceptions.NoSuchElementException:
            pass
     
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
