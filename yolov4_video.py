from ctypes import *
import random
import os
import cv2
import time
import darknet
import argparse
from threading import Thread, enumerate
from queue import Queue
from RB1_MyWnd import MyWindow
from PyQt5.QtWidgets import QApplication
import sys
import serial as ser
import struct

get_result = True
full = [0, 0, 0, 0]
nums = [0, 0, 0, 0]
No = 0
checkI = True

thresh = 0.5
nameMap = {
    "battery": "电池",
    "can": "饮料容器",
    "bottle": "饮料容器",
    "fruit": "水果",
    "vegetable": "蔬菜",
    "flowerpot": "砖瓦碎片",
    "cigarette": "烟头",
    "bowl": "陶瓷",
    "bricks": "砖瓦陶瓷"
}


def parser():
    parser = argparse.ArgumentParser(description="YOLO Object Detection")
    # 创建一个参数解析对象
    parser.add_argument("--input", type=str, default=0,
                        help="video source. If empty, uses webcam 0 stream")
    # 添加单个命令参数 type为输入的指定类型 dafault在没有命令输入时的默认值
    parser.add_argument("--out_filename", type=str, default="",
                        help="inference video name. Not saved if empty")
    parser.add_argument("--weights", default="weights/1GPU/yolov4-garbage_best.weights",
                        help="yolo weights path")
    parser.add_argument("--dont_show", action='store_true',
                        help="windown inference display. For headless systems")
    # action='store'表示存储参数值 store_true就代表着一旦有这个参数，做出动作“将其值标为True”，也就是没有时，默认状态下其值为False。
    parser.add_argument("--ext_output", action='store_true',
                        help="display bbox coordinates of detected objects")
    parser.add_argument("--config_file", default="./cfg/yolov4-garbage.cfg",
                        help="path to config file")
    parser.add_argument("--data_file", default="./cfg/voc.data",
                        help="path to data file")
    parser.add_argument("--thresh", type=float, default=.05,
                        help="remove detections with confidence below this value")
    return parser.parse_args()
    # 使得参数创建并生效
    # argparse模块的作用是用于解析命令行参数。



def str2int(video_path):
    """
    argparse returns and string althout webcam uses int (0, 1 ...)
    Cast to int if needed
     argparse返回的是字符串，而不是网络摄像头使用的int (0, 1 ...)。
    如果需要的话，可将其转换为int
    """
    try:
        return int(video_path)
    except ValueError:
        return video_path


def check_arguments_errors(args):
    # 检查错误并返回错误提示
    assert 0 < args.thresh < 1, "Threshold should be a float between zero and one (non-inclusive)"
    if not os.path.exists(args.config_file):
        raise (ValueError("Invalid config path {}".format(os.path.abspath(args.config_file))))
    if not os.path.exists(args.weights):
        raise (ValueError("Invalid weight path {}".format(os.path.abspath(args.weights))))
    if not os.path.exists(args.data_file):
        raise (ValueError("Invalid data file path {}".format(os.path.abspath(args.data_file))))
    if str2int(args.input) == str and not os.path.exists(args.input):
        raise (ValueError("Invalid video path {}".format(os.path.abspath(args.input))))


def set_saved_video(input_video, output_video, size):
    fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    fps = int(input_video.get(cv2.CAP_PROP_FPS))
    video = cv2.VideoWriter(output_video, fourcc, fps, size)
    # cv2.VideoWriter()第一个参数是要保存的文件的路径 ，fourcc 指定编码器，fps 要保存的视频的帧率，frameSize 要保存的文件的画面尺寸
    return video


def serial_read():
    global get_result
    global full
    global thresh
    global Num
    global results
    global checkI
    # print(se.inWaiting())
    while True:
        while se.inWaiting() > 0:
            # print(se.inWaiting())
            data = se.read(1)  # 读取长度为10的bytes格式字符
            data = data.decode('gb18030')  # 解码为str
            print(data)
            if data == 'I':
                if checkI:
                    checkI = False
                    myWin.Close_video()
                    # thresh = 0.05
                    # myWin.Show_SmallClass(None)-
                    # myWin.Show_Class(None)
                    # myWin.Show_Success('正在识别……')
                    get_result = True
                else:
                    pass
            # if data == 'M':
            #     myWin.isVideo = True
            if data == '9':  # 分类完毕
                get_result = True
                results = []
                myWin.Show_Success('OK!')
            elif data == 'A':  # 1号桶满载
                full[0] = 1
            elif data == 'B':  # 2号桶满载
                full[1] = 1
            elif data == 'C':  # 3号桶满载
                full[2] = 1
            elif data == 'D':  # 4号桶满载
                full[3] = 1
            elif data == 'a':  # 1号桶未满载
                full[0] = 0
            elif data == 'b':  # 2号桶未满载
                full[1] = 0
            elif data == 'c':  # 3号桶未满载
                full[2] = 0
            elif data == 'd':  # 4号桶未满载
                full[3] = 0
            # elif data == 'F':
            #     myWin.Show_SmallClass('砖瓦碎片')
            #     myWin.Show_Class('其他垃圾')
            #     myWin.Show_Success('正在投放……')
            #     Num += 1
            #     myWin.Show_No(Num)
            # #     myWin.Show_Num(1)
            # elif data == 'X':
            #     myWin.Show_SmallClass('蔬菜')
            #     myWin.Show_Class('厨余垃圾')
            # elif data == 'x':
            #     myWin.Show_SmallClass('烟头')
            #     myWin.Show_Class('其他垃圾')


