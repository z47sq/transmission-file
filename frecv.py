#!/usr/bin/env python
# -*- coding:utf-8 -*-
#   
#   Author  :   Zhangsiqi
#   Date    :   18/6/6
#   Desc    :   传输文件的非阻塞 frecv
# 非阻塞 frecv 主要是采用 fork 的方式实现非阻塞 recv，主要原理就是当 socket 接受到（accept）一个请求，就 fork 出一个子进程去处理这个请求。然后父进程继续接受其他请求。从而实现并发的处理请求，不需要处理上一个请求才能接受、处理下一个请求。
import errno
import os
import sys
import signal
import socket
import time
import struct
#一个进程使用fork创建子进程，如果子进程退出，而父进程并没有调用wait或waitpid获取子进程的状态信息，那么子进程的进程描述符仍然保存在系统中。这种进程称之为僵尸进程。
#孤儿进程：一个父进程退出，而它的一个或多个子进程还在运行，那么那些子进程将成为孤儿进程。孤儿进程将被init进程(进程号为1)所收养，并由init进程对它们完成状态收集工作。

SERVER_ADDRESS = (HOST, PORT) = '192.168.123.7', 8888#把服务器的地址和端口号赋给SERVER_ADDRESS

#因为过多的子进程并发开始，同时结束，会并发的发出结束的信号，父进程的 signal 一瞬间接收过多的信号，导致了有的信号丢失，这种情况还是会遗留一些僵尸进程。这个时候就需要写一个处理信号grim_reaper的方法。采用waitpid的os.WHOHANG选项，进行死循环。以确保获取到所有 signal
def grim_reaper(signum, frame):#信号处理函数，其包括两个参数分别为signum与目前的栈帧，直接在参数里写*args比较省事
    while True:
        try:
            pid, status = os.waitpid(
                -1,          # pid=-1时，等待任何一个子进程退出
                 os.WNOHANG  # 使用了WNOHANG参数调用waitpid，即使没有子进程退出，它也会立即返回；如果没有子进程退出，则不阻塞waitpid()调用
            )
#如果大量的产生僵死进程，将因为没有可用的进程号而导致系统不能产生新的进程。则会抛出OSError，而 OSError 因为waitpid的os.WNOHANG选项，不会阻塞，但是如果没有子进程退出，会抛出OSError，需要 catch 到这个异常，保证父进程接收到了每个子进程的结束信息，从而保证没有僵尸进程。
        except OSError:
            return
#子进程关闭一定要通知父进程，否则会出现‘僵尸进程’
        if pid == 0:  # 不存在僵尸进程（子进程）
            return



def handle_request(client_connection,client_address):#处理请求
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
    

def serve_forever():
# server 端创建一个socket,linux系统会分配唯一一个socket 编号给它  
# socket.AF_INET --> 机器网络之间的通信  
# socket.SOCK_STREAM --> TCP 协议通信(对应UDP) 
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# 把服务绑定到对应的ip和port 
    listen_socket.bind(SERVER_ADDRESS)
# 启动socket 网络监听服务,一直监听client的网络请求
    listen_socket.listen(1024)
    print 'Waiting connection...'

    signal.signal(signal.SIGCHLD, grim_reaper)#两个参数分别为信号，处理方式。子进程死后，会发送SIGCHLD信号给父进程，父进程收到此信号后，执行waitpid()函数为子进程收尸。就是基于这样的原理：就算父进程没有调用wait，内核也会向它发送SIGCHLD消息

    while True:
        try:#不出现异常
            client_connection, client_address = listen_socket.accept()
        except IOError as e:#IOError异常会提供一个二元元组, 包含对应数值错误代码和一个说明字符串
            code, msg = e.args#args作为参数
            if code == errno.EINTR:#在socket服务器端，设置了信号捕获机制，有子进程，当在父进程阻塞于慢系统调用时由父进程捕获到了一个有效信号时，内核会致使accept返回一个EINTR错误(被中断的系统调用)。
                continue#跳出此次循环，继续执行下一次
            else:
                raise#向正在执行的程序发送一个信号，通过raise显示地引发异常。一旦执行了raise语句，raise后面的语句将不能执行

#采用 fork 的方式实现非阻塞 Server，主要原理就是当 socket 接受到（accept）一个请求，就 fork 出一个子进程去处理这个请求。然后父进程继续接受请求。从而实现并发的处理请求，不需要处理上一个请求才能接受、处理下一个请求。
        pid = os.fork()
#os.fork函数创建进程的过程：程序每次执行时，操作系统都会创建一个新进程来运行程序指令。进程还可调用os.fork，要求操作系统新建一个进程。父进程是调用os.fork函数的进程。父进程所创建的进程叫子进程。每个进程都有一个不重复的进程ID号。或称pid，它对进程进行标识。子进程与父进程完全相同，两个进程的唯一区别是fork的返回值。子进程接收返回值0，而父进程接收子进程的pid作为返回值。一个现有进程可以调用fork函数创建一个新进程。由fork创建的新进程被称为子进程。fork函数被调用一次但返回两次。两次返回的唯一区别是子进程中返回0值而父进程中返回子进程ID。 对于程序，只要判断fork的返回值，就知道自己是处于父进程还是子进程中。
        if pid == 0:  # 子进程
            listen_socket.close()  #停止接受请求
            handle_request(client_connection,client_address)
            client_connection.close()
            os._exit(0)#退出程序
        else:  # 父进程
            client_connection.close()  # 只接受请求，不与客户端传输数据

if __name__ == '__main__':
    serve_forever()
