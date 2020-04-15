# -*- coding: utf-8 -*-

import platform
from pyvirtualdisplay import Display
from selenium import webdriver


if platform.system() == 'Linux':
    display = Display(visible=0, size=(1366, 768))
    display.start()
    architecture = '32' if platform.architecture()[0].startswith('32') else '64'
    geckodriver = 'drivers/geckodriver-linux' + architecture

elif platform.system() == 'Darwin':
    geckodriver = 'drivers/geckodriver-macos'

else:
    architecture = '64' if '64' in platform.machine() else '32'
    geckodriver = 'drivers/geckodriver-win' + architecture + '.exe'

print(geckodriver)

browser = webdriver.Firefox(executable_path=geckodriver)
browser.implicitly_wait(5)
