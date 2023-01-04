import pefile
import re
import psutil
import getpass
import socket
import time
import threading
import wx
import os

#用以匹配PE文件中对应的字节
pattern1 = r'VirtualAddress:\s+0x0\b'
pattern2 = r'Size:\s+0x0\b'
#获得当前系统的用户名
username = getpass.getuser()
hostname = socket.gethostname()
username = hostname + '\\' + username

app = wx.App()
app.MainLoop()

#进程对应可执行文件是否被签名认证
def hv_cer(PEfile_Path):
    pe = pefile.PE(PEfile_Path)
    IMAGE_DIRECTORY_ENTRY_SECURITY = str(pe.OPTIONAL_HEADER.DATA_DIRECTORY[4])
    if (re.search(pattern1, IMAGE_DIRECTORY_ENTRY_SECURITY) is None and re.search(pattern2, IMAGE_DIRECTORY_ENTRY_SECURITY) is None):
        return 1 #经过数字签名
    else:
        return 0 #未经过数字签名

#得到未签名认证的用户级进程，作为低可信进程
def get_nocer():
    pids = psutil.pids()
    userpids = []
    for pid in pids:
        try:
            p = psutil.Process(pid)
            if username == str(p.as_dict()['username']):
                userpids.append(pid)
        except:
            continue

    print('获得用户级别进程')
    print(userpids)
    nocerpid = []
    for pid in userpids:
        if pid in psutil.pids():
            p = psutil.Process(pid)
            if hv_cer(p.exe()) == 0:
                print("得到一个不可信进程...")
                nocerpid.append(pid)
    return nocerpid

#监控线程的功能
def my_monitor(pid):
    p = psutil.Process(pid)
    oldlist = p.connections()
    oldnum = len(oldlist)
    while True:
        try:
            time.sleep(5) 
            #每5秒钟检查进程是否有新的连接
            newlist = p.connections()
            newnum = len(newlist)
            if oldnum == newnum:
                continue
            else:
                newcons = []
                for x in newlist:
                    if x not in oldlist:
                        newcons.append(x)
                oldlist = newlist
                oldnum = newnum
                if newcons == []:
                    continue
                else:
                    infor = ''
                    for one in newcons:
                        infor += '进程名称:' + str(p.name()) + '  ' + '本地ip:' + str(one.laddr) + '  ' + '远程ip:' + str(one.raddr) +'\n'
                    dlg = wx.MessageDialog(None, infor, "网络连接提示，请选择是否终止此进程", wx.YES_NO)
                    if dlg.ShowModal() == wx.ID_NO:
                        continue
                    else:
                        os.popen('taskkill.exe /pid:'+str(pid))
        except:
            print("进程结束")
            continue

#主程序
pids = psutil.pids() #先获取以此系统所有正在运行的进程
print('正在获取可执行文件未签名的用户级别进程')
nocerpid = get_nocer()
print('低可信库进程pid:')
print(nocerpid)
tlist =[]
print('下面为每个低可信度进程创建监控线程')

for pid in nocerpid:
    try: #判断该进程是否还在运行，相当有必要
        t = threading.Thread(target = my_monitor, daemon=True, args = (pid,))
        tlist.append(t)
        t.start()
        print('为' + str(psutil.Process(pid).name()) + '创建监控线程成功')
    except:
        continue

print('程序将会每5秒检测是否有新的不可信进程加入......')
while True:
    time.sleep(5)
    newpids = psutil.pids()
    new_pro = []
    for one in newpids:
        if one not in pids:
            try:
                if one in psutil.pids() and psutil.Process(one).as_dict()['username'] == username:
                    if one in psutil.pids() and hv_cer(psutil.Process(one).exe()) == 0:
                        new_pro.append(one)
            except:
                continue

    pids = newpids
    for pid in new_pro:
        try:
            print("发现低可信进程" + str(psutil.Process(pid).name()) +', 正在为此创建监控线程')
            t = threading.Thread(target = my_monitor, daemon=True, args = (pid,))
            tlist.append(t)
            t.start()
        except:
            continue
        
    

    