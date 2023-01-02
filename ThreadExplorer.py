import os 
import psutil
import json
class ThreadExplorer:
    def __init__(self):
        self.Process_message = {}
        self.getList()
        self.flag = 0

    def getList(self):
        pids = psutil.pids()
        for pid in pids:
            try:    
                #print(pid)
                process = psutil.Process(pid)
                MianProcess = process.parent()
                self.Process_message[f"{process.name()}:{pid}"] = {
                
                    "Process name:":process.name(),
                    "PID:":pid,
                    "Running:":process.is_running(),
                    #"Path:":process.exe(),
                    "Parent:":MianProcess.name(),
                    "Parent pid:":process.ppid(),
                    #"Time:":process.create_time(),
                    #"User name:":process.username(),
                }
            except:
                continue
# threadExplorer = ThreadExplorer()
# data = json.dumps(threadExplorer.Process_message)
# data = json.loads(data)
# #print(data)
# for value in data.values():
#     print(value['Process name:'])
    # def exec(self, commands:str):
    #     cmd = commands.split(' ')
    #     if "ls" == cmd[0]:
    #         return self.list
    #     elif "pwd" == cmd[0]:
    #         return os.getcwd()
    #     elif "cd" == cmd[0]:
    #         os.chdir(' '.join(cmd[1:]))
    #         self.getList()
    #         return os.getcwd()
    #     elif "select" == cmd[0]:
    #         num = int(cmd[1])
    #         return os.path.join(os.getcwd(), self.list[num][0])