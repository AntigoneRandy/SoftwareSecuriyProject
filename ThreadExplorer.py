import os 
import psutil
class ThreadExplorer:
    def __init__(self):
        self.Process_message = {}
        self.getList()

    def getList(self):
        try:
            pids = psutil.pids()
            for pid in pids:
                process = psutil.Process(pid)
                MianProcess = process.parent()
                self.Process_message[f"{process.name()} | {pid}"] = {
                    "Process name:":process.name(),
                    "PID:":pid,
                    "Running:":process.is_running(),
                    "Path:":process.exe(),
                    "Parent:":MianProcess.name(),
                    "Parent pid:":process.ppid(),
                    "Time:":process.create_time(),
                    "User name:":process.username(),
                }
        except:
            print("fail to get thread")

    def exec(self, commands:str):
        cmd = commands.split(' ')
        if "ls" == cmd[0]:
            return self.list
        elif "pwd" == cmd[0]:
            return os.getcwd()
        elif "cd" == cmd[0]:
            os.chdir(' '.join(cmd[1:]))
            self.getList()
            return os.getcwd()
        elif "select" == cmd[0]:
            num = int(cmd[1])
            return os.path.join(os.getcwd(), self.list[num][0])