import mysql.connector
import time
from selenium import webdriver, common
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from _config import db, db_host, db_user, db_password, faz_user, faz_password


browser = webdriver.Firefox(executable_path='geckodriver.exe')
browser.implicitly_wait(5)

# Datenbankverbindung herstellen
db = mysql.connector.connect(host=db_host, database=db, user=db_user, password=db_password)

# Prüfen, ob Datenbankverbindung erfolgreich hergestellt wurde
if not db.is_connected():
    print('Fehler bei der Datenbankverbindung')
    exit(1)

# Einzelnen Cursor für Datenbankoperationen deklarieren
cursor = db.cursor(buffered=True)

# prevent db connection timeout
cursor.execute('SET session wait_timeout=28800;')

browser.get("https://www.faz.net/mein-faz-net/?ot=de.faz.ot.body-vm&vm=loginboxformresp&excludeAds=true")
# time.sleep(10)
# username = browser.find_element_by_name("loginName")
username = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.NAME, 'loginName')))
username.send_keys(faz_user)
password = browser.find_element_by_name("password")
password.send_keys(faz_password)
Anmelden = browser.find_element_by_class_name("btn-Base_Link")
Anmelden.click()

time.sleep(5)

#Testartikel:
#Artikel mit weiteren Kommentaren anzeigen und Antwortkommentaren
#link = "https://www.faz.net/aktuell/brexit/guy-verhofstadt-der-brexit-bleibt-ein-schrecklicher-gedanke-16610934.html"
#browser.get(link)

#link = "https://www.faz.net/aktuell/politik/inland/was-am-schuelerstreik-fridays-for-future-ungewoehnlich-ist-16043259.html"
#browser.get(link)

#Artikel Präsentation
#link = "https://www.faz.net/aktuell/politik/inland/deutsche-klimapolitik-vom-green-new-deal-bis-zum-kohle-gipfel-16582815.html"
#browser.get(link)

#Plus-Artikel
#link = "https://www.faz.net/aktuell/politik/inland/kommentar-zur-iaa-feldmann-am-steuer-das-wird-teuer-16610514.html"
#browser.get(link)

#normaler Artikel
#browser.get("https://www.faz.net/aktuell/wirtschaft/weltwirtschaftsforum/prinz-charles-in-davos-programm-fuer-nachhaltige-maerkte-16595493.html#lesermeinungen")

#normaler Kommentar
#browser.get("https://www.faz.net/aktuell/finanzen/tuebinger-muell-steuer-ist-fuer-die-tonne-16610893.html")


#Artikel über mehrere Seiten
#link = ("https://www.faz.net/aktuell/wirtschaft/digitec/wie-start-ups-die-smartphone-sucht-lindern-wollen-16547346.html")
#browser.get(link)

#Artikel mit vielen Kommentaren
#link =('https://www.faz.net/aktuell/wirtschaft/teure-umweltpolitik-klimaschutz-als-neue-ersatzreligion-16018515.html#lesermeinungen')
#browser.get(link)


#einzelne Artikel loose aus der Datenbank aufrufen
# time.sleep(5)
cursor.execute('SELECT url, uid FROM article WHERE outlet = %s AND text IS NULL' , ("faz.net",))
if cursor.with_rows:
    articles = cursor.fetchall()
    print('%d lose Artikel in Datenbank gefunden' % (len(articles),))
else:
    articles = []
    print('keine Artikel in der Datenbank gefunden')

