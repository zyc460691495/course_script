import base64
import os
import random
import sys
import re
import cv2
import requests
from selenium import webdriver
from selenium import common
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from loguru import logger
import time
import ddddocr

logger.add("app.log", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}")


def delayed_input(ele, text, interval=0.1):
    ele.send_keys(Keys.CONTROL + 'a')  # 全选
    ele.send_keys(Keys.BACKSPACE)  # 删除
    for word in text:
        ele.send_keys(word)
        time.sleep(random.randint(int(interval * 500), int(interval * 1500)) / 1000)


def save_data_url_image(data_url, filename):
    try:
        if 'base64,' in data_url:
            # 分离出 base64 部分
            base64_data = data_url.split('base64,')[1]
            # 解码并保存
            image_data = base64.b64decode(base64_data)
            with open(filename, 'wb') as f:
                f.write(image_data)
        else:
            response = requests.get(data_url)
            with open(filename, 'wb') as f:
                f.write(response.content)

        logger.info("图片保存成功：{}".format(filename))
    except Exception as e:
        logger.error(str(e))
        logger.error("图片保存失败：{}".format(filename))
        sys.exit(1)


class CourseScript():

    def __init__(self, driver_path=None, debug_port=None, mode="auto"):

        if driver_path is None:
            driver_path = r"./chromedriver-win64/chromedriver.exe"
        if debug_port is None:
            debug_port = 9222
        # 初始化
        logger.info("正在初始化")
        chrome_options = Options()
        service = ChromeService(executable_path=driver_path)
        # chrome_options.add_experimental_option("debuggerAddress", "localhost:{}".format(debug_port))
        # chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        self.driver = webdriver.Chrome(options=chrome_options, service=service)
        self.action = ActionChains(self.driver)
        self.wait = WebDriverWait(self.driver, 10)
        # 创建 Chrome WebDriver 实例
        # chrome.exe --remote-debugging-port=9222 --user-data-dir="D:\JetBrains\PyCharmProjects\course_script\temp"
        # netstat -ano|findstr "9222"
        self.ddddocr = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
        self.driver.get("https://pc.kmelearning.com/jsncxyslhs/home/login")
        self.driver.refresh()

        init_wait_time = 10
        while True:
            try:
                self.driver.implicitly_wait(init_wait_time)
                logger.info("初始化完成")
                break
            except Exception:
                logger.error("页面加载超时，尝试重新加载，预计等待时长：{}".format(init_wait_time))
                self.driver.refresh()
                init_wait_time = 5 + init_wait_time

        if mode == "auto":
            self.login()

    def login(self, username_str=None, password_str=None):

        if not self.driver.current_url.endswith("login"):
            return
        if username_str is None:
            username_str = "32083020020816127X"
        if password_str is None:
            password_str = "zycxmm16127X"
        self.wait.until(
            EC.presence_of_element_located((By.ID, "login-box"))
        )
        username = self.driver.find_element(By.ID, "1")
        delayed_input(username, username_str)
        logger.info("账号输入完成")
        password = self.driver.find_element(By.ID, "2")
        delayed_input(password, password_str)
        logger.info("密码输入完成")
        agreement = self.driver.find_element(By.CLASS_NAME, "ant-checkbox-input")
        if not agreement.is_selected():
            agreement.click()
            logger.info("已勾选协议")
        login = self.driver.find_element(By.CLASS_NAME, "ant-btn")
        login.click()
        logger.info("已提交，即将进入滑块验证码")
        self.slide_verification()

    def slide_verification(self):
        self.wait.until(EC.visibility_of(self.driver.find_element(By.ID, "aliyunCaptcha-window-popup")))

        slider = self.driver.find_element(By.ID, "aliyunCaptcha-sliding-slider")
        self.human_drag(self.get_slide_distance(), slider)
        time.sleep(3)
        msg = self.driver.find_element(By.ID, "aliyunCaptcha-sliding-text").text
        if msg.startswith("验证通过"):
            logger.success("滑块验证通过")
            return
        else:
            # 循环验证
            while True:
                if msg.startswith("请拖动滑块完成拼图") or msg.startswith("验证失败"):
                    logger.error("滑块验证失败，正在重试")
                    slider = self.driver.find_element(By.ID, "aliyunCaptcha-sliding-slider")
                    self.human_drag(self.get_slide_distance(), slider)
                    time.sleep(1)
                    msg = self.driver.find_element(By.ID, "aliyunCaptcha-sliding-text").text
                    if msg.startswith("验证通过"):
                        logger.success("滑块验证通过")
                        break
                if not self.driver.current_url.endswith("login"):
                    logger.success("滑块验证通过")
                    break

    def get_slide_distance(self, save_img=True):
        # 获取图片
        slider_img = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "aliyunCaptcha-puzzle"))
        )

        background_img = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "aliyunCaptcha-img"))
        )

        slider_url = slider_img.get_attribute('src')
        background_url = background_img.get_attribute('src')

        slider_png_save_path = "slider.png"
        background_png_save_path = "background.png"
        save_data_url_image(slider_url, slider_png_save_path)
        save_data_url_image(background_url, background_png_save_path)
        slider = open("slider.png", "rb").read()
        background = open("background.png", "rb").read()
        res = self.ddddocr.slide_match(slider, background, simple_target=False)
        distance = res["target"][0]
        return distance

    def human_drag(self, distance, slider):
        self.driver.implicitly_wait(4)

        # 点击并按住滑块
        self.wait.until(EC.element_to_be_clickable((By.ID, "aliyunCaptcha-sliding-slider")))
        self.action.click_and_hold(slider).perform()
        puzzle_block = self.driver.find_element(By.ID, "aliyunCaptcha-puzzle")
        # 50 109
        # 100 157
        # 150 195
        # 200 227
        # 225 241
        factor = 1
        if distance <= 50:
            factor = 2
        elif distance <= 100:
            factor = 1.5
        elif distance <= 150:
            factor = 1.33
        elif distance <= 200:
            factor = 1.13
        elif distance <= 25:
            factor = 1.07
        self.action.move_by_offset(distance * factor, 0).perform()
        bias = 3

        while True:
            puzzle_block_move_dis = float(puzzle_block.get_attribute("style").split(";")[0][6:][:-2])
            y_offset = random.randint(-2, 2)
            if distance - puzzle_block_move_dis > 0:
                if distance - puzzle_block_move_dis > 10:
                    span = 10
                elif distance - puzzle_block_move_dis > 5:
                    span = 5
                elif distance - puzzle_block_move_dis > 2:
                    span = 2
                else:
                    span = 0.5
            else:
                if puzzle_block_move_dis - distance > 10:
                    span = -10
                elif puzzle_block_move_dis - distance > 5:
                    span = -5
                elif puzzle_block_move_dis - distance > 2:
                    span = -2
                else:
                    span = -0.5
            # 执行移动
            puzzle_block_move_dis += span
            self.action.move_by_offset(span, y_offset).perform()
            puzzle_block_move_dis = float(puzzle_block.get_attribute("style").split(";")[0][6:][:-2])
            logger.info("正在调整，距离" + str(distance - puzzle_block_move_dis))
            if abs(distance - puzzle_block_move_dis) <= bias:
                break

        self.action.release().perform()

    def start(self):
        if self.driver.current_url.endswith("index"):
            logger.info("当前位置：" + "首页")
            nav = self.driver.find_element(By.XPATH, "//*[@id='homeIndex']/div/div[2]/div/div/div/div/div/div[8]")
            nav.click()
            logger.info("正在进入" + "个人中心")
            self.wait.until(EC.url_contains("course"))

        if self.driver.current_url.endswith("course"):
            logger.info("当前位置：" + "个人中心")
            item = self.driver.find_element(By.XPATH,
                                            "//*[@id='root']/div[3]/div/div[2]/div[2]/div[1]/div[2]/div/div[3]")
            item.click()
            logger.info("正在进入：" + "我的任务")
            self.wait.until(EC.url_contains("myTask"))

        if self.driver.current_url.endswith("myTask"):
            logger.info("当前位置：" + "我的任务")
            tasks = self.driver.find_elements(By.CLASS_NAME, "index-module-item")
            if len(tasks) <= 0:
                logger.info("无学习任务，直接退出")
                sys.exit(0)

            for task in tasks:
                if task.text.__contains__("盱眙"):
                    task.click()
                    logger.info("正在进入：" + "".join(task.text.split()))
                    self.wait.until(EC.url_contains("courseplay"))
                    self.driver.implicitly_wait(4)
                    button = self.driver.find_element(By.CLASS_NAME, "studyButton")
                    button.click()
                    self.study()
                else:
                    logger.info("非目标学习任务，跳过")

    def study(self):
        self.driver.implicitly_wait(4)
        activities = self.driver.find_elements(By.CLASS_NAME, "panelContent")
        for activity_idx, activity in enumerate(activities):
            try:
                activity.get_attribute("class")
            except Exception:
                activity = self.driver.find_elements(By.CLASS_NAME, "panelContent")[activity_idx]

            if len(activity.find_elements(By.TAG_NAME, "i")) == 1:
                logger.info(activity.text.split()[0] + "已学习直接跳过")
                continue
            logger.info("正在进入" + activity.text.split()[0])
            activity.click()
            self.driver.implicitly_wait(4)
            courses = self.driver.find_elements(By.CLASS_NAME, "course-chapters-section")
            courses_done = self.driver.find_elements(By.CLASS_NAME, "done-icon")
            for course_idx, (course, course_done) in enumerate(zip(courses, courses_done)):
                try:
                    course_done.get_attribute("class")
                except Exception:
                    course = self.driver.find_elements(By.CLASS_NAME, "course-chapters-section")[course_idx]
                    course_done = self.driver.find_elements(By.CLASS_NAME, "done-icon")[course_idx]

                if "anticon" in course_done.get_attribute("class").split():
                    logger.info(course.text.split()[0] + "已学习直接跳过")
                    continue

                course.click()
                self.driver.implicitly_wait(4)
                try:
                    self.driver.find_element(By.CLASS_NAME, "prism-big-play-btn").click()
                except Exception:
                    self.driver.find_element(By.CLASS_NAME, "ant-modal-root")
                    self.driver.find_element(By.CLASS_NAME, "confirm").click()
                    self.driver.find_element(By.CLASS_NAME, "prism-big-play-btn").click()
                logger.info("正在播放视频")
                self.driver.implicitly_wait(2)
                video = self.driver.find_element(By.TAG_NAME, "video")
                # cur_time = video.get_attribute("currentTime")
                # var video = document.querySelector('video')
                # console.log(video.attributes)
                total_time = video.get_attribute("duration")
                playback_rate = 6.0
                logger.info("开始加速x{}".format(playback_rate))
                js = "arguments[0].playbackRate = {}".format(playback_rate)
                self.driver.execute_script(js, video)
                self.driver.implicitly_wait(4)
                logger.info("最多等待时长" + str(float(total_time) / 6 + 1))

                wait = WebDriverWait(self.driver, float(total_time))
                wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "prism-big-play-btn")))
                logger.info("视频播放结束，正在切换")
                self.driver.implicitly_wait(4)
            self.driver.find_element(By.CLASS_NAME, "back-btn").click()
            self.driver.implicitly_wait(2)


if __name__ == '__main__':
    script = CourseScript()
    script.start()
