import serial as ser
import struct,time
a ='z'
c=a.encode('utf-8')
b=678
#创建并打开串口
se = ser.Serial('/dev/ttyTHS1',115200,timeout=0.5)
# def recv(serial):
    # while True:
    #     data=serial.read(64)
    #     if data=='':
    #         continue
    #     else:
    #         break
    # return data
while True:
    # print(se.in_waiting)
    #判断是否有数据
    if se.in_waiting:
    #inWaiting()：返回接收缓存中的字节数
    #读数据
        data=se.read(se.in_waiting)
        data=str(data,encoding='utf-8')
        print(data)   #  这里是调试的串口接收，接受函数看自己需要定，这里只是方便博主调试
        print(type(data))
        #写数据
    se.write(str(1).encode('utf-8'))
    # se.write(a.encode('utf-8'))
    # time.sleep(0.1)