for article in articles:
    article_uid = article[1]
    #print(article_uid)
    url = article[0]
    print(url)
    browser.get(url)

    #read article on one page
    try:
        # read_on_same_page = browser.find_element_by_partial_link_text('ARTIKEL AUF EINER SEITE LESEN')
        read_on_same_page = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, 'ARTIKEL AUF EINER SEITE LESEN')))
        if read_on_same_page:
            read_on_same_page = browser.find_element_by_class_name('btn-Base_Link').get_attribute("href")
            teillink = read_on_same_page.split('#')
            wholelink = (teillink[0] + "?printPagedArticle=true#pageIndex_2")
            browser.get(wholelink)
    except (common.exceptions.NoSuchElementException, common.exceptions.TimeoutException):
        print("Hier gibt es nur eine Seite")
    # time.sleep(5)

    try:
        # publication_date = browser.find_element_by_class_name('atc-MetaTime').text
        publication_date = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'atc-MetaTime')))
        if publication_date:
            publication_date = publication_date.text
    except (common.exceptions.NoSuchElementException, common.exceptions.TimeoutException):
        publication_date = ''
    print(publication_date, sep='\n')

    try:
        article_title = browser.find_element_by_css_selector('.atc-HeadlineText').text
    except common.exceptions.NoSuchElementException:
        article_title = ''
    print(article_title, sep='\n')

    try:
        article_author = browser.find_element_by_class_name('atc-MetaItem-author').text
    except common.exceptions.NoSuchElementException:
        article_author = ''
    print(article_author, sep='\n')

    try:
        article_presentation = browser.find_element_by_class_name('atc-MetaAuthorText').text
        if " KOMMENTAR " in article_presentation:
            print('%s als Meinungsartikel identifiziert' % (article_presentation,))
            article_presentation = "Meinungsartikel"
        else:
            article_presentation = " "
    except common.exceptions.NoSuchElementException:
        #article_presentation = 'Kein Kommentar'
        article_presentation = ""


    try:
        article_teaser = browser.find_element_by_class_name('atc-IntroText').text
    except common.exceptions.NoSuchElementException:
        article_teaser = ''


    try:
        article_text = article_teaser + "\n\n"
        paragraphs = browser.find_elements_by_class_name("atc-TextParagraph")
        for paragraph in paragraphs:
            article_text = article_text + "\n\n" + paragraph.text
    except common.exceptions.NoSuchElementException:
        article_text = article_teaser + ''
    print(article_text, sep='\n')

    # Save articles in DBS
    cursor.execute(
        'UPDATE article SET scrape_date = %s, publication_date =%s, title = %s, text = %s, author = %s, presentation = %s WHERE uid = %s',
        (
            int(time.time()),  # aktueller Zeitstempel
            publication_date,
            article_title,
            article_text,
            article_author,
            article_presentation,
            article_uid
        ))
    if cursor.rowcount > 0:
        print('Artikel %d für die FAZ erfolgreich aktualisiert' % (article_uid,))

    # time.sleep(5)

    while True:
        try:
            # browser.implicitly_wait(10)
            # versuch1 = browser.find_element_by_class_name("js-lst-Comments_List-show-more").click()
            # time.sleep(10)
            # versuch2 = browser.find_element_by_class_name("js-lst-Comments_List-show-more").click()
            WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'js-lst-Comments_List-show-more'))).click()
        except (common.exceptions.NoSuchElementException,
                common.exceptions.TimeoutException,
                common.exceptions.StaleElementReferenceException):
            break

    #start scraping comments
    comments_main = browser.find_elements_by_class_name('lst-Comments_Item-level1')
    # comment_id = 0

    for j, comment_main in enumerate(comments_main):

        # Hauptkommentar in DB schreiben und neu erstellte ID merken
        try:
            kommentar_autor = comment_main.find_element_by_class_name('lst-Comments_CommentInfoNameText').get_attribute('innerHTML')
        except common.exceptions.NoSuchElementException:
            kommentar_autor = ''
        try:
            kommentar_titel = comment_main.find_element_by_class_name('lst-Comments_CommentTitle').get_attribute('innerHTML')
        except common.exceptions.NoSuchElementException:
            kommentar_titel = ''
        try:
            kommentar_text = comment_main.find_element_by_class_name('lst-Comments_CommentText').get_attribute('innerHTML')
        except common.exceptions.NoSuchElementException:
            kommentar_text = ''
        cursor.execute('INSERT INTO comment (article_uid, rank , commenter, title, text)'
                       'VALUES (%s, %s, %s, %s, %s)',
                       (article_uid, (j+1), kommentar_autor, kommentar_titel, kommentar_text))
        if cursor.lastrowid:
            comment_main_uid = cursor.lastrowid
            print('Hauptkommentar für die FAZ erfolgreich gespeichert unter der ID %d' % (comment_main_uid,))
        else:
            comment_main_uid = None


        #allcomments = box.find_elements_by_class_name('lst-Comments_CommentTextContainer')
        comments_replies = comment_main.find_elements_by_class_name('lst-Comments_Item-level2')

        # first_comment_id = comment_id + 1

        for k, comment_reply in enumerate(comments_replies):
            #comment_id = comment_id + 1
            #print(comment_id)

            # is_reply_to = first_comment_id, "/", k + 1
            # is_reply_to = str(is_reply_to)
            # print(is_reply_to)

            try:
                kommentar_autor = comment_reply.find_element_by_class_name('lst-Comments_CommentInfoNameLink').get_attribute('innerHTML')
            except common.exceptions.NoSuchElementException:
                kommentar_autor = ''
            try:
                kommentar_titel = comment_reply.find_element_by_class_name('lst-Comments_CommentTitle').get_attribute('innerHTML')
            except common.exceptions.NoSuchElementException:
                kommentar_titel = ''
            try:
                kommentar_text = comment_reply.find_element_by_class_name('lst-Comments_CommentText').get_attribute('innerHTML')
            except common.exceptions.NoSuchElementException:
                kommentar_text = ''

            #first_comment_id = comment_id + 1

            #save comments in DBS
            cursor.execute('INSERT INTO comment (article_uid, rank , commenter, title, text, is_reply_to)'
                           'VALUES (%s, %s, %s, %s, %s, %s)',
                           (article_uid, (k+1), kommentar_autor, kommentar_titel, kommentar_text, comment_main_uid))
            if cursor.lastrowid:
                uid = cursor.lastrowid
                print('Kommentar für die FAZ erfolgreich gespeichert unter der ID %d' % (uid,))

        # first_comment_id = comment_id + 1

    # take screenshots
    # option 1

    # original_size = browser.get_window_size()
    # required_width = browser.execute_script('return document.body.parentNode.scrollWidth')
    # required_height = browser.execute_script('return document.body.parentNode.scrollHeight')
    # #print(required_width)
    # #print(required_height)
    # time.sleep(90)
    # browser.set_window_size(required_width, required_height)
    # with open('Screenshot'+article_title+'.png', 'wb') as image_file:
    #     image_file.write(bytearray(browser.find_element_by_tag_name('body').screenshot_as_png))
    # browser.set_window_size(original_size['width'], original_size['height'])

    #option 2
    # path = '/Users/corneliamaurus/PycharmProjects/untitled/Artikel_'+str(article_uid)+'.png'
    path = 'screenshots/Artikel_'+str(article_uid)+'.png'
    browser.find_element_by_tag_name('body').screenshot(path)
    print('Screenshot für die FAZ unter %s gespeichert' % (path,))

browser.quit()
