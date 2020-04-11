import time
import mysql.connector
from selenium import webdriver, common
import re #ermöglicht den Regex-Ausdruck search einzusetzen
from _config import db, db_host, db_user, db_password, zeit_user, zeit_password

# Browser instanzieren
browser = webdriver.Firefox(executable_path='geckodriver.exe')

#Datenbankverbindung herstellen
db = mysql.connector.connect(host=db_host, database=db, user=db_user, password=db_password)

                              

#Prüfen, ob Datenbankverbindung erfolgreich hergestellt wurde
if not db.is_connected():
    print('Fehler bei der Datenbankverbindung')
    exit(1)

#Einzelnen Cursor für Datenbankoperationen deklarieren
cursor = db.cursor(buffered=True)

# prevent db connection timeout
cursor.execute('SET session wait_timeout=28800;')


#***ANMELDUNG ZEIT ONLINE KONTO***
outlet_signin = 'https://meine.zeit.de/anmelden?url=https%3A%2F%2Fwww.zeit.de%2Findex&entry_service=sonstige'
browser.get(outlet_signin)
browser.find_element_by_css_selector('#login_email').send_keys(zeit_user)
browser.find_element_by_css_selector('#login_pass').send_keys(zeit_password)
browser.find_element_by_css_selector('.submit-button').click()


#+++++++++++++++++ ARTIKEL SCRAPEN ++++++++++++++++++++++++#

cursor.execute('SELECT url, uid FROM article WHERE outlet = %s AND text IS NOT NULL', ("zeit.de",))
if cursor.with_rows:
    articles = cursor.fetchall() #Prüft ob Zeilen leer sind und nimmt nur jene mit Inhalt
    print('%d lose Artikel in Datenbank gefunden' % (len(articles),))

    for article in articles:  
        artikel_url = article[0]#Reihenfolge im Select Statement 
        article_uid = article[1]

        browser.get(artikel_url)
        
        #neuerdings ploppt ein iFrame auf, der weggeklickt werden muss
        time.sleep(3)
        try:
            frame = browser.find_element_by_xpath('//*[starts-with(@id, "sp_message_iframe_")]') #dafür muss man in den iFrame navigieren, der wie eine eigene Webseite funktioniert
            browser.switch_to.frame(frame)
            akzeptieren = browser.find_element_by_class_name('message-component')
            akzeptieren.click()
            #raus au dem iframe zur eigentlichen Seite
            browser.switch_to_default_content  #die nochmal neugeladen wird damit er dort auf die elemente zugreift
            browser.refresh()
        except common.exceptions.NoSuchElementException:
            pass

        try:
            read_on_same_page = browser.find_element_by_link_text('Auf einer Seite lesen')
            if read_on_same_page:
                artikel_url = read_on_same_page.get_attribute('href')
                browser.get(artikel_url)
        except common.exceptions.NoSuchElementException:
            pass

        try:
            article_title = browser.find_element_by_css_selector('h1.article-heading').text
        except common.exceptions.NoSuchElementException:
            article_title = ''

        try:
            article_text = browser.find_element_by_class_name('article-body').text
        except common.exceptions.NoSuchElementException:
            article_text = ''
        
        try:
            publication_date = browser.find_element_by_class_name('metadata__date').get_attribute('datetime')
        except common.exceptions.NoSuchElementException:
            article_text = ''
        
        #+++++++++++++++++++++++++++++ AUTOR  +++++++++++++++++++++++++++++++++#
        #Liste aller vorhanden Darstellungsformen und wie sie im Fenster angegeben werden
        kom = 'Ein Kommentar von'
        pro = 'Protokoll:'
        gast = 'Ein Gastbeitrag von'
        inte = 'Interview:'
        ana = 'Eine Analyse von'
        rez = 'Eine Rezension von'
        kol = 'Eine Kolumne von'
        ess = 'Ein Essay von'   
        
        #Autorenname bei Agenturaritkel
            # muss als erstes stehen, da die anderen Fälle diese Feld überschreiben, wenn sie vorhanden sind
        try:
            article_author = browser.find_element_by_class_name('metadata__source').text
            article_author = article_author.replace('Quelle: ', '').strip() # Lässt am Ende nur die Namen dort stehen
        except common.exceptions.NoSuchElementException:
                pass    
        #Autorennamen Zeit-Online
        try:
            article_author = browser.find_element_by_class_name('byline').text
            article_author = article_author.replace(pro, '').replace(inte,"").replace(ana,'').replace(gast,'').replace(kom,'').replace(rez,'').replace(ess,'').strip()# Lässt am Ende nur die Namen dort stehen
        except common.exceptions.NoSuchElementException:
                pass
            
        #Autorennamen wenn Zeit-Online Kolumne
        try:
            article_author = browser.find_element_by_class_name('column-heading__name').text
            article_author = article_author.replace(kol, '').replace(' und', ',').strip()# Lässt am Ende nur die Namen dort stehen
        except common.exceptions.NoSuchElementException:
                pass    
            
        #Autorname wenn Zeit-Campus
        try:
            article_author= browser.find_element_by_class_name('article-header__byline').text
            article_author = article_author.replace(pro, '').replace(inte,"").replace(ana,'').replace(gast,'').replace(kom,'').replace(rez,'').replace(ess,'').strip()# Lässt am Ende nur die Namen dort stehen
        except common.exceptions.NoSuchElementException:
                pass
        
         #+++++++++++++++++++++++ DARSTELLUNGSFORMEN ++++++++++++++++++++++++++#
        
        #Agentur
        try:
            article_presentation = browser.find_element_by_class_name('metadata__source').text
            article_presentation = ''
        except common.exceptions.NoSuchElementException:
                pass    
        
        #Darstellungsform Zeit-Online
        try:
            article_presentation = browser.find_element_by_class_name('byline').text
            # es wird geprüft, ob in der Beschreibungsspalte eine Darstellungsform vorhanden ist, ansonsten bleibt die Zeile leer
            if  kom in article_presentation:
                    article_presentation = "Kommentar"
            elif pro in article_presentation:
                    article_presentation = "Protokoll"
            elif gast in article_presentation:
                    article_presentation = "Gastbeitrag"
            elif inte in article_presentation:
                    article_presentation = "Interview"
            elif ana in article_presentation:
                    article_presentation = "Analyse"
            elif rez in article_presentation:
                    article_presentation = "Rezension"
            elif ess in article_presentation:
                    article_presentation ='Essay'
            else:
                article_presentation = ''
        except common.exceptions.NoSuchElementException:
                pass
        
        #Darstellungsform wenn Zeit-Online Kolumne
        try:
            article_presentation = browser.find_element_by_class_name('column-heading__name').text
            if kol in article_presentation:
                    article_presentation = "Kolumne"
            else:
                article_presentation = ''
        except common.exceptions.NoSuchElementException:
                pass    
            
        #Darstellungsform wenn Zeit-Campus
        try:
            article_presentation= browser.find_element_by_class_name('article-header__byline').text
            if  kom in article_presentation:
                    article_presentation = "Kommentar"
            elif pro in article_presentation:
                    article_presentation = "Protokoll"
            elif gast in article_presentation:
                    article_presentation = "Gastbeitrag"
            elif inte in article_presentation:
                    article_presentation = "Interview"
            elif ana in article_presentation:
                    article_presentation = "Analyse"  
            elif rez in article_presentation:
                    article_presentation = "Rezension"
            elif ess in article_presentation:
                    article_presentation ='Essay'
            else:
                article_presentation = ''
        except common.exceptions.NoSuchElementException:
                pass
                 
        #+++++++++++++++++++++ DATENBANK UPDATE FÜR ARTIKEL +++++++++++++++++++++++++#