def gstreamer_pipeline(
        capture_width=1280,
        capture_height=720,
        display_width=640,
        display_height=480,
        framerate=60,
        flip_method=0,
):
    return (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), "
            "width=(int)%d, height=(int)%d, "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
            % (
                capture_width,
                capture_height,
                framerate,
                flip_method,
                display_width,
                display_height,
            )
    )


if __name__ == '__main__':
    # 创建一个窗口
    app = QApplication(sys.argv)
    # 命令行参数解析
    args = parser()
    # 检查命令行参数是否有错，并报错
    check_arguments_errors(args)
    # 指定各参数的值
    network, class_names, class_colors = darknet.load_network(
        args.config_file,
        args.data_file,
        args.weights,
        batch_size=1
    )
    # width = darknet.network_width(network)
    # height = darknet.network_height(network)
    # 修改图片的长、宽
    width = 960
    height = 480
    print(width, height)
    flip = 0
    # cv2.namedWindow('cam')

    cap = cv2.VideoCapture(0)
    # 读取摄像头,0为摄像头索引，当有多个摄像头时，从0开始编号
    # print(cap.get(3))
    # print(cap.get(4))
    # cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
    random.seed(3)  # deterministic bbox colors
    myWin = MyWindow()
    myWin.show()

    results = []
    # 串口通信
    se = ser.Serial('/dev/ttyTHS0', 115200, timeout=0.001)
    # 创建一个子线程serial_read判断是否满载
    Thread(target=serial_read).start()

    while cap.isOpened():
        # 从视频或摄像头中读取一帧（即一张图像）,返回是否成功标识ret(True代表成功，False代表失败），img为读取的视频帧
        ret, frame = cap.read()
        # 判断是否读取成功，未成功继续读取
        if not ret:
            continue
        # cv2.cvtColor(p1,p2) 是颜色空间转换函数，p1是需要转换的图片，p2是转换成何种格式。cv2.COLOR_BGR2RGB 将BGR格式转换成RGB格式
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 将原始图像调整为指定大小（原始图像，输出图像的尺寸（元组方式）， interpolation：插值方法cv2.INTER_LINEA双线性插值（默认））
        frame_resized = cv2.resize(frame_rgb, (width, height),
                                   interpolation=cv2.INTER_LINEAR)
        darknet_image = darknet.make_image(width, height, 3)
        darknet.copy_image_from_bytes(darknet_image, frame_resized.tobytes())

        #  inference
        if myWin.isVideo == False:
            prev_time = time.time()
            detections = darknet.detect_image(network, class_names, darknet_image, thresh=thresh)  # 改变量名
            fps = int(1 / (time.time() - prev_time))
            # print("FPS: {}".format(fps))
            # darknet.print_detections(detections, args.ext_output)
            darknet.free_image(darknet_image)
            if frame_resized is not None:
                image = darknet.draw_boxes(detections, frame_resized, class_colors)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                myWin.Show_image(image)
                # if not args.dont_show:
                # cv2.imshow('cam', image)
                if cv2.waitKey(fps) == 27:
                    break

            myWin.Show_Full(full, nums)  # 显示是否满载

            if get_result:  # 得出分类结果前，get_result为True
                if darknet.save_detections(detections):
                    results.append(darknet.save_detections(detections))
                    print(results)

            if len(results) == 1:
                No += 1

                myWin.Show_No(No)
                myWin.Show_Num(No)
                myWin.Show_Success('正在投放……')
                get_result = False
                # thresh = 0.5
                x = {}
                times = {}
                for i in range(len(results)):
                    for y in range(len(results[i])):
                        if results[i][y][0] not in x:
                            x[results[i][y][0]] = float(results[i][y][1])
                            times[results[i][y][0]] = 1
                        else:
                            x[results[i][y][0]] = x[results[i][y][0]] + float(results[i][y][1])
                            times[results[i][y][0]] = times[results[i][y][0]] + 1
                print(x)
                print(times)
                out = max(x, key=x.get)
                confidence = x[out] / times[out]
                results = []
                print(out, confidence)

                # myWin.Show_Class(out)  #  显示类别
                # if out != 'cigarette':
                myWin.Show_SmallClass(nameMap[out])
                if out == 'battery':
                    se.write('1\r\n'.encode())
                    nums[2] += 1
                    myWin.Show_Class('有害垃圾')
                    # myWin.Show_Num(Num_1)
                elif out == 'can' or out == 'bottle':
                    se.write('2\r\n'.encode())
                    nums[0] += 1
                    myWin.Show_Class('可回收垃圾')
                    # myWin.Show_Num(Num_2)
                elif out == 'fruit' or out == 'vegetable':
                    se.write('3\r\n'.encode())
                    nums[1] += 1
                    myWin.Show_Class('厨余垃圾')
                    # myWin.Show_Num(Num_3)
                elif out == 'cigarette' or out == 'bricks':
                    se.write('4\r\n'.encode())
                    nums[3] += 1
                    myWin.Show_Class('其他垃圾')
                    # myWin.Show_Num(Num_4)
                # elif out == 'cigarette':
                #     se.write('4\r\n'.encode())

        else:
            myWin.Open_video()  # 播放视频

    cap.release()
    cv2.destroyAllWindows()

    # input_path = str2int(args.input)
    # cap = cv2.VideoCapture(input_path)
    # Thread(target=video_capture, args=(frame_queue, darknet_image_queue)).start()
    # Thread(target=inference, args=(darknet_image_queue, detections_queue, fps_queue)).start()
    # Thread(target=drawing, args=(frame_queue, detections_queue, fps_queue)).start()