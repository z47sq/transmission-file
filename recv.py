#!/usr/bin/env python
# -*- coding:utf-8 -*-
#   
#   Author  :   Zhangsiqi
#   Date    :   18/6/6
#   Desc    :   传输文件的阻塞 recv
import socket
import time
import sys
import os
import struct

SERVER_ADDRESS = (HOST, PORT) = '192.168.123.7', 6666#把服务器的地址和端口号赋给SERVER_ADDRESS

def handle_request(client_connection, client_address):#处理请求
    print 'Accept new connection from {0}'.format(client_address)
    client_connection.send('Hi, Welcome to the server!')
    while 1:
        data = client_connection.recv(1024)
        if data == 'N' or not data:#如果从发送端接收到的数据是'N'
            print '{0} connection close'.format(client_address)
            client_connection.send('Connection closed!')
            break
        else:
	    fileinfo_size = struct.calcsize('128sl')#struct.calcsize用于计算格式字符串所对应的结果的长度
	    buf = client_connection.recv(fileinfo_size)
	    if buf:#如果不加这个if，第一个文件传输完成后会自动走到下一句
	        filename, filesize = struct.unpack('128sl', buf)#struct.unpack用于将字节流转换成python数据类型
	        fn = filename.strip('\00')#移除字符串指定的字符序列\00
	        new_filename = os.path.join('./', 'new_' + fn)#os.path.join()：将多个路径组合后返回
	        print 'file new name is {0}, filesize is {1}'.format(new_filename,
		                                                         filesize)

	        recvd_size = 0  # 定义已接收文件的大小
	        fp = open(new_filename, 'wb')#向新建立的文件中写入数据
	        print 'start receiving...'
	        while not recvd_size == filesize:#如果已接收文件的大小不等于传输文件大小
		    if filesize - recvd_size > 1024:#每次接收1K个字节
		        data = client_connection.recv(1024)
		        recvd_size += len(data)
		    else:#当文件传输剩余部分不到1K时
		        data = client_connection.recv(filesize - recvd_size)
		        recvd_size = filesize#已接收文件的大小等于传输文件大小
		    fp.write(data)#把接收到的数据写到文件中
		fp.close()
                time.sleep(5)  # 模拟阻塞事件
		print 'end receive...'
        client_connection.send('{0} is arrived!'.format(fn))#向发送端发送消息当前文件已到达接收端
def server():
# server 端创建一个socket,linux系统会分配唯一一个socket 编号给它  
# socket.AF_INET --> 机器网络之间的通信  
# socket.SOCK_STREAM --> TCP 协议通信(对应UDP) 
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# 把服务绑定到对应的ip和port 
    listen_socket.bind(SERVER_ADDRESS)
# 启动socket 网络监听服务,一直监听client的网络请求
    listen_socket.listen(10)
    print 'Waiting connection...'

    while 1:
        client_connection, client_address = listen_socket.accept()
        handle_request(client_connection,client_address)
# 通信完毕，关闭链接；链接没有关闭时可进行可以多次数据通信 
        client_connection.close()

if __name__ == '__main__':
    server()
