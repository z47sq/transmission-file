#!/usr/bin/env python
# -*- coding:utf-8 -*-
#   
#   Author  :   Zhangsiqi
#   Date    :   18/6/6
#   Desc    :   传输文件的阻塞 send

import socket
import os
import sys
import struct

SERVER_ADDRESS = (HOST, PORT) = '192.168.123.7', 6666#把服务器的地址和端口号赋给SERVER_ADDRESS
def client():
# socket.AF_INET --> 机器网络之间的通信  
# socket.SOCK_STREAM --> TCP 协议通信(对应UDP) 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(SERVER_ADDRESS)#与server端连接
    print s.recv(1024)#打印从接收端收到的数据
    while 1:
        data = raw_input('Do you want to continue(Y/N): ')
        s.send(data)#向接收端发送指令
        if data!='N':
            filepath = raw_input('Input file path: ')#输入要进行传输的文件路径
            if os.path.isfile(filepath):#判断路径是否为文件
            # 定义文件信息。128s表示文件名为128bytes长，l表示一个int或long文件类型，在此为文件大小
                fileinfo_size = struct.calcsize('128sl')
            # 定义文件头信息，包含文件名和文件大小
                fhead = struct.pack('128sl', os.path.basename(filepath),
                                os.stat(filepath).st_size)
                s.send(fhead)#把文件头信息发送到接收端
                print 'client filepath: {0}'.format(filepath)
    
                fp = open(filepath, 'rb')#读写打开二进制文件，只允许读写数据
                while 1:
                    data = fp.read(1024)
                    if not data:#空文件
                        print '{0} file send over...'.format(filepath)
                        break
                    s.send(data)#把文件中的数据发送到接收端
        print 'Client is waiting response...'
        print s.recv(1024)
        if data=='N':
	    break#如果指令为'N'则终止程序
        
if __name__ == '__main__':
    client()
