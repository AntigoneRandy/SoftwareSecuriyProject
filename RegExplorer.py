import winreg
import re


class RegExplorer:
    def __init__(self):
        self.list_subdir = {}
        self.list_keyvalue = {}
        self.path = ''
        self.path = 'SOFTWARE\\360zip\\'
        self.key = 0

    def getList(self):
        self.list_subdir = {}
        self.list_keyvalue = {}
        i = 0
        subkey = self.path
        try:
            while True:
                self.key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey)
                # print('open key success.')
                x = winreg.EnumKey(self.key, i)
                self.list_subdir[i] = x
                i += 1
        except WindowsError as e:
            run = False # 所有的子目录都被找完了
            # print("no more subkey")
            # print(self.list_subdir)
        try:
            j = 0
            while True:
                name,value,typeNo = winreg.EnumValue(self.key, j)
                # print(name, value, typeNo)
                self.list_keyvalue[j] = {'name':name, 'value':value, 'typeNo':typeNo}
                j += 1
        except WindowsError as e:
            # print(self.list_keyvalue)
            if self.key:
                winreg.CloseKey(self.key)

    def back(self):
        if (self.path == ''):
            return
        list = re.split(r'\\', self.path)
        for e in list[::-1]:
            if(e!=''):
                last_subkey = e
                break
        self.path = ''
        for e in list:
            if (e == '' or e == last_subkey):
                continue
            self.path += e
            self.path += r'\\'
        


# regExplorer=RegExplorer()

# regExplorer.path = 'SOFTWARE\\360zip\\'

# regExplorer.getList()
# print(regExplorer.list_subdir)
# print(regExplorer.list_keyvalue)
# print(regExplorer.path)

# for i in regExplorer.list_subdir:
#     print(regExplorer.list_subdir[i])
# regExplorer.back()

# regExplorer.getList()

# regExplorer.back()

# regExplorer.getList()

# regExplorer.back()

# regExplorer.getList()

# regExplorer.back()

# regExplorer.getList()

# regExplorer.back()

# regExplorer.getList()

# regExplorer.back()

# regExplorer.path = ''

# regExplorer.getList()
