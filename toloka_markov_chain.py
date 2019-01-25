from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget, QGroupBox, QHBoxLayout, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import Qt
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from time import sleep
from subprocess import Popen
import pickle
import random
import sys
import os

ARTICLES, MUSIC, VIDEO, SHOP, \
WARTICLES, WMUSIC, WVIDEO, WSHOP, \
CARTICLES, CMUSIC, CVIDEO, CSHOP = [list() for i in range(12)]

DICTS = [ARTICLES, MUSIC, VIDEO, SHOP]
WORDS = [WARTICLES, WMUSIC, WVIDEO, WSHOP]
CHAINS = [CARTICLES, CMUSIC, CVIDEO, CSHOP]

def getDicts():
    global DICTS
    location = os.path.dirname(os.path.abspath(__file__))
    dictlist = [f"{location}\\dicts\\{item}" for item in ("ARTICLES.txt", "MUSIC.txt", 
    "VIDEO.txt", "SHOP.txt")]
    for count, item in enumerate(dictlist):
        try:
            with open(item, 'r', encoding="utf8") as file:
                for line in file:
                    if "\ufeff" in line:
                        line = line.replace("\ufeff", "")
                    DICTS[count].append(line.strip('\n'))
        except UnicodeDecodeError as e:
            print(e)

def getChain():
    global DICTS, WORDS, CHAINS
    for item in range(len(DICTS)):
        words = []
        for line in DICTS[item]:
            line = line.replace('\r', ' ').replace('\n', ' ')
            new_words = [word for word in line.split(' ') if word not in ['', ' ']]
            words = words + new_words
        chain = {}
        for ct, key_one in enumerate(words):
            if len(words) > ct + 2:
                key_two = words[ct + 1]
                word = words[ct + 2]
                if (key_one, key_two) not in chain:
                    chain[(key_one, key_two)] = [word]
                else:
                    chain[(key_one, key_two)].append(word)
        WORDS[item] = words
        CHAINS[item] = chain
        print(words, '\n', chain)

