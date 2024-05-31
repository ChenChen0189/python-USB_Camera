# !/usr/bin/python3
# -*- coding: UTF-8 -*-

import cv2
import os
import time
import logging
import sys
import pygame.camera
from rich.logging import RichHandler


def logging_init() -> None:
    """ logger初始化. """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(RichHandler(rich_tracebacks=True,
                                  tracebacks_show_locals=True,
                                  log_time_format="[%Y/%m/%d %H:%M:%S]",
                                  keywords=['Camera'],
                                  omit_repeated_times=False))


def create_directory():
    """在脚本同级创建命名为Picture的目录, 然后脚本每次执行时会创建新的子目录, 并以时间戳来命名"""
    main_dir = "Pictures"
    current_dir = os.getcwd()
    main_dir_path = os.path.join(current_dir, main_dir)
    
    # 如果主目录不存在，则创建它
    if not os.path.exists(main_dir_path):
        os.makedirs(main_dir_path)
    
    # 获取当前时间，并格式化为字符串（年月日_时分秒）
    time_str = time.strftime("%Y%m%d_%H%M%S")
    sub_dir_path = os.path.join(main_dir_path, time_str)
    
    # 创建子目录
    os.makedirs(sub_dir_path)
    return sub_dir_path

def show_and_select_camera():
    """检测、显示可用摄像头，并返回手动所选择Camera的编号。
    
    使用 pygame 来检测设备连接的摄像头列表，如果没有检测到摄像头，程序将打印提示信息并退出。
    如果检测到摄像头，函数将打印出可用的摄像头列表和对应的 ID。
    """

    try:
        pygame.camera.init()     # 初始化 pygame 的摄像头模块
        camera_list = pygame.camera.list_cameras()  # 获取设备上的摄像头列表
    except Exception as e:
        logging.error(f"Failed to initialize cameras or list cameras: {e}")
        sys.exit(1) 

    if not camera_list:
        logging.error("Do not find any cameras.")
        sys.exit(1)
    
    cameras = dict(enumerate(camera_list))  # 创建 ID 到摄像头名称的映射
    cameras_num = len(cameras)
    logging.info(f"Available Cameras as follow, Please choose one: (range: [0-{cameras_num-1}])")
    logging.info('{:=>50}'.format(''))
    for id, dev in cameras.items():
        logging.info(f"{id} : {dev}")
    logging.info('{:=>50}'.format(''))

    index = int(input(f'Please select the camera index from [0-{cameras_num-1}]:'))
    if 0 <= index < cameras_num:
        camera = cameras[index] 
        logging.info(f'You selection is: [ {index}: {camera} ]')
        return index
    else:
        logging.error(f'Out of the selection range, please select again!')
        sys.exit(1) 


class USBCamera:
    def __init__(self, device_index=0, frame_resolution=(1280, 720), frame_rate=30):
        """
        初始化 USB 摄像头。

        :param device_index: 设备索引，通常默认摄像头是 0。
        :param frame_resolution: 分辨率，以元组形式 (宽度, 高度)。
        :param frame_rate: 摄像头的帧率。
        """
        self.device_index = device_index
        self.frame_resolution = frame_resolution
        self.frame_rate = frame_rate
        self.camera = None

    def open_camera(self):
        """尝试打开摄像头并设置分辨率与帧率。"""
        try:
            self.camera = cv2.VideoCapture(self.device_index)
            if not self.camera.isOpened():
                self.camera.open(self.device_index)
            
            # 增加延时保护
            time.sleep(1)

            # 设置摄像头分辨率
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_resolution[1])
            # 设置摄像头帧率
            self.camera.set(cv2.CAP_PROP_FPS, self.frame_rate)
            # 尝试设置自动对焦
            self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)

            logging.info(f"Initial Camera with configuration: index: {self.device_index}, "
                         f"resolution: {self.frame_resolution}, "
                         f"frame rate: {self.frame_rate}fps")
        except Exception as e:
            logging.error(f"Failed to open the camera: {e}")

    def show_live_camera(self, timeout=60):
        """
        检测指定 camera 状态，并有 60 秒画面出图，进行镜头位置调整
        :return: None
        """
        act_frame_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        act_frame_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        act_frame_fps = int(self.camera.get(cv2.CAP_PROP_FPS))
        print(f"Actual camera info: {act_frame_width}x{act_frame_height}@{act_frame_fps}fps")
        start_time = time.time()
        while True:
            # 计算剩余的倒计时时间，使用 60 进制
            elapsed_time = time.time() - start_time
            remaining_time = max(0, int(timeout - elapsed_time))
            remaining_minute = remaining_time // 60
            remaining_second = remaining_time % 60
            countdown_clock = f"Countdown Clock: {remaining_minute:02d}:{remaining_second:02d}"
            # 读取图像
            ret, frame = self.camera.read()
            if not ret:     # 判断是否可以收到 camera frame，不能接收报错退出
                self.camera.release()
                logging.error(f"Can not receive camera_id:{self.device_index} frame")
                sys.exit(1)
            # 在帧上添加文本
            cv2.putText(frame, f'Camera ID: {self.device_index}', (25, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Frame Info: {act_frame_width}x{act_frame_height}@{act_frame_fps}fps", (25, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, countdown_clock, (25, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, f'Enter "q" to close windows', (25, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
            cv2.imshow('frame', frame)
            # 时间超时关闭
            if cv2.waitKey(1) == ord('q') or elapsed_time > timeout:
                break
        cv2.destroyAllWindows()
        cv2.waitKey(1)

    def take_picture(self, save_path=None, test_case_name=None, count=None, pic_mark=False):
        """
        拍照并保存图像。
        :param save_path: 图像保存路径。
        :param test_case_name: 测试用例名称，用于命名图片。
        :param count: 测试用例名称中照片编号，用于命名图片。默认是空
        :param pic_mark: 照片左上角添加水印，默认是不启动
        :return: None
        """
        if self.camera is None or not self.camera.isOpened():
            logging.warning("Camera is not opened. Trying to open it...")
            self.open_camera()

        try:
            ret, frame = self.camera.read()
            if ret:
                # 获取当前时间并格式化为字符串
                now_time = time.strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(save_path, f"{test_case_name}_{now_time}_{count}.jpg")
                cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                logging.info(f"Image saved as: {test_case_name}_{now_time}_{count}.jpg")
                if pic_mark:
                    self.add_pic_mark(filename, f"{test_case_name}_{now_time}_{count}")
            else:
                logging.warning("Failed to capture image from camera.")
        except Exception as e:
            logging.error(f"Error capturing and saving image: {e}")

    def add_pic_mark(self, file_path, text):
        """
        照片添加水印功能
        :param file_path: 照片路径
        :param text: 需要添加的文字
        :return: None
        """
        pic = cv2.imread(file_path)
        cv2.putText(pic, f'Camera ID: {self.device_index}', (25, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
        cv2.putText(pic, f"{text}", (25, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
        cv2.imwrite(file_path, pic)

    def release_camera(self):
        """释放摄像头资源。"""
        if self.camera:
            self.camera.release()
            logging.info("Camera resources have been released.")

    def __del__(self):
        """确保摄像头资源被正确释放。"""
        self.release_camera()


# Example Usage:
if __name__ == "__main__":
    
    logging_init()
    path = create_directory()
    id = show_and_select_camera()
    my_camera = USBCamera(device_index=id, frame_resolution=(1280, 720), frame_rate=15)
    my_camera.open_camera()
    time.sleep(1)
    my_camera.show_live_camera()
    my_camera.take_picture(save_path=path, test_case_name='test', count='1', pic_mark=True)
    my_camera.release_camera()