#  Zu Testzwecken Update, beim Start der Erhebung auf Insert umstellen
        cursor.execute('UPDATE article SET scrape_date = %s, title = %s, text = %s,publication_date =%s, author = %s, presentation = %s WHERE uid = %s ', 
                      (
                           int(time.time()),  # aktueller Zeitstempel noch nicht umgewandelt
                           article_title,
                           article_text,
                           publication_date,
                           article_author ,
                           article_presentation ,
                           article_uid))  
        if cursor.rowcount > 0:
         print('Artikel %d für die ZEIT erfolgreich aktualisiert' % (article_uid,))


       #+++++++++++++++++ COOKIES UND VORBEREITUNG FÜR KOMMENTARE  +++++++++++++++++#
         
        while True:
            #Cookies wegklicken
                try:
                  cookies= browser.find_element_by_class_name('data-protection__button').click()
                except common.exceptions.NoSuchElementException:
                    pass 
            
            #Alle Kommentare öffnen
                weitereAntworten = browser.find_elements_by_partial_link_text('Weitere Antworten anzeigen')
                time.sleep(2)
                for a in weitereAntworten:
                    a.click()
                    
             #Maincomment-Rank für alle Kommentarseiten               
                cursor.execute('SELECT rank FROM article a JOIN comment c ON a.uid = c.article_uid WHERE a.uid=%s ORDER BY CONVERT(rank, UNSIGNED) DESC LIMIT 1', (article_uid,) )    
                # Vereinigt die article und comment Tabelle über die uid des aktuellen Artikels, dabei wird durch ORDER BY und LIMIT 1 sichergestellt, dass der aktuelle Kommentar-Rank oben steht
                #Convert wandelt die varchar Spalte in ein int um, damit die Sortierung klappt
                main_comment_rank = cursor.fetchone() # wählt den zuletzt vergebenen rank aus 
                if  isinstance(main_comment_rank, tuple): # wenn ein Rank vorhanden ist, muss er ein Tupel sein
                    main_comment_rank = int(main_comment_rank[0]) # und wird hier zu einem int konvertiert, um mit ihm zu rechnen
                    print ( "Aktueller Kommentar-Rank: " , (main_comment_rank) ) #die Datenbank muss natürlich für die spezifische uid leer sein
                else:
                    main_comment_rank=0 # bei einem NoneType Objekt wird eine 0 für die Rechnung vergeben
                    print ("(Noch) keine Ranks vorhanden") 
            
         #+++++++++++++++++ KOMMENTARE FÜR AKTUELLEN ARTIKEL SCRAPEN +++++++++++++++++#
         # !!! PROBLEM  unterschiedliche Performance bei verschiedenen Durchgängen. In der Regel werden zwischen 200-300 Kommentare gescrapet bevor er sich aufhängt, weil manche Elemente auf einmal nicht gefunden werden
         # lässt man diesen Teil einzeln laufen gibt es bisher keine Probleme damit das Elemente auf einmal nicht gefunden werden
         
                comments = browser.find_elements_by_css_selector('#js-comments-body article')
                for i, comment in enumerate(comments):
                 comment_author = comment.find_element_by_class_name('comment-meta__name').text
                 comment_title = ''
                 comment_text = comment.find_element_by_class_name('comment__body').text
                 comment_rank = i + 1 + main_comment_rank
                 
                 #!!! PROBLEM es wird immer nur die Antwort des ersten Kommentars genommen, anstatt sich das aktuelle Kommentar wie bei den anderen Variablen anzuschauen
                 try:
                     comment_isreplyto = browser.find_element_by_class_name('js-jump-to-comment').text
                      # XPATH - Version: comment_isreplyto = browser.find_element_by_xpath('//div/div//form[1]/button[@class="comment__origin js-jump-to-comment"]').text
                 except common.exceptions.NoSuchElementException:
                     comment_isreplyto =""
                 print (comment_author, comment_rank)
                 
                 
                 #+++++++++++++++++++ADAPTION VON ELENAS isreplyto VARIANTE t++++++++++++++++++++#
            #   funktioniert leider nicht, nicht mal auf der ersten Seite 
            
            #     comment_boxes = browser.find_elements_by_class_name('comment-section__body')
            #     #by_xpath("//div[@data-qa='comments']/div"
            #     comment_id = 0
            # #hier müssen eigentlich schon 12 elemente zu finden sein
            #     for j, box in enumerate(comment_boxes):
            
            #         comments = box.find_elements_by_class_name("comment")
            #         #hier sind alle 12 kommentare drin
            #         first_comment_id = comment_id + 1
                   
            
            #         for k, comment in enumerate(comments):
                        
            #             comment_id = comment_id + 1
            #             print(comment_id)
                        
            #             is_reply_to = '%s.%s' % (first_comment_id, (k + 1))
            #             print(is_reply_to)
                        
            #             comment_author = comment.find_element_by_class_name('comment-meta__name').text
            #             print(comment_author)
            #             comment_title = ''
            #             comment_text = comment.find_element_by_class_name('comment__body').text
            #             #comment_rank = i + 1
          
            #         first_comment_id = comment_id + 1
                 
        #+++++++++++++ SPEICHERN DER KOMMENTARE IN DATENBANK +++++++++++++++++++++++++++++++++++#
        
                 cursor.execute('INSERT INTO comment (article_uid, `rank`, commenter, title, text, is_reply_to) '
                                    'VALUES (%s, %s, %s, %s, %s, %s)',
                                    (
                                       article_uid,  # Artikel-ID
                                       comment_rank,
                                       comment_author,
                                       comment_title,
                                       comment_text,
                                       comment_isreplyto
 
                                  ))
                 #+++++++ Screenshot für aktuelle Seite  einfügen ++++++++++#
                 #Bennenung des Screenshots
                currenturl = browser.current_url  
                if  "page" in currenturl:
                        seitenzahl = re.search('page=(.*)#comments', currenturl) #sucht nach dem Part der zwischen 'page' und 'comments' liegt
                        seitenzahl = seitenzahl.group(1) # gibt den Teil des Strings zurück an dem ein Match vorlag
                else:
                    seitenzahl=''
                screenshot_name = (str(article_uid) + "_" + seitenzahl + ".png") # baut den Name des Screentshots zusammen
                # Screenshot ausführen
                original_size = browser.get_window_size()
                required_width = browser.execute_script('return document.body.parentNode.scrollWidth')
                required_height = browser.execute_script('return document.body.parentNode.scrollHeight')
                browser.set_window_size(required_width, required_height)
                with open(screenshot_name, 'wb') as image_file:
                    image_file.write(bytearray(browser.find_element_by_tag_name('body').screenshot_as_png))
                    browser.set_window_size(original_size['width'], original_size['height'])
                
                #Weiterklicken zur nächsten Kommentarseite bis man am Ende angelangt ist
                try:
                    element = browser.find_element_by_class_name('pager__button--next').click()
                    time.sleep(1)
                except common.exceptions.NoSuchElementException:
                   break
               

         
        if cursor.lastrowid:
            comment_uid = cursor.lastrowid
            print('Kommentar für die ZEIT erfolgreich gespeichert unter der ID %d' % (comment_uid,))
