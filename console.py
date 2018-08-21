# /usr/bin/env python
from selenium import webdriver
import selenium
import GxbManager as gm
import json
import threading
import time
import argparse
GXB_LOGIN = '''https://cas.gaoxiaobang.com/login?tenant_id=1039&service=https%3A%2F%2Fbh3773.gaoxiaobang.com%2F'''
helpString = '''GXB Manager Prototype
GXB MANAGER IS ONLY FOR STUDY

Command list:
h: display help.
g [target]: go to target webpage.
s: show current status of video.
p: play/stop current video.
a: answer dialog question.
n: jump to next video.
q: quit the program.
lg: login using username and password from user.json
ls: get a list of all videos' title.
ao: turn on auto class processer.
af: turn off auto class processer.
auto class processer can automatically solve in-video questions, start paused videos and skip discussions/exams.
'''
parser = argparse.ArgumentParser(description="Open GXB class manager")
parser.add_argument("-f", "--file", default="user.json",
                    help="json file for username and password")
parser.add_argument("-n", "--headless", default=False, action="store_true",
                    help="use headless chrome")
parser.add_argument("-m", "--mute", default=False,
                    action="store_true", help="mute all sounds from browser")
args = parser.parse_args()
autoClassShouldStop = False
chrome_options = webdriver.ChromeOptions()
if(args.mute):
    chrome_options.add_argument('--mute-audio')
if(args.headless):
    chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
driver = webdriver.Chrome(chrome_options=chrome_options)
driver.get('http://bh3773.gaoxiaobang.com')
print('>>', end='')
context = input()


def autoClassProcess():
    while(not autoClassShouldStop):
        time.sleep(5)
        # Ensure that the webpage is fully loaded.
        try:
            if(driver.execute_script('return document.readyState') != 'complete'):
                continue
            if(not gm.inVideoPage(driver)):
                if(gm.nextVideo(driver)):
                    print(
                        "[Notice] In exam or discuss page, forwarding to new video.")
                else:
                    print(
                        "[Error] Can't find video and not in special pages! Ensure you are in a valid page!")
            else:
                status = gm.status(driver)
                if(status.playStatus == 'paused'):
                    if(gm.needAnswer(driver)):
                        if(gm.answer(driver)):
                            print("[Notice] Auto answered in class question.")
                        else:
                            print("[Error] Video stopped for unknown reason!")
                    else:
                        if(gm.triggerPlay(driver)):
                            print("[Notice] Auto played paused video.")
                        else:
                            print("[Error] Can't play paused video!")
        except Exception as e:
            print('[Warning] ', e)


autoClass = threading.Thread(
    target=autoClassProcess, name='AutoClassProcessingThread')

while(context):
    output = ""
    if(context == 's'):
        output = repr(gm.status(driver))
    elif(context == 'h'):
        output = helpString
    elif(context == 'p'):
        if(gm.triggerPlay(driver)):
            output = ""
        else:
            output = "Not valid video page."
    elif(context == 'a'):
        if(gm.answer(driver)):
            output = ""
        else:
            output = "Not valid time to answer."
    elif(context == 'n'):
        if(gm.nextVideo(driver)):
            output = ""
        else:
            output = "Not valid video page or class reaches end."
    elif(context == 'lg'):
        username = None
        password = None
        try:
            with open(args.file, 'r') as f:
                djson = json.load(f)
                username = djson['username']
                password = djson['password']
        except json.JSONDecodeError:
            output = "Can't read user.json, login failed."
        if(username and password and gm.autoLogin(driver, GXB_LOGIN, username, password)):
            output = ""
        else:
            output = "Can't login. Maybe you have logged in?"
    elif(context == 'ls'):
        cl = gm.videoList(driver)
        if(cl):
            for i in cl:
                print(i.get_attribute('title'))

        else:
            output = "Not valid class page."
    elif(context == 'ao'):
        if(autoClass.is_alive()):
            output = "auto process already running!"
        else:
            autoClassShouldStop = False
            autoClass.start()
    elif(context == 'af'):
        autoClassShouldStop = True
    elif(context == 'q'):
        break
    elif(len(context.split(' ')) == 2 and context.split(' ')[0] == 'g'):
        try:
            driver.get(context.split(' ')[1])
            output = ""
        except selenium.common.exceptions.WebDriverException:
            output = "Not valid address!"
    else:
        output = "Unknown command. Input h to see all available commands."
    print(output)
    print('>>', end='')
    context = input()
driver.quit()
autoClassShouldStop = True
quit()
