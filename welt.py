import time
import mysql.connector
from selenium import webdriver, common
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from _config import db, db_host, db_user, db_password, welt_user, welt_password


browser = webdriver.Firefox(executable_path='geckodriver.exe')
browser.implicitly_wait(5)

# database connection
db = mysql.connector.connect(host=db_host, database=db, user=db_user, password=db_password)

# check database connection
if not db.is_connected():
    print('Fehler bei der Datenbankverbindung')
    exit(1)

# Einzelnen Cursor für Datenbankoperationen deklarieren
cursor = db.cursor(buffered=True)

# prevent db connection timeout
cursor.execute('SET session wait_timeout=28800;')


# sign in on welt.de
browser.get('https://secure.mypass.de/sso/web-fullpage/login?service=https%3A%2F%2Flo.la.welt.de%2Fuser%2Fredirect%3FredirectUrl%3Dhttps%253A%252F%252Fwww.welt.de%252F&wt_eid=2155419246963806176&wt_t=1579609313997')
username = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#username')))
username.send_keys(welt_user)
browser.find_element_by_css_selector('#password').send_keys(welt_password)
browser.find_element_by_css_selector('#proceedButton').click()
time.sleep(5)


# get links from list of test articles (later: from db)
# articles_test = ["https://www.welt.de/wirtschaft/plus207021623/Systemrelevante-Berufe-So-viel-verdienen-Krankenpfleger-und-Kassierer.html", "https://www.welt.de/debatte/kommentare/plus185672756/UN-Klimagipfel-Was-an-der-Rede-der-jungen-Greta-nicht-stimmte.html"]


# Einzelne Artikel loose aus der Datenbank aufrufen
cursor.execute('SELECT url, uid FROM article WHERE outlet = %s AND text IS NULL', ("welt.de",))

if cursor.with_rows:

    articles = cursor.fetchall()

    print('%d lose Artikel in Datenbank gefunden' % (len(articles),))
else:
    articles = []
    print('keine Artikel in der Datenbank gefunden')


# SCRAPE ARTICLE DATA
for i, article in enumerate(articles):

    article_uid = article[1]

    print(article_uid)

    url = article[0]

    print(url)

