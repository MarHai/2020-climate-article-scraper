import time
from selenium import common
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from _config import welt_user, welt_password
from _browser import browser
from _database import cursor, insert_comment, update_article


print('Start: %d' % time.time())


def showAllComments(comment_container):
    try:
        comment_button = comment_container.find_element_by_xpath('div[last()]/a/span')
        comment_button.click()
        time.sleep(0.5)
        showAllComments(comment_container)
    except common.exceptions.NoSuchElementException:
        pass


browser.get('https://secure.mypass.de/sso/web-fullpage/login?service=https%3A%2F%2Flo.la.welt.de%2Fuser%2Fredirect%3FredirectUrl%3Dhttps%253A%252F%252Fwww.welt.de%252F&wt_eid=2155419246963806176&wt_t=1579609313997')
username = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#username')))
username.send_keys(welt_user)
browser.find_element_by_css_selector('#password').send_keys(welt_password)
browser.find_element_by_css_selector('#proceedButton').click()
time.sleep(5)

cursor.execute('SELECT url, uid FROM article WHERE outlet = %s AND text IS NULL', ("welt.de",))
if cursor.with_rows:
    articles = cursor.fetchall()
    print('%d lose Artikel in Datenbank gefunden' % (len(articles),))
else:
    articles = []
    print('keine Artikel in der Datenbank gefunden')

for i, article in enumerate(articles):
    article_uid = article[1]
    url = article[0]
    print(url)

    cursor.execute('SELECT COUNT(*) FROM article WHERE uid = %s AND text IS NULL' % article_uid)
    double_check = cursor.fetchone()
    if double_check[0] == 0:
        print('Artikel inzwischen verarbeitet')
        continue

    try:
        browser.get(url)
    except common.exceptions.TimeoutException:
        print('Artikel lädt nihct')
        update_article(article_uid, '', 'Artikel nicht mehr verfügbar', '', '', '')
        continue

    browser.execute_script('document.querySelectorAll(".as-oil-content-overlay").forEach(function(el) { el.remove() })')

    try:
        agb = browser.find_element_by_class_name('max-content-wrapper')
        if agb:
            agb.find_element_by_xpath('a').click()
    except common.exceptions.NoSuchElementException:
        pass

    try:
        publication_date = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'c-publish-date')))
        if publication_date:
            publication_date = publication_date.get_attribute('datetime')
    except (common.exceptions.NoSuchElementException, common.exceptions.TimeoutException):
        publication_date = ""

    if publication_date == '':
        try:
            publication_date = browser.find_element_by_tag_name('time')
            if publication_date:
                publication_date = publication_date.get_attribute('datetime')
        except common.exceptions.NoSuchElementException:
            publication_date = ""

    try:
        article_presentation = browser.find_element_by_css_selector('.rf-o-section')
        if article_presentation:
            article_presentation = article_presentation.text
    except common.exceptions.NoSuchElementException:
        article_presentation = ""

    try:
        article_title = browser.find_element_by_css_selector('.rf-o-headline')
        if article_title:
            article_title = article_title.text
    except common.exceptions.NoSuchElementException:
        article_title = ''

    try:
        article_author = browser.find_element_by_class_name('c-author__by-line')
        if article_author:
            article_author = article_author.text
            article_author = article_author.replace('Von ', '')
    except common.exceptions.NoSuchElementException:
        article_author = ''

    try:
        article_teaser = browser.find_element_by_css_selector('.c-summary__intro')
        if article_teaser:
            article_teaser = article_teaser.text
    except common.exceptions.NoSuchElementException:
        article_teaser = ''

    article_text = article_teaser + "\n\n"
    try:
        paragraphs = browser.find_elements_by_css_selector('.c-article-text p:not(.o-element__text)')
        for paragraph in paragraphs:
            article_text = article_text + paragraph.text + '\n\n'
    except common.exceptions.NoSuchElementException:
        pass

    update_article(article_uid, article_title, article_text, publication_date, article_author, article_presentation)

    try:
        showAllComments(browser.find_element_by_xpath("//div[@data-qa='comments']"))
        comment_boxes = browser.find_elements_by_xpath("//div[@data-qa='comments']/div")
        for j, box in enumerate(comment_boxes):
            try:
                show_more_comments = box.find_element_by_xpath("div[last()]/div[2]/a")
                show_more_comments.click()
            except common.exceptions.ElementClickInterceptedException:
                browser.execute_script('document.querySelectorAll(".c-dialog__shadow").forEach(function(el) { el.remove() })')
            except common.exceptions.NoSuchElementException:
                pass

            comments = box.find_elements_by_xpath(".//div[@data-qa='comment']")
            first_comment_id = 0
            for k, comment in enumerate(comments):
                try:
                    kommentare_autor = comment.find_element_by_xpath("div[1]/div[2]/div/a")
                    if kommentare_autor:
                        kommentare_autor = kommentare_autor.text
                except common.exceptions.NoSuchElementException:
                    kommentare_autor = ''

                try:
                    kommentare_text = comment.find_element_by_xpath("div[3]")
                    if kommentare_text:
                        kommentare_text = kommentare_text.text
                except common.exceptions.NoSuchElementException:
                    kommentare_text = ''

                if k == 0:
                    first_comment_id = insert_comment(article_uid, j+1, kommentare_autor, kommentare_text)
                else:
                    insert_comment(article_uid, j + 1, kommentare_autor, kommentare_text, '', first_comment_id)
    except common.exceptions.NoSuchElementException:
        pass

    original_size = browser.get_window_size()
    required_width = browser.execute_script('return document.body.parentNode.scrollWidth')
    required_height = browser.execute_script('return document.body.parentNode.scrollHeight')
    browser.set_window_size(required_width, required_height)
    path = 'screenshots/Artikel_'+str(article_uid)+'.png'
    browser.find_element_by_tag_name('body').screenshot(path)
    browser.set_window_size(original_size['width'], original_size['height'])
    print('Screenshot für die Welt unter %s gespeichert \n\n' % (path,))

browser.quit()
print('Ende: %d' % time.time())
