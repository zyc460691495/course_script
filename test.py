from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from loguru import logger
import time

# def class_attribute_is(driver, locator, attribute_value):
#     if "playing" in driver.find_element(By.CLASS_NAME, "prism-big-play-btn").get_attribute("class").split():
#         print("播放中")
#     elif "pause" in driver.find_element(By.CLASS_NAME, "prism-big-play-btn").get_attribute("class").split():
#         print()

# chrome_options = Options()
# service = ChromeService(executable_path=r"C:\Program Files\chromedriver-win64\chromedriver.exe")
# chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
# driver = webdriver.Chrome(options=chrome_options, service=service)
# driver.implicitly_wait(2)
# js = "arguments[0].playbackRate = 6.0"
# video = driver.find_element(By.TAG_NAME, "video")
# print()
# driver.execute_script("arguments[0].setAttribute('playbackRate', 6.0)", video)
# video.get_attribute("playbackRate")

def waiting(cycle=20, delay=0.1):
    """旋转式进度指示"""
    for i in range(cycle):
        for ch in ['-', '\\', '|', '/']:
            print('\b%s' % ch, end='', flush=True)
            time.sleep(delay)

# waiting()

import os
import random
import time

import cv2
import numpy as np
import requests
from selenium.webdriver.common.action_chains import ActionChains


class Code():
    '''
    滑动验证码破解
    '''

    def __init__(self, slider_ele=None, background_ele=None, count=1, save_image=False):
        '''

        :param slider_ele:
        :param background_ele:
        :param count:  验证重试次数
        :param save_image:  是否保存验证中产生的图片， 默认 不保存
        '''

        self.count = count
        self.save_images = save_image
        self.slider_ele = slider_ele
        self.background_ele = background_ele

    def get_slide_locus(self, distance):
        distance += 8
        v = 0
        m = 0.3
        # 保存0.3内的位移
        tracks = []
        current = 0
        mid = distance * 4 / 5
        while current <= distance:
            if current < mid:
                a = 2
            else:
                a = -3
            v0 = v
            s = v0 * m + 0.5 * a * (m ** 2)
            current += s
            tracks.append(round(s))
            v = v0 + a * m
        # 由于计算机计算的误差，导致模拟人类行为时，会出现分布移动总和大于真实距离，这里就把这个差添加到tracks中，也就是最后进行一步左移。
        # tracks.append(-(sum(tracks) - distance * 0.5))
        # tracks.append(10)
        return tracks

    def slide_verification(self, driver, slide_element, distance):
        '''

        :param driver: driver对象
        :param slide_element: 滑块元祖
        :type   webelement
        :param distance: 滑动距离
        :type: int
        :return:
        '''
        # 获取滑动前页面的url网址
        start_url = driver.current_url
        print('滑动距离是: ', distance)
        # 根据滑动的距离生成滑动轨迹
        locus = self.get_slide_locus(distance)

        print('生成的滑动轨迹为:{},轨迹的距离之和为{}'.format(locus, distance))

        # 按下鼠标左键
        ActionChains(driver).click_and_hold(slide_element).perform()

        time.sleep(0.5)

        # 遍历轨迹进行滑动
        for loc in locus:
            time.sleep(0.01)
            ActionChains(driver).move_by_offset(loc, random.randint(-5, 5)).perform()
            ActionChains(driver).context_click(slide_element)

        # 释放鼠标
        ActionChains(driver).release(on_element=slide_element).perform()

        # # 判断是否通过验证，未通过下重新验证
        # time.sleep(2)
        # # 滑动之后的yurl链接
        # end_url = driver.current_url

        # if start_url == end_url and self.count > 0:
        #     print('第{}次验证失败，开启重试'.format(6 - self.count))
        #     self.count -= 1
        #     self.slide_verification(driver, slide_element, distance)

    def onload_save_img(self, url, filename="image.png"):
        '''
        下载图片并保存
        :param url: 图片网址
        :param filename: 图片名称
        :return:
        '''
        try:
            response = requests.get(url)
        except Exception as e:
            print('图片下载失败')
            raise e
        else:
            with open(filename, 'wb') as f:
                f.write(response.content)

    def get_element_slide_distance(self, slider_ele, background_ele, correct=0):
        '''
        根据传入滑块， 和背景的节点， 计算滑块的距离
        :param slider_ele: 滑块节点参数
        :param background_ele:  背景图的节点
        :param correct:
        :return:
        '''
        # 获取验证码的图片
        slider_url = slider_ele.get_attribute('src')
        background_url = background_ele.get_attribute('src')

        # 下载验证码链接
        slider = 'slider.jpg'
        background = 'background.jpg'

        self.onload_save_img(slider_url, slider)

        self.onload_save_img(background_url, background)

        # 进行色度图片, 转化为numpy 中的数组类型数据
        slider_pic = cv2.imread(slider, 0)
        background_pic = cv2.imread(background, 0)

        # 获取缺口数组的形状
        width, height = slider_pic.shape[::-1]

        # 将处理之后的图片另存
        slider01 = 'slider01.jpg'
        slider02 = 'slider02.jpg'
        background01 = 'background01.jpg'

        cv2.imwrite(slider01, slider_pic)
        cv2.imwrite(background01, background_pic)

        # 读取另存的滑块
        slider_pic = cv2.imread(slider01)

        # 进行色彩转化
        slider_pic = cv2.cvtColor(slider_pic, cv2.COLOR_BGR2GRAY)

        # 获取色差的绝对值
        slider_pic = abs(255 - slider_pic)
        # 保存图片
        cv2.imwrite(slider02, slider_pic)
        # 读取滑块
        slider_pic = cv2.imread(slider02)

        # 读取背景图
        background_pic = cv2.imread(background01)

        # 必脚两张图的重叠部分
        result = cv2.matchTemplate(slider_pic, background_pic, cv2.TM_CCOEFF_NORMED)

        # 通过数组运算，获取图片缺口位置
        top, left = np.unravel_index(result.argmax(), result.shape)

        # 背景图缺口坐标
        print('当前滑块缺口位置', (left, top, left + width, top + height))

        # 判读是否需求保存识别过程中的截图文件
        if self.save_images:
            loc = [(left + correct, top + correct), (left + width - correct, top + height - correct)]
            self.image_crop(background, loc)

        else:
            # 删除临时文件
            os.remove(slider01)
            os.remove(slider02)
            os.remove(background01)
            os.remove(background)
            os.remove(slider)
            # print('删除')
            # os.remove(slider)
        # 返回需要移动的位置距离
        return left

    def image_crop(self, image, loc):
        cv2.rectangle(image, loc[0], loc[1], (7, 249, 151), 2)
        cv2.imshow('Show', image)
        # cv2.imshow('Show2', slider_pic)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

