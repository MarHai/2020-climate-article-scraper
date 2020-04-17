import time
from selenium import common
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from _config import zeit_user, zeit_password
from _browser import browser
from _database import cursor


print('Start: %d' % time.time())
outlet_signin = 'https://meine.zeit.de/anmelden?url=https%3A%2F%2Fwww.zeit.de%2Findex&entry_service=sonstige'
browser.get(outlet_signin)
browser.find_element_by_css_selector('#login_email').send_keys(zeit_user)
browser.find_element_by_css_selector('#login_pass').send_keys(zeit_password)
browser.find_element_by_css_selector('.submit-button').click()

try:
    frame = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.XPATH, '//*[starts-with(@id, "sp_message_iframe_")]')))
    browser.switch_to.frame(frame)
    akzeptieren = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'message-component')))
    time.sleep(3)
    akzeptieren.click()
    time.sleep(3)
    browser.switch_to.default_content()
    browser.refresh()
except (common.exceptions.NoSuchElementException, common.exceptions.TimeoutException):
    pass

cursor.execute('SELECT url, uid FROM article WHERE outlet = %s AND text IS NULL', ("zeit.de",))
if cursor.with_rows:
    articles = cursor.fetchall()
    print('%d lose Artikel in Datenbank gefunden' % (len(articles),))

    for article in articles:  
        artikel_url = article[0]
        article_uid = article[1]
        print(artikel_url)
        browser.get(artikel_url)

        try:
            read_on_same_page = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.LINK_TEXT, 'Auf einer Seite lesen')))
            if read_on_same_page:
                artikel_url = read_on_same_page.get_attribute('href')
                browser.get(artikel_url)
        except (common.exceptions.NoSuchElementException, common.exceptions.TimeoutException):
            pass

        try:
            article_title = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.article-heading')))
            if article_title:
                article_title = article_title.text
        except (common.exceptions.NoSuchElementException, common.exceptions.TimeoutException):
            article_title = ''

        try:
            article_text = browser.find_element_by_class_name('article-body')
            if article_text:
                article_text = article_text.text
        except common.exceptions.NoSuchElementException:
            article_text = ''
        
        try:
            publication_date = browser.find_element_by_class_name('metadata__date')
            if publication_date:
                publication_date = publication_date.get_attribute('datetime')
        except common.exceptions.NoSuchElementException:
            publication_date = ''
        
        kom = 'Ein Kommentar von'
        pro = 'Protokoll:'
        gast = 'Ein Gastbeitrag von'
        inte = 'Interview:'
        ana = 'Eine Analyse von'
        rez = 'Eine Rezension von'
        kol = 'Eine Kolumne von'
        ess = 'Ein Essay von'
        try:
            article_author = browser.find_element_by_class_name('metadata__source').text
            article_author = article_author.replace('Quelle: ', '').strip() # Lässt am Ende nur die Namen dort stehen
        except common.exceptions.NoSuchElementException:
            pass

        try:
            article_author = browser.find_element_by_class_name('byline').text
            article_author = article_author.replace(pro, '').replace(inte,"").replace(ana,'').replace(gast,'').replace(kom,'').replace(rez,'').replace(ess,'').strip()# Lässt am Ende nur die Namen dort stehen
        except common.exceptions.NoSuchElementException:
            pass
            
        try:
            article_author = browser.find_element_by_class_name('column-heading__name').text
            article_author = article_author.replace(kol, '').replace(' und', ',').strip()# Lässt am Ende nur die Namen dort stehen
        except common.exceptions.NoSuchElementException:
            pass
            
        try:
            article_author= browser.find_element_by_class_name('article-header__byline').text
            article_author = article_author.replace(pro, '').replace(inte,"").replace(ana,'').replace(gast,'').replace(kom,'').replace(rez,'').replace(ess,'').strip()# Lässt am Ende nur die Namen dort stehen
        except common.exceptions.NoSuchElementException:
            pass
        
        try:
            article_presentation = browser.find_element_by_class_name('metadata__source').text
            article_presentation = ''
        except common.exceptions.NoSuchElementException:
                pass    
        
        try:
            article_presentation = browser.find_element_by_class_name('byline').text
            if kom in article_presentation:
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
        
        try:
            article_presentation = browser.find_element_by_class_name('column-heading__name').text
            if kol in article_presentation:
                    article_presentation = "Kolumne"
            else:
                article_presentation = ''
        except common.exceptions.NoSuchElementException:
                pass    
            
        try:
            article_presentation = browser.find_element_by_class_name('article-header__byline').text
            if kom in article_presentation:
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
                article_presentation = 'Essay'
            else:
                article_presentation = ''
        except common.exceptions.NoSuchElementException:
                pass
                 
        cursor.execute('UPDATE article SET scrape_date = %s, title = %s, text = %s,publication_date =%s, author = %s, presentation = %s WHERE uid = %s ',
                      (
                           int(time.time()),  # aktueller Zeitstempel noch nicht umgewandelt
                           article_title,
                           article_text,
                           publication_date,
                           article_author or '',
                           article_presentation or '',
                           article_uid))

        if cursor.rowcount > 0:
            print('Artikel %d für die ZEIT erfolgreich aktualisiert' % (article_uid,))

        try:
            num_of_comment_pages = int(browser.find_element_by_css_selector('ul.pager__pages > li.pager__page:last-child').text)
        except:
            num_of_comment_pages = 1

        last_rank = 0
        for comment_page in range(num_of_comment_pages):
            if comment_page != 0:
                browser.get(artikel_url + '?page=' + str(comment_page+1) + '#comments')

            try:
                load_reply_comments = WebDriverWait(browser, 5).until(EC.presence_of_all_elements_located((By.PARTIAL_LINK_TEXT, 'Weitere Antworten anzeigen')))
                for a in load_reply_comments:
                    a.click()
            except (common.exceptions.NoSuchElementException, common.exceptions.TimeoutException):
                pass

            comments_top = browser.find_elements_by_css_selector('#js-comments-body article.comment.js-comment-toplevel')
            for i, comment_top in enumerate(comments_top):
                comment_author = comment_top.find_element_by_class_name('comment-meta__name').text
                comment_title = comment_top.find_element_by_class_name('comment__body').text
                comment_text = comment_top.find_element_by_class_name('comment__body').text
                last_rank = last_rank + 1
                cursor.execute('INSERT INTO comment (article_uid, `rank`, commenter, text) VALUES (%s, %s, %s, %s)',
                               (article_uid, last_rank, comment_author, comment_text))
                if cursor.lastrowid:
                    comment_top_uid = cursor.lastrowid
                    print('Hauptkommentar für die ZEIT gespeichert unter der ID %d' % (comment_top_uid,))

                    zeit_comment_level_id = comment_top.get_attribute('data-ct-row')
                    comments_sub = browser.find_elements_by_css_selector('#js-comments-body article.comment.comment--indented[data-ct-row="' + zeit_comment_level_id + '"]')
                    for j, comment_sub in enumerate(comments_sub):
                        comment_author = comment_sub.find_element_by_class_name('comment-meta__name').text
                        comment_text = comment_sub.find_element_by_class_name('comment__body').text
                        cursor.execute('INSERT INTO comment (article_uid, `rank`, commenter, text, is_reply_to) '
                                       'VALUES (%s, %s, %s, %s, %s)',
                                       (article_uid, j+1, comment_author, comment_text, comment_top_uid))
                        if cursor.lastrowid:
                            uid = cursor.lastrowid
                            print('Antwortkommentar für die ZEIT gespeichert unter der ID %d' % (uid,))

        screenshot_name = 'screenshots/Artikel_' + str(article_uid) + '.png'
        original_size = browser.get_window_size()
        required_width = browser.execute_script('return document.body.parentNode.scrollWidth')
        required_height = browser.execute_script('return document.body.parentNode.scrollHeight')
        browser.set_window_size(required_width, required_height)
        browser.find_element_by_tag_name('body').screenshot(screenshot_name)
        browser.set_window_size(original_size['width'], original_size['height'])
        print('Screenshot für die ZEIT unter %s gespeichert \n\n' % (screenshot_name,))

browser.close()
print('Ende: %d' % time.time())
