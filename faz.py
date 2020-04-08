from __future__ import print_function
import mysql.connector
import time
from selenium import webdriver, common


browser = webdriver.Firefox(executable_path="/Users/corneliamaurus/PycharmProjects/untitled/geckodriver")

# Datenbankverbindung herstellen
db = mysql.connector.connect(host='',
                             database='',
                             user='',
                             password='')

# Prüfen, ob Datenbankverbindung erfolgreich hergestellt wurde
if not db.is_connected():
    print('Fehler bei der Datenbankverbindung')
    exit(1)

# Einzelnen Cursor für Datenbankoperationen deklarieren
cursor = db.cursor(buffered=True)

browser.get("https://www.faz.net/mein-faz-net/?ot=de.faz.ot.body-vm&vm=loginboxformresp&excludeAds=true&redirectUrl=")
time.sleep(10)

username = browser.find_element_by_name("loginName")
username.send_keys("")
password = browser.find_element_by_name("password")
password.send_keys("")
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
time.sleep(5)
cursor.execute('SELECT url, uid FROM article WHERE outlet = %s AND text IS NULL' , ("faz.net",))
if cursor.with_rows:
    articles = cursor.fetchall()
    print('%d lose Artikel in Datenbank gefunden' % (len(articles),))

for article in articles:
    article_uid = article[1]
    #print(article_uid)
    url = article[0]
    #print(url)
    browser.get(url)

#read article on one page
    try:
        read_on_same_page = browser.find_element_by_partial_link_text('ARTIKEL AUF EINER SEITE LESEN')
        if read_on_same_page:
            read_on_same_page = browser.find_element_by_class_name('btn-Base_Link').get_attribute("href")
            teillink = read_on_same_page.split('#')
            wholelink = (teillink[0] + "?printPagedArticle=true#pageIndex_2")
            browser.get(wholelink)
    except common.exceptions.NoSuchElementException:
        print("Hier gibt es nur eine Seite")
    time.sleep(5)

    try:
        publication_date = browser.find_element_by_class_name('atc-MetaTime').text
    except common.exceptions.NoSuchElementException:
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
            article_presentation = "Meinungsartikel"
        else:
            article_presentation = " "
    except common.exceptions.NoSuchElementException:
        #article_presentation = 'Kein Kommentar'
        article_presentation = " "
    print(article_presentation, sep='\n')


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

    time.sleep(5)

    while True:
        try:
            browser.implicitly_wait(10)
            versuch1 = browser.find_element_by_class_name("js-lst-Comments_List-show-more").click()
            time.sleep(10)
            versuch2 = browser.find_element_by_class_name("js-lst-Comments_List-show-more").click()
        except common.exceptions.NoSuchElementException:
            break

#start scraping comments
    comment_boxes = browser.find_elements_by_class_name('lst-Comments_Item-level1')
    comment_id = 0

    for j, box in enumerate (comment_boxes):

        #allcomments = box.find_elements_by_class_name('lst-Comments_CommentTextContainer')
        allcomments = box.find_elements_by_class_name('lst-Comments_CommentBoxContent')

        first_comment_id = comment_id + 1

        for k, comment in enumerate(allcomments):
            comment_id = comment_id + 1
            print(comment_id)

            is_reply_to = first_comment_id, "/", k + 1
            is_reply_to = str(is_reply_to)
            print(is_reply_to)

            try:
                kommentare_autor = comment.find_element_by_class_name('lst-Comments_CommentInfoNameText').get_attribute("innerHTML")
                print(kommentare_autor)
            except common.exceptions.NoSuchElementException:
                kommentare_autor = ''

            try:
                kommentare_titel = comment.find_element_by_class_name('lst-Comments_CommentTitle').get_attribute("innerHTML")
                print(kommentare_titel)
            except common.exceptions.NoSuchElementException:
                kommentare_titel = ''

            try:
                kommentare_text = comment.find_element_by_class_name('lst-Comments_CommentText').get_attribute("innerHTML")
                print(kommentare_text)
            except common.exceptions.NoSuchElementException:
                kommentare_text = ''

        #first_comment_id = comment_id + 1

        #save comments in DBS
            cursor.execute('INSERT INTO comment (article_uid, rank , commenter, title, text, is_reply_to)'
                        'VALUES (%s, %s, %s, %s, %s, %s)',
                        (
                            article_uid,  # Artikel-ID
                            comment_id,
                            kommentare_autor,
                            kommentare_titel,
                            kommentare_text,
                            is_reply_to,
                         ))
            if cursor.lastrowid:
                uid = cursor.lastrowid
                print('Kommentar für die FAZ erfolgreich gespeichert unter der ID %d' % (uid,))

        first_comment_id = comment_id + 1

    time.sleep(30)
    #make all comments visible in order to take screenshots
    try:
        firstcommentopen = browser.find_element_by_class_name("lst-Comments_CommentTextContainerMainInfo")

        comment_button = browser.find_elements_by_class_name("js-lst-Comments_CommentTitleClickProxy")
        for x in range(0, len(comment_button)):
            if comment_button[x].is_displayed():
                comment_button[x].click()

        answercomment_button = browser.find_elements_by_class_name("js-lst-Comments_CommentReplyList")
        for y in range(0, len(answercomment_button)):
            if answercomment_button[y].is_displayed():
                answercomment_button[y].click()

        answercomment = browser.find_elements_by_class_name("lst-Comments_Item-level2")
        for z in range(0, len(answercomment)):
            answercomment_button2 = answercomment[z].find_elements_by_class_name("js-lst-Comments_CommentTitleClickProxy")
            for x in range(0, len(answercomment_button2)):
                if answercomment_button2[x].is_displayed():
                    answercomment_button2[x].click()
    except common.exceptions.NoSuchElementException:
        pass

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
    path = '/Users/corneliamaurus/PycharmProjects/untitled/Artikel_'+str(article_uid)+'.png'

    el = browser.find_element_by_tag_name('body')
    time.sleep(60)
    el.screenshot(path)

    time.sleep(20)


browser.quit()
