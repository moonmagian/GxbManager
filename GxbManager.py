from selenium import webdriver
import selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import re
STATUS_OUTPUT = \
    '''Video: {0}
Status: {1}
Time(sec): {2} / {3}'''

CLASS_REGEX = r'''https://bh3773.class.gaoxiaobang.com/class/(\d+)/unit/(\d+)/chapter/(\d+)'''
CLASS_STRING = '''https://bh3773.class.gaoxiaobang.com/class/{0}/unit/{1}/chapter/{2}'''
# Get VideoListIDs needs LOTS OF resources, cache them to lower CPU usage.
VLIDcache = {}


class Status:
    title = "TITLE"
    playStatus = "PLAYSTATUS"
    ctime = -1
    duration = -1
    error = False

    def __repr__(self):
        if(not self.error):
            return STATUS_OUTPUT.format(self.title, self.playStatus, str(self.ctime), str(self.duration))
        else:
            return "Not valid video page."


def videoList(driver: webdriver.chrome.webdriver.WebDriver):
    try:
        return list(filter(lambda x: x.get_attribute(
                'content_type') == 'Video', driver.find_elements_by_class_name("chapter-info")))
    except:
        return []


def autoLogin(driver: webdriver.chrome.webdriver.WebDriver, loginLink: str, username: str, passwd: str):
    try:
        driver.get(loginLink)
        driver.find_element_by_id('username').send_keys(username)
        driver.find_element_by_id('password').send_keys(passwd)
        driver.find_element_by_class_name('login_btn').click()
        return True
    except selenium.common.exceptions.NoSuchElementException:
        return False


def status(driver: webdriver.chrome.webdriver.WebDriver):
    '''
    Get current status of video page.

    :param driver: WebDriver, the WebDriver to get status
    :returns: Status, a Status object storing status information
    '''
    output = Status()
    try:
        videoPlayer = driver.find_element_by_id('video_player_html5_api')
        output.title = driver.find_element_by_class_name('chapter-title').text
        videoShell = driver.find_element_by_id('video_player')
        vsClass = videoShell.get_attribute('class')
        if(vsClass.find('vjs-paused') + 1):
            output.playStatus = 'paused'
        else:
            output.playStatus = 'playing'
        output.duration = videoPlayer.get_property('duration')
        output.ctime = videoPlayer.get_property('currentTime')
    except Exception:
        output.error = True
    finally:
        return output


def triggerPlay(driver):
    '''
    Trigger current play status.

    :param driver: WebDriver, the WebDriver to trigger
    :returns: Bool, if the trigger is successful
    '''
    try:
        videoPlayer = driver.find_element_by_class_name('video-js')
        videoPlayer.click()
        return True
    except Exception:
        return False


def needAnswer(driver: selenium.webdriver.chrome.webdriver.WebDriver):
    '''
    Check if a question is shown.

    :param driver: WebDriver, the WebDriver to check
    :returns: Bool, if a question is shown.
    '''
    f = driver.find_elements_by_class_name('correctAnswer')
    if(f):
        return True
    else:
        return False


def answer(driver: selenium.webdriver.chrome.webdriver.WebDriver):
    '''
    Answer in-video questions.

    :param driver: WebDriver, the WebDriver to answer
    :returns: Bool, if answer is successful
    '''
    try:
        answers = driver.find_element_by_class_name(
            'correctAnswer').get_attribute('data')
        correctArray = [ord(i) - ord('A') for i in answers]
        chooseName = 'gxb-icon-check'
        try:
            driver.find_element_by_class_name('gxb-icon-radio')
            chooseName = 'gxb-icon-radio'
        except selenium.common.exceptions.NoSuchElementException:
            pass
        for answer in correctArray:
            driver.find_elements_by_class_name(chooseName)[
                answer].click()
        driver.find_element_by_class_name('submit').click()
        play = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'player')))
        play.click()
        return True
    except:
        return False


def nextVideo(driver: webdriver.chrome.webdriver.WebDriver):
    match = re.match(CLASS_REGEX, driver.current_url)
    if(not match):
        return False
    videoIds = list(map(lambda x: x.get_attribute(
        'chapter_id'), videoList(driver)))
    try:
        # When the page is not video, append it to video list to get the nearest video.
        if(match.groups()[2] not in videoIds):
            videoIds.append(match.groups()[2])
            videoIds.sort()
        index = videoIds.index(match.groups()[2])
        if(index != len(videoIds) - 1):
            url = CLASS_STRING.format(
                *match.groups()[:-1], videoIds[index + 1])
            driver.get(url)
            return True
        else:
            return False
            # TODO: When the class ends. Raise a custom error and start a new class.
    except:
        return False


def inVideoPage(driver: webdriver.chrome.webdriver.WebDriver):
    match = re.match(CLASS_REGEX, driver.current_url)
    if(not match):
        return False
    if(match.groups()[0] not in VLIDcache.keys()):
        VLIDcache[match.groups()[0]] = list(map(lambda x: x.get_attribute(
            'chapter_id'), videoList(driver)))
    return(match.groups()[2] in VLIDcache[match.groups()[0]])
