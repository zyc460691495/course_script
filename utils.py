import base64
import os
import random
import socket
import subprocess
import sys
import time

import requests
from selenium.webdriver import Keys
from loguru import logger

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


def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False  # 端口未被占用
        except socket.error as e:
            return True  # 端口已被占用

def start_debug_browser(debug_port):
    # 创建 Chrome WebDriver 实例
    # chrome.exe --remote-debugging-port=9222 --user-data-dir="D:\JetBrains\PyCharmProjects\course_script\temp"
    # netstat -ano|findstr "9222"

    # 假设Chrome在默认安装目录
    chrome_dir = r"C:\Program Files\Google\Chrome\Application"
    # 如果目录不存在，尝试其他位置
    if not os.path.exists(chrome_dir):
        chrome_dir = r"C:\Program Files (x86)\Google\Chrome\Application"

    if not os.path.exists(chrome_dir):
        logger.error(f"Chrome目录不存在: {chrome_dir}")
        sys.exit(1)

    # 完整命令序列
    full_command = f'cd /d "{chrome_dir}" && chrome.exe --remote-debugging-port=9222 --user-data-dir="D:\\JetBrains\\PyCharmProjects\\course_script\\temp"'

    try:
        # 启动Chrome
        chrome_process = subprocess.Popen(
            full_command,
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )

        logger.info(f"在目录 {chrome_dir} 中启动Chrome")
        time.sleep(3)

        # 检查端口
        result = subprocess.run(
            "netstat -ano | findstr {}".format(debug_port),
            shell=True,
            capture_output=True,
            text=True
        )

        logger.info("端口{}状态:".format(debug_port))
        logger.info(result.stdout if result.stdout else "未监听")
        return chrome_process

    except Exception as e:
        logger.error(f"执行出错: {e}")
        sys.exit(1)

port = 9222
print(f"Port {port} is open: {is_port_open(port)}")