# for i, url in enumerate(articles_test):

    browser.get(url)
    # time.sleep(12)

    # show article on same page // bisher nicht benötigt
    # try:
    #     read_on_same_page = browser.find_element_by_class_name('btn-Base_Link')
    #     if read_on_same_page:
    #         article[0] = read_on_same_page.get_attribute('href')
    #         browser.get(article[0])
    # except common.exceptions.NoSuchElementException:
    #     pass

    # wait until overlay disappears
    #try:
    #    overlay = browser.find_element_by_class_name('as-oil-content-overlay')
    #    # print(overlay)
    #    if overlay:
    #        time.sleep(33)
    #
    #except common.exceptions.NoSuchElementException:
    #    pass
    browser.execute_script('document.querySelectorAll(".as-oil-content-overlay").forEach(function(el) { el.remove() })')

    # get rid of agb warning
    try:
        agb = browser.find_element_by_class_name('max-content-wrapper')
        # print(abg)

        if agb:
            agb.find_element_by_xpath('a').click()

    except common.exceptions.NoSuchElementException:
        pass

    try:
        # publication_date = browser.find_element_by_class_name('c-publish-date').get_attribute('datetime')
        # Für das erste zu suchende Elemente auf der Seite arbeiten wir mit Wait, damit die Seite ggf. noch laden kann
        publication_date = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'c-publish-date')))
        if publication_date:
            publication_date = publication_date.get_attribute('datetime')
        print(publication_date)
    except (common.exceptions.NoSuchElementException, common.exceptions.TimeoutException):
        publication_date = ""

    # Backup-Plan für publication_date
    if publication_date == '':
        try:
            publication_date = browser.find_element_by_tag_name('time')
            if publication_date:
                publication_date = publication_date.get_attribute('datetime')
                print(publication_date)
        except common.exceptions.NoSuchElementException:
            publication_date = ""

    # article_presentation = ""
    try:
        article_presentation = browser.find_element_by_css_selector('.rf-o-section')
        if article_presentation:
            article_presentation = article_presentation.text
        # check if presentation is "Meinung"
        # presentation = browser.find_element_by_css_selector('.rf-o-section').text
        # print(presentation)
        # if "MEINUNG" in presentation:
        #     article_presentation = "Meinungsartikel"
        # else:
        #     article_presentation = ""
        print(article_presentation)
    except common.exceptions.NoSuchElementException:
        article_presentation = ""

    try:
        article_title = browser.find_element_by_css_selector('.rf-o-headline')
        if article_title:
            article_title = article_title.text
        print(article_title)
    except common.exceptions.NoSuchElementException:
        article_title = ''

    try:
        article_author = browser.find_element_by_class_name('c-author__by-line')
        if article_author:
            article_author = article_author.text
            article_author = article_author.replace('Von ', '')
        print(article_author)
    except common.exceptions.NoSuchElementException:
        article_author = ''

    try:
        article_teaser = browser.find_element_by_css_selector('.c-summary__intro')
        if article_teaser:
            article_teaser = article_teaser.text
    except common.exceptions.NoSuchElementException:
        article_teaser = ''
    # print(article_teaser)

    article_text = article_teaser + "\n\n"
    try:
        # paragraphs = browser.find_element_by_class_name("c-article-text").find_elements_by_css_selector("p")
        paragraphs = browser.find_elements_by_css_selector('.c-article-text p:not(.o-element__text)')
        for paragraph in paragraphs:
            article_text = article_text + paragraph.text + '\n\n'
    except common.exceptions.NoSuchElementException:
        pass
    print(article_text)

    # update db
    cursor.execute('UPDATE article SET scrape_date = %s, publication_date = %s, title = %s, text = %s, author = %s, presentation = %s WHERE uid = %s',
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
        print('Artikel %d für welt.de erfolgreich aktualisiert' % (article_uid,))

    # SCRAPE COMMENT DATA
    try:
        comment_container = browser.find_element_by_xpath("//div[@data-qa='comments']")
        # print('Kommentar-Box:', comment_container)

        # show all comments
        def showAllComments():
            try:
                comment_button = comment_container.find_element_by_xpath('div[last()]/a/span')
                comment_button.click()
                time.sleep(0.5)
                showAllComments()
            except common.exceptions.NoSuchElementException:
                pass

        showAllComments()
        # time.sleep(1)


        comment_boxes = browser.find_elements_by_xpath("//div[@data-qa='comments']/div")

        # define comment_id that counts all comments (later in db: rank)
        # comment_id = 0

        # function to save comments in db
        def storeCommentInDBandReturnUID(db_cursor, article_uid, rank, commenter, text, is_reply_to=None):
            db_cursor.execute('INSERT INTO comment (article_uid, rank, commenter, text, is_reply_to)'
                              'VALUES (%s, %s, %s, %s, %s)',
                              (article_uid, rank, commenter, text, is_reply_to))
            if db_cursor.lastrowid:
                uid = db_cursor.lastrowid
                print('Kommentar für die welt.de erfolgreich gespeichert unter der ID %d' % (uid,))
                return uid
            else:
                print('Kommentar nicht erfolgreich gespeichert, FEHLER!')
                return None

        for j, box in enumerate(comment_boxes):

            # show all replies
            try:
                show_more_comments = box.find_element_by_xpath("div[last()]/div[2]/a")

                show_more_comments.click()
            except common.exceptions.NoSuchElementException:

                pass

            comments = box.find_elements_by_xpath(".//div[@data-qa='comment']")

            # store id of first comment (= "main" comment) of each box to use it in "is-reply-to"
            # first_comment_id = comment_id + 1
            first_comment_id = 0

            for k, comment in enumerate(comments):

                # increment comment_id with each comment
                # comment_id = comment_id + 1
                # print(comment_id)

                # in is-reply-to, store the position of the comment relative to the first comment (= "main" comment) of this box
                # is_reply_to = '%s.%s' % (first_comment_id, (k + 1))
                # print(is_reply_to)

                # no title
                # kommentare_titel = ''

                try:
                    kommentare_autor = comment.find_element_by_xpath("div[1]/div[2]/div/a")
                    if kommentare_autor:
                        kommentare_autor = kommentare_autor.text
                    print(kommentare_autor)
                except common.exceptions.NoSuchElementException:
                    kommentare_autor = ''

                try:
                    kommentare_text = comment.find_element_by_xpath("div[3]")
                    if kommentare_text:
                        kommentare_text = kommentare_text.text
                    print(kommentare_text)
                except common.exceptions.NoSuchElementException:
                    kommentare_text = ''

                if k == 0:
                    first_comment_id = storeCommentInDBandReturnUID(cursor,
                                                                    article_uid, j+1, kommentare_autor, kommentare_text)
                else:
                    storeCommentInDBandReturnUID(cursor,
                                                 article_uid, j + 1, kommentare_autor, kommentare_text,
                                                 first_comment_id)

            # before hopping to the next comment box, set first_comment_id to current comment_id + 1
            # first_comment_id = comment_id + 1

    except common.exceptions.NoSuchElementException:
        pass


    # take screenshot
    original_size = browser.get_window_size()

    required_width = browser.execute_script('return document.body.parentNode.scrollWidth')
    required_height = browser.execute_script('return document.body.parentNode.scrollHeight')

    browser.set_window_size(required_width, required_height)

    # path = '/Users/Elena/PycharmProjects/Artikel_'+str(article_uid)+'.png'
    path = 'screenshots/Artikel_'+str(article_uid)+'.png'

    # driver.save_screenshot(path)
    browser.find_element_by_tag_name('body').screenshot(path)

    browser.set_window_size(original_size['width'], original_size['height'])

browser.quit()
