# -*- coding: UTF-8 -*-
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from RB1 import Ui_MainWindow  #UI类
from PyQt5.QtCore import QFile  #读取文件
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import cv2  #读取视频
from PyQt5.QtGui import QImage, QPixmap  #逐帧显示视频
import threading  #创建线程以显示视频,否则若把视频播放放在主线程中,会卡死(原因不太懂)  #也可用QThreading
#播放视频用
# from PyQt5.Qt import QUrl, QVideoWidget
# from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtWidgets import QApplication, QWidget
#其他库
from time import sleep

class MyWindow(QMainWindow,Ui_MainWindow) :
    def __init__(self, parent=None):  #这个parent不知道是干啥的
        super(MyWindow, self).__init__(parent)
        self.setupUi(self) #setupUi是UI类里的,且这个函数要求传入一个mainWnd并将元件绑在传入的mainWnd上,而self在继承了QMainWindow后就是个mainWnd了
        #至此,已经完成了元件绑定

        self.isVideo = True  #没有垃圾投入的时候,就播放视频
        self.stopFlag = False  #按下Close按键的时候,就关闭视频

        self.Btn_Open.clicked.connect(self.Open_video)
        self.Btn_Close.clicked.connect(self.Close_video)

        #视频播放器
        # self.video_widget = QVideoWidget(self)
        # self.playlist = QMediaPlaylist(self)
        # self.player = QMediaPlayer(self)
        # self.player.setPlaylist(self.playlist)
        # self.player.setVideoOutput(self.Label_Video)
        # self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile('video2.wmv')))
        # self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        # self.player.setVolume(80)

        #这里是一些对ui的补充
        self.Label_Video.setScaledContents(True)  #自动缩放图片大小
        self.Btn_Close.setEnabled(False)
        # self.Label_Class.setScaledContents(True)
        # self.Label_Class.adjustSize()
        # self.Label_Class.setWordWrap(True)

    def Open_video(self):  #读取文件,并启动子线程
        self.isVideo = True
        if self.isVideo :
            # self.fileName, self.fileType = QFileDialog.getOpenFileName(self, 'Choose file', '', '*.mp4')  #第一个参数要求传入一个mainWnd
            self.fileName = "video.mp4"  #!!!
            self.cap = cv2.VideoCapture(self.fileName)
            self.frameRate = self.cap.get(cv2.CAP_PROP_FPS)
        else :
            pass  #这里用来读取摄像头及分类后的图片
        self.Btn_Open.setEnabled(False)
        self.Btn_Close.setEnabled(True)
        # th = threading.Thread(target=self._display)  #这里不写target会卡死
        # th.start()
        self._display()


    def _display(self):  #子线程逐帧播放视频,并循环读取下一帧
        while self.cap.isOpened():
            # print("111")
            success, frame = self.cap.read()
            if not success :  #如果播完了,就重新从头播放
                self.cap = cv2.VideoCapture(self.fileName)
                success, frame = self.cap.read()
            # RGB转BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)  #图片,宽,高,颜色选项
            self.Label_Video.setPixmap(QPixmap.fromImage(img))

            if self.isVideo:
                # print("666")
                # cv2.waitKey(int(50 / self.frameRate))
                temp = 1
                cv2.waitKey(temp)
                # print("777")
            else:
                cv2.waitKey(1)
            # print("333")

            if self.stopFlag :
                self.stopFlag = False
                self.Label_Video.clear()
                self.Btn_Close.setEnabled(False)
                self.Btn_Open.setEnabled(True)
                self.isVideo = False
                break

    def Close_video(self):
        self.stopFlag = True
        self.isVideo = False

    def Show_Num(self,num):  #改变 Label_Num 垃圾数量
        self.Label_Num2.setText(str(num))
        QApplication.processEvents()

    def Show_No(self,nomber):
        self.Label_No2.setText(str(nomber))

    def Show_image(self,image):
        img = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        img = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGB888)  #图片,宽,高,颜色选项
        self.Label_Video.setPixmap(QPixmap.fromImage(img))

    def Show_Success(self,message):
        # self.Label_Success2.setStyleSheet("font : 24px; color : green;")
        # self.Label_Success2.setText("<u>"+message+"</u>")
        self.Label_Success2.setText("<html><head/><body><p><span style=\" font-weight:600; text-decoration: underline; color:#009400;\">{}</span></p></body></html>".format(message))

    def Show_Class(self,classification):
        self.Label_Class2.setText(classification)
        QApplication.processEvents()

    def Show_SmallClass(self,classifi):
        self.Label_SmallClass2.setText(classifi)

    def Show_Full(self,full_lst,num_lst):
        #full_lst是长为4的数组,分别表示 可回收物、厨余垃圾、有害垃圾、其他垃圾 对应的筐是否满了
        for index,fullness in enumerate(full_lst) :
            label = eval("self.label_Full"+str(index+1))
            pic = eval("self.label_Pic"+str(index+1))
            num = num_lst[index]
            if fullness :
                label.setText(str(num)+" "+"满载啦！")
                label.setStyleSheet("font : 24px; color : red; font-weight : bold")
                pic.setPixmap(QPixmap("pictures/fulled"+str(index+1)))
            else :
                label.setText(str(num))
                label.setStyleSheet("font : 20px; color : green; font-weight : bold")
                pic.setPixmap(QPixmap("pictures/garbage"+str(index+1)))

    def testFunc(self):
        i = 0
        while(i<10) :
            self.Show_Num(i)
            i+=1
            sleep(0.5)
        self.Show_No(1)
        image = cv2.imread("./img_23.jpg")
        # myWin.Show_image(image)
        # myWin.Show_Class("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.Show_Class("ABCDEF")
        self.Show_Success("你好啊")
        self.Show_Full([0,1,0,0],[1,2,3,4])
        self.Show_SmallClass("烟头")
        self.Close_video()
        # myWin.player.play()

