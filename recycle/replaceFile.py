import os

import pysftp

# apiIps = ['192.168.133.177']
#
# print('支持替换的工程：api')
# targetProject = input('请输入要替换的工程：')
# def getIps(targetproject):
#     return {
#         'api': apiIps
#     }.get(targetproject)
#
# ips = getIps(targetProject)
# print(ips)

# 替换文件
cnopts = pysftp.CnOpts()
cnopts.hostkeys.load('C:\\Users\\yangnx\\.ssh\\known_hosts')
cnopts.hostkeys = None
with pysftp.Connection('192.168.133.177', username='root', password='123qwe!@#', cnopts=cnopts) as sftp:
    index = open('e:/index.txt')
    content = index.readlines(10)
    with sftp.cd('/root'):
        sftp.chdir('./yangnx/tomcat-recycle')
        for c in content:
            _c = c.split(':', 1)
            targetPath = _c[1].split('gcj_customer_service\\')

            print(sftp.exists('recycle'))
            # sftp.remove(targetPath[1] + '/' + _c[0])  # 删除目标文件
            print(os.path.abspath('..\\yangnx') + '\\' + _c[0])
            print(targetPath[1] + '/' + _c[0])

            sftp.put(os.path.abspath('..\\yangnx') + '\\' + _c[0], '/root/yangnx/tomcat-recycle/' + targetPath[1] + '/' + _c[0])
            print(os.path.abspath('..\\yangnx') + '\\' + _c[0])
            print('/root/yangnx/tomcat-recycle/' + targetPath[1])

