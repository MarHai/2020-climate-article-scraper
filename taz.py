# -*- coding: utf-8 -*-

import time
from selenium import common
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from _browser import browser
from _database import cursor, update_article, insert_comment


print('Start: %d' % time.time())
cursor.execute('SELECT url, uid FROM article WHERE outlet = %s AND text IS NULL', ("taz.de",))
if cursor.with_rows:
    articles = cursor.fetchall()
    print('%d lose Artikel in Datenbank gefunden' % (len(articles),))

    for article in articles:  
        artikel_url = article[0]
        article_uid = article[1]
        
        browser.get(artikel_url)
        print(artikel_url)
        
        try:
            paywall = WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.tzi-paywahl__close a')))
            paywall.click()
        except (common.exceptions.NoSuchElementException, common.exceptions.TimeoutException):
            pass
        
        try:
            article_title = browser.find_element_by_css_selector('.news.article h1:nth-child(1) > span:not(.hide):not(.kicker)').text
        except common.exceptions.NoSuchElementException:
            article_title = ''
            
        try:
            article_text = ''
            article_paragraphs = browser.find_elements_by_css_selector('.news.article p.intro, .news.article article > p.article')
            for p in article_paragraphs:
                article_text += p.text + '\n\n'
        except common.exceptions.NoSuchElementException:
            article_text = ''

        try:
            publication_date = browser.find_element_by_css_selector('.news .date')
            try:
                publication_date = publication_date.get_attribute('content')
            except:
                publication_date = publication_date.text
        except common.exceptions.NoSuchElementException:
            publication_date = ''
            
        try:
            article_author = []
            article_authors = browser.find_elements_by_css_selector('.news.article .author [itemprop="name"]')
            for author in article_authors:
                if author.text not in article_author:
                    article_author.append(author.text)
            article_author = ', '.join(article_author)
        except common.exceptions.NoSuchElementException:
            article_author = ''
        
        try:
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
        except common.exceptions.NoSuchElementException:
            article_presentation = ''

        update_article(article_uid, article_title, article_text, publication_date, article_author, article_presentation)

        try:
            browser.execute_script('window.scrollTo(0, Math.max(document.documentElement.scrollHeight, document.body.scrollHeight, document.documentElement.clientHeight));')
            time.sleep(2)
        except:
            pass

        try:
            browser.find_element_by_css_selector('.community .showAll.submit').click()
            time.sleep(2)
        except:
            pass
        
        comments_main = browser.find_elements_by_css_selector('.community .body ul.sectbody > li')
        for j, comment_main in enumerate(comments_main):
            try:
                kommentar_autor= comment_main.find_element_by_css_selector('.author.person').text
            except common.exceptions.NoSuchElementException:
                kommentar_autor = ''

            try:
                kommentar_text= comment_main.find_element_by_css_selector('.objlink.nolead').text
            except common.exceptions.NoSuchElementException:
                kommentar_text = ''

            comment_main_uid = insert_comment(article_uid, (j+1), kommentar_autor, kommentar_text)
            if comment_main_uid:
                comments_replies = comment_main.find_elements_by_css_selector('ul.thread > li')
                for k, comment_reply in enumerate(comments_replies):
                    try:
                        kommentar_autor = comment_reply.find_element_by_css_selector('.author.person').text
                    except common.exceptions.NoSuchElementException:
                        kommentar_autor = ''

                    try:
                        kommentar_text = comment_reply.find_element_by_css_selector('.objlink.nolead').text
                    except common.exceptions.NoSuchElementException:
                        kommentar_text = ''

                    insert_comment(article_uid, (k+1), kommentar_autor, kommentar_text, '', comment_main_uid)

        screenshot_name = 'screenshots/Artikel_' + str(article_uid) + '.png' # baut den Name des Screentshots zusammen
        original_size = browser.get_window_size()
        required_width = browser.execute_script('return document.body.parentNode.scrollWidth')
        required_height = browser.execute_script('return document.body.parentNode.scrollHeight')
        browser.set_window_size(required_width, required_height)
        browser.find_element_by_tag_name('body').screenshot(screenshot_name)
        browser.set_window_size(original_size['width'], original_size['height'])
        print('Screenshot für die taz unter %s gespeichert \n\n' % (screenshot_name,))

browser.close()
print('Ende: %d' % time.time())
