import os
import socket

config = configparser.ConfigParser()
config.read('config.ini', 'utf8')

master_ip = config.get('client', 'masterIp')
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect((master_ip, 8088))
ip = s.getsockname()[0]
print(ip)