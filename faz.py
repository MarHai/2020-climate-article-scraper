import time
from selenium import common
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from _config import faz_user, faz_password
from _browser import browser
from _database import cursor, insert_comment, update_article


print('Start: %d' % time.time())
browser.get("https://www.faz.net/mein-faz-net/?ot=de.faz.ot.body-vm&vm=loginboxformresp&excludeAds=true")

username = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.NAME, 'loginName')))
username.send_keys(faz_user)
password = browser.find_element_by_name("password")
password.send_keys(faz_password)
Anmelden = browser.find_element_by_class_name("btn-Base_Link")
Anmelden.click()
time.sleep(5)

cursor.execute('SELECT url, uid FROM article WHERE outlet = %s AND (text IS NULL OR text = "Artikel nicht mehr verfügbar")' , ("faz.net",))
if cursor.with_rows:
    articles = cursor.fetchall()
    print('%d lose Artikel in Datenbank gefunden' % (len(articles),))
else:
    articles = []
    print('keine Artikel in der Datenbank gefunden')

for article in articles:
    article_uid = article[1]
    url = article[0]
    print(url)

    cursor.execute('SELECT COUNT(*) FROM article WHERE uid = %s AND '
                   '(text IS NULL OR text = "Artikel nicht mehr verfügbar")' % article_uid)
    double_check = cursor.fetchone()
    if double_check[0] == 0:
        print('Artikel inzwischen verarbeitet')
        continue

    try:
        browser.get(url)
    except common.exceptions.TimeoutException:
        print('Artikel lädt nihct, warte weitere Sekunden ...')
        time.sleep(3)
    except common.exceptions.WebDriverException:
        print('Browser kann nicht mehr, vmtl. ein Hauptspeicherproblem, wir probieren es später nochmals ...')
        continue

    try:
        read_on_same_page = WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, 'ARTIKEL AUF EINER SEITE LESEN')))
        if read_on_same_page:
            read_on_same_page = browser.find_element_by_class_name('btn-Base_Link').get_attribute("href")
            teillink = read_on_same_page.split('#')
            wholelink = (teillink[0] + "?printPagedArticle=true#pageIndex_2")
            browser.get(wholelink)
    except (common.exceptions.NoSuchElementException, common.exceptions.TimeoutException):
        pass

    try:
        publication_date = WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 'atc-MetaTime')))
        if publication_date:
            publication_date = publication_date.text
    except (common.exceptions.NoSuchElementException, common.exceptions.TimeoutException):
        publication_date = ''

    try:
        article_title = browser.find_element_by_css_selector('.atc-HeadlineText').text
    except common.exceptions.NoSuchElementException:
        article_title = ''

    try:
        article_author = browser.find_element_by_class_name('atc-MetaItem-author').text
        article_author = article_author.replace('VON ', '')
        article_author = article_author.replace('EIN KOMMENTAR ', '')
    except common.exceptions.NoSuchElementException:
        article_author = ''

    try:
        article_presentation = browser.find_element_by_class_name('atc-MetaAuthorText').text
        if " KOMMENTAR " in article_presentation:
            article_presentation = "Meinungsartikel"
        else:
            article_presentation = " "
    except common.exceptions.NoSuchElementException:
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

    update_article(article_uid, article_title, article_text, publication_date, article_author, article_presentation)

    while True:
        try:
            WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 'js-lst-Comments_List-show-more'))).click()
        except (common.exceptions.NoSuchElementException,
                common.exceptions.TimeoutException,
                common.exceptions.StaleElementReferenceException):
            break

    comments_main = browser.find_elements_by_class_name('lst-Comments_Item-level1')
    for j, comment_main in enumerate(comments_main):
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

        comment_main_uid = insert_comment(article_uid, (j+1), kommentar_autor, kommentar_titel, kommentar_text)

        comments_replies = comment_main.find_elements_by_class_name('lst-Comments_Item-level2')

        for k, comment_reply in enumerate(comments_replies):
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

            insert_comment(article_uid, (k+1), kommentar_autor, kommentar_text, kommentar_titel, comment_main_uid)

    required_width = browser.execute_script('return document.body.parentNode.scrollWidth')
    required_height = browser.execute_script('return document.body.parentNode.scrollHeight')
    if required_height > 10000:
        required_height = 10000
    browser.set_window_size(required_width, required_height)
    path = 'screenshots/Artikel_'+str(article_uid)+'.png'
    browser.find_element_by_tag_name('body').screenshot(path)
    print('Screenshot für die FAZ unter %s gespeichert \n\n' % (path,))

browser.quit()
print('Ende: %d' % time.time())