class BaseLayer(QWidget):
    trigger = pyqtSignal()

    def __init__(self):
        super().__init__()
        __screen = QDesktopWidget().screenGeometry(-1)
        self.height, self.width = __screen.height(), __screen.width()
        self.setGeometry((self.width * 50 / 100 - 200), (self.height * 50 / 100 - 100),400, 200)
        self.setFixedSize(400, 200)
        self.rectx, self.recty, self.rectw, self.recth = [0 for i in range(4)]
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.trigger.connect(self.releaseButton)
        self.framed = 0
        self.initUI()

    def initUI(self):
        self.vlay = QVBoxLayout()
        self.vlay_grid0 = QGroupBox()
        self.vlay_hlay0 = QHBoxLayout()

        self.vlay_hlay1 = QHBoxLayout()
        self.vlay_adapted = QGroupBox()

        self.launch = QPushButton("Launch selenium")
        self.launch.clicked.connect(self.selen)
        self.vlay_hlay0.addWidget(self.launch)
        
        self.articles1 = QPushButton("Article")
        self.articles1.clicked.connect(lambda art: self.insert(0))
        self.music1 = QPushButton("Music")
        self.music1.clicked.connect(lambda mu: self.insert(1))
        self.video1 = QPushButton("Video")
        self.video1.clicked.connect(lambda vi: self.insert(2))
        self.shops1 = QPushButton("Item")
        self.shops1.clicked.connect(lambda sho: self.insert(4))
        for item in [self.articles1, self.music1, self.video1, self.shops1]:
            self.vlay_hlay1.addWidget(item)

        self.vlay_adapted.setTitle("1-st adaptat")
        self.vlay_adapted.setStyleSheet(r"""
        QGroupBox{border: 1px solid gray;margin-top: 0.5em;font: 12px consolas;}QGroupBox::title {top: -7px;left: 10px;}""")
        self.vlay_adapted.setLayout(self.vlay_hlay1)
        
        self.vlay_grid0.setTitle("Main")
        self.vlay_grid0.setStyleSheet(r"""
        QGroupBox{border: 1px solid gray;margin-top: 0.5em;font: 12px consolas;}QGroupBox::title {top: -7px;left: 10px;}""")
        self.vlay_grid0.setLayout(self.vlay_hlay0)

        self.vlay.addWidget(self.vlay_grid0)
        self.vlay.addWidget(self.vlay_adapted)
        self.vlay_adapted.setEnabled(False)
        self.setLayout(self.vlay)
    
    def closeEvent(self, event):
        try:
            if not self.launch.isEnabled():
                self.driver.quit()
        except selenium.common.exceptions.WebDriverException:
            pass
        Popen("releasedriver.bat", shell=True)
        sys.exit(0)

    def selen(self):
        try:
            self.listener = InitListener(parent=self)
            chrome_options = Options()
            chrome_options.add_argument("user-data-dir=selenium") 
            chrome_options.add_argument("start-maximized")
            chrome_options.add_argument("--disable-infobars")
            path = os.path.dirname(os.path.realpath(__file__))
            self.driver = webdriver.Chrome(executable_path=f'{path}\\chromedriver.exe', options=chrome_options, service_log_path='NUL')
            self.driver.implicitly_wait(1000)
            self.driver.get("https://toloka.yandex.ru/")
            self.launch.setEnabled(False)
            self.launch.setText("Working...")
            self.vlay_adapted.setEnabled(True)
            self.listener.start()
        except WebDriverException:
            pass

    def releaseButton(self):
        self.launch.setEnabled(True)
        self.launch.setText("Launch selenium")
        self.vlay_adapted.setEnabled(False)

    def checkLink(self):
        link = self.driver.execute_script("return document.URL;")
        print(link)
        if not ("/task/" in link) and (link != "https://iframe-toloka.com/"):
            return 1
        else:
            return 0

    def findFrame(self):
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame(self.driver.find_element_by_tag_name("iframe"))

    def locatingTextarea(self):
        try:
            self.findFrame()
            findfocused = self.driver.find_elements_by_xpath("//*[@class='task task_focused']")
            #findfocused = self.driver.find_element_by_css_selector(".task.task_focused")
            if len(findfocused) > 0:
                findtext = findfocused[0].find_elements_by_xpath(".//*[@class='textarea__textarea']")
                if len(findtext) > 0:
                    return findtext
            else:
                return 1
        except WebDriverException as e:
            pass
    
    def genResponse(self, val):
        global WORDS, CHAINS
        words = WORDS[val]
        chain = CHAINS[val]
        rand = random.randint(0, len(words) - 2)
        try:
            key = (words[rand], words[rand + 1])
        except IndexError as e:
            print(e)
        sentence = key[0] + ' ' + key[1]
        while len(sentence) < 80:
            try:
                makeword = random.choice(chain[key])
                sentence += ' ' + makeword
                key = (key[1], makeword)
            except KeyError as e:
                break
        return sentence

    def insert(self, val):
        getCode = self.checkLink()
        try:
            if getCode == 0:
                getText = self.locatingTextarea()
                getResponse = str(self.genResponse(val))
                if getText != 1 and getText is not None:
                    getText[0].clear()
                    getText[0].send_keys(getResponse)
            else:
                pass
        except WebDriverException as e:
            pass

class InitListener(QThread):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent

    def run(self):
        while True:
            DISCONNECTED_MSG = 'Unable to evaluate script: disconnected: not connected to DevTools\n'
            try:
                if self.parent.driver.get_log('driver')[-1]['message'] == DISCONNECTED_MSG:
                    self.parent.trigger.emit()
                    break
            except IndexError:
                pass
            except WebDriverException:
                pass
            sleep(1)


Popen("releasedriver.bat", shell=True)
getDicts()
app = QApplication(sys.argv)
appe = BaseLayer()
getChain()
appe.show()
app.aboutToQuit.connect(app.deleteLater)
sys.exit(app.exec_())
