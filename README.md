logging_init() # 初始化logging
path = create_directory() # 创建文件夹
id = show_and_select_camera() # 选择camera id
my_camera = USBCamera(device_index=id, frame_resolution=(1280, 720), frame_rate=15) # 初始化camera
my_camera.open_camera() # 打开camera
time.sleep(1)
my_camera.show_live_camera() # 实时展示对应camera画面
my_camera.take_picture(save_path=path, test_case_name='test', count='1', pic_mark=True) # 拍照，测试名称/照片编号按需要填写，需要照片水印可以设置 true，默认是 false
my_camera.release_camera() # 释放camera
