import wx
import wx.xrc
import os
import pysftp
import re
import time
import glob
import json
import getpass
import math
import paramiko
import select
from threading import Thread
from wx.lib.pubsub import pub
from conf import grid_count

# 项目配置
size = 30
projects = {
    'prod': {
        'gccce': {
            'project_name': 'gcj_customer_service',
            'ips': ['10.126.15.196', '10.126.15.197', '10.126.15.202', '10.126.15.203'],
            'username': 'paas',
            'password': 'Paas@$^ali',
            'tomcat_location': '/opt/apache-tomcat-7.0.47_8080',
            'app_location': '/opt/project/webapps_8080/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        },
        'task': {
            'project_name': 'gcj_cstm_task_manager',
            'ips': ['10.126.15.208', '10.126.15.231', '10.126.15.232'],
            'username': 'paas',
            'password': 'Paas@$^ali',
            'tomcat_location': '/opt/apache-tomcat-7.0.47_8080',
            'app_location': '/opt/project/webapps_8080/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        },
        'bg': {
            'project_name': 'member_center_bg',
            'ips': ['10.126.15.184', '10.126.15.185'],
            'username': 'paas',
            'password': 'Paas@$^ali',
            'tomcat_location': '/opt/apache-tomcat-7.0.47_8080',
            'app_location': '/opt/project/webapps_8080/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        },
        'api': {
            'project_name': 'member_center_api',
            'ips': ['10.126.15.182', '10.126.15.183', '10.126.14.63'],
            'username': 'paas',
            'password': 'Paas@$^ali',
            'tomcat_location': '/opt/apache-tomcat-7.0.47_8080',
            'app_location': '/opt/project/webapps_8080/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        },
        'master': {
            'project_name': 'gcw_master_site',
            'ips': ['10.126.15.139', '10.126.15.140', '10.126.15.141', '10.126.15.142'],
            'username': 'paas',
            'password': 'Paas@$^ali',
            'tomcat_location': '/opt/apache-tomcat-7.0.47_8080',
            'app_location': '/opt/project/webapps_8080/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        },
        'dws-hw': {
            'project_name': 'gcj_dws_hw_online',
            'ips': ['10.125.4.34', '10.125.4.38', '10.125.4.75', '10.125.4.145', '10.125.4.155', '10.125.4.198', '10.125.4.222', '10.125.4.240', '10.125.4.244'],
            'username': 'paas',
            'password': 'Paas@$^hw',
            'tomcat_location': '/opt/apache-tomcat-7.0.47_8080',
            'app_location': '/opt/project/webapps/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        },
        'dws-yz': {
            'project_name': 'gcj_dws_yz',
            'ips': ['10.127.61.3', '10.127.61.52', '10.127.61.175', '10.127.61.21'],
            'username': 'root',
            'password': 'root',
            'tomcat_location': '/data/apache-tomcat-7.0.47_8080',
            'app_location': '/data/project/webapps/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        },
        'water-backend': {
            'project_name': 'waterdrop_admin_online',
            'ips': ['10.125.4.224', '10.125.4.125', '10.125.4.196', '10.125.4.247'],
            'username': 'paas',
            'password': 'Paas@$^hw',
            'tomcat_location': '/opt/apache-tomcat-8.0.28_8080',
            'app_location': '/opt/project/webapps/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        },
        'bid-data-interface': {
            'project_name': 'bid_data_interface_online',
            'ips': ['10.125.4.83', '10.125.4.29'],
            'username': 'paas',
            'password': 'Paas@$^hw',
            'tomcat_location': '/opt/apache-tomcat-7.0.47_8080',
            'app_location': '/opt/project/webapps/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        }
    },
    'recycle': {
        'api': {
            'project_name': 'member_center_api',
            'ips': ['192.168.133.177'],
            'username': 'root',
            'password': '123qwe!@#',
            'tomcat_location': '/opt/tomcats/apache-tomcat-member-center-api',
            'app_location': '/opt/tomcats/apache-tomcat-member-center-api/webapps/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000,

            'compiled_location': 'E:\Works\Publication Directory\member_center_api'
        },
        'master': {
            'project_name': 'gcw_master_site',
            'ips': ['192.168.133.177'],
            'username': 'root',
            'password': '123qwe!@#',
            'tomcat_location': '/opt/tomcats/apache-tomcat-gcw',
            'app_location': '/opt/tomcats/apache-tomcat-gcw/webapps/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000,

            'compiled_location': 'E:\Works\Publication Directory\gcw_master_site'
        },
        'bid_data_interface': {
            'project_name': 'bid_data_interface_online',
            'ips': ['192.168.133.177'],
            'username': 'root',
            'password': '123qwe!@#',
            'tomcat_location': '/opt/tomcats/apache-tomcat-bid-data-interface',
            'app_location': '/opt/tomcats/apache-tomcat-bid-data-interface/webapps/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000,

            'compiled_location': 'E:\Works\Publication Directory\\bid_data_interface_online'
        }
    }
}
replace_project_dir = 'ReplaceProject-%s' % getpass.getuser()
special_jar_names = ['member-center-util-', 'template.helper-', 'parser.engine-', 'waterdrop-common-']

restartFlagStr1 = 'Server startup in [\d|,]+ ms\Z'
restartFlagStr2 = 'INFO: Creation of SecureRandom instance for session ID generation using [SHA1PRNG] took [\d|,]+ milliseconds'

searchFileThreadFlag = True
# 替换文件
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None


def operate_tomcat(replace_dic, project, target_ips, need_delete_all_exist, need_replace, need_close, need_start):
    if len(target_ips) == 0:  # 是否有指定操作哪个ip
        target_ips = project['ips']
    for i, ip in enumerate(target_ips):
        if ip:
            send_wx_pub('【准备进行操作 %d/%d IP:%s】' % (i + 1, len(target_ips), ip), i, project)
            result = replace_file(replace_dic, log_out_index=i, ip=ip, project=project,
                                  need_delete_all_exist=need_delete_all_exist, need_replace=need_replace,
                                  need_close=need_close, need_start=need_start)
            if result != 'success':
                break
            else:
                send_wx_pub('【操作已完成 %d/%d IP:%s】\n' % (i + 1, len(target_ips), ip), i, project)


def replace_file(replace_dic, log_out_index, ip, project, need_delete_all_exist, need_replace, need_close, need_start):
    with pysftp.Connection(host=ip, username=project['username'], password=project['password'], cnopts=cnopts) as sftp:
        # with sftp.cd('/opt/project/webapps_8080/ROOT'):
        replace_flag = False
        # 替换文件
        with sftp.cd(project['app_location']):
            if need_replace:
                if len(replace_dic) > 0:
                    valid = True
                    for (source, target) in replace_dic.items():
                        send_wx_pub('来源文件:%s   目标文件:%s  %s' % (source, target, sftp.exists(target)), log_out_index, project)
                        # valid = valid & sftp.exists(target)
                    if need_delete_all_exist:
                        sftp.execute('rm -rf ' + sftp.getcwd() + '/webapps/ROOT/*')
                        target_project_name = replace_project_dir
                    else:
                        target_project_name = os.listdir(replace_project_dir)[0]

                    if valid:
                        send_wx_pub('校验成功 正在替换文件', log_out_index, project)
                        # os.listdir(replace_project_dir)[0] 这里存在潜在的问题
                        for (source, target) in replace_dic.items():
                            # 本地保存的路径
                            local_newly_backup_dir = str(source).replace(target_project_name, '%s-%s-%s' % (target_project_name, ip, 'newly'))
                            local_backup_dir = str(source).replace(target_project_name, '%s-%s' % (target_project_name, ip))
                            # 如果本地备份目录没有，则创建本地备份目录
                            if not os.path.exists(os.path.abspath(local_backup_dir)):
                                os.makedirs(os.path.dirname(os.path.abspath(local_backup_dir)), exist_ok=True)
                            if not os.path.exists(os.path.abspath(local_newly_backup_dir)):
                                os.makedirs(os.path.dirname(os.path.abspath(local_newly_backup_dir)), exist_ok=True)

                            # 保存被替换的文件，以防出问题
                            if sftp.exists(target):
                                sftp.get(target, local_backup_dir, preserve_mtime=True)
                            # 删除并保存已经存在的jar
                            for special_jar_name in special_jar_names:
                                # 如果要替换的是特殊的jar，则要删除线上所有该jar的其它版本
                                if os.path.basename(source).startswith(special_jar_name) & os.path.basename(source).endswith('.jar'):
                                    for jar_name in sftp.listdir(project['app_location'] + '/WEB-INF/lib'):
                                        if str(jar_name).startswith(special_jar_name):
                                            other_version_jar_path = project['app_location'] + '/WEB-INF/lib/' + jar_name
                                            sftp.get(other_version_jar_path, local_backup_dir, preserve_mtime=True)
                                            sftp.remove(other_version_jar_path)

                            # 判断线上的文件夹路径是否存在，否则创建文件夹
                            if not sftp.exists('/'.join(str(target).split('/')[:-1])):
                                sftp.makedirs('/'.join(str(target).split('/')[:-1]))
                            # 常规替换
                            sftp.put(source, target)
                            sftp.get(target, local_newly_backup_dir, preserve_mtime=True)

                        replace_flag = True
                    else:
                        send_wx_pub('校验失败 要替换的文件在远程服务器上未能发现，请检查文件路径是否正确', log_out_index, project)
                        return 'fail'
                else:
                    replace_flag = True

        with sftp.cd(project['tomcat_location']):
            if not need_replace or (need_replace and replace_flag):
                if need_close:
                    send_wx_pub('正在关闭tomcat', log_out_index, project)
                    grep = sftp.execute('ps -ef | grep ' + project['tomcat_location'])
                    for g in grep:
                        gStr = str(g, 'utf-8')
                        if re.search(project['tomcat_location'], gStr) is not None:
                            pid = re.split('\s+', gStr)[1]
                            sftp.execute('kill -9 ' + pid)
                    send_wx_pub('tomcat已关闭', log_out_index, project)
                if need_start:
                    send_wx_pub('正在重启tomcat', log_out_index, project)

                    # 启动tomcat
                    # paramiko 执行远程命令
                    client = paramiko.SSHClient()
                    client.load_system_host_keys()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                    client.connect(ip, username=project['username'], password=project['password'])
                    transport = client.get_transport()
                    channel = transport.open_session()
                    execute_jar = 'source /etc/profile; %s/bin/startup.sh' % (sftp.getcwd())
                    print(execute_jar)
                    channel.exec_command(execute_jar)
                    client.close()

                    # sftp.execute('sh ' + sftp.getcwd() + '/bin/catalina.sh start')
                    return tailLog(sftp, log_out_index, ip, project, [], False)
        return 'success'


# 监控tomcat输出日志，判断是否重启成功
def tailLog(sftp, log_out_index, ip, project, outs, first_flag):
    # out = sftp.execute('tail -n 20 /opt/tomcats/apache-tomcat-member-center-api/logs/catalina.out')
    out = sftp.execute(
        'tail -n ' + str(project['logs_tail_size']) + ' ' + project['tomcat_location'] + '/logs/catalina.out')
    newOut = [i for i in out if i not in outs and len(i) < project['logs_line_length']]
    wx.CallAfter(pub.sendMessage, 'update' + str(log_out_index), log_out_index=log_out_index, project=project,
                 log_out=newOut)
    restart = False
    for o in newOut:
        line = str(o, 'utf-8').replace('\n', '')
        if (re.search(restartFlagStr1, line) is not None or re.search(restartFlagStr1, line)) and first_flag:
            restart = True
            send_wx_pub('-------------%s Tomcat 重新启动成功 --------------' % ip, log_out_index, project)
            print('-------------%s Tomcat 重新启动成功 --------------' % ip)
    if not restart:
        time.sleep(1)
        return tailLog(sftp, log_out_index, ip, project, out, True)
    if restart:
        return 'success'

# 线程启动操作
class TestThread(Thread):
    def __init__(self, replace_dic, project, target_ips=(), need_delete_all_exist=False, need_replace=True,
                 need_close=True, need_start=True, all_in_time=False):
        Thread.__init__(self)
        self.replace_dic = replace_dic
        self.project = project
        self.target_ips = target_ips

        self.need_delete_all_exist = need_delete_all_exist
        self.need_replace = need_replace
        self.need_close = need_close
        self.need_start = need_start
        self.all_in_time = all_in_time
        self.start()

    def run(self):
        # 停止先前的日志输出
        wx.CallAfter(pub.sendMessage, 'stop_all')
        time.sleep(1)
        operate_tomcat(replace_dic=self.replace_dic, project=self.project, target_ips=self.target_ips,
                       need_delete_all_exist=self.need_delete_all_exist, need_replace=self.need_replace,
                       need_close=self.need_close, need_start=self.need_start)



# 替换文件的窗口
class ReplaceFileFrame(wx.Frame):
    def __init__(self, parent, menu_id):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title='文件替换', pos=wx.DefaultPosition,
                          size=wx.Size(1000, 700), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)
        self.files = []
        self.replace_dic = {}
        self.menu_id = menu_id
        self.project = self.current_project()
        global searchFileThreadFlag
        searchFileThreadFlag = True

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(wx.Colour(223, 223, 223))
        self.SetSize(wx.Size(1500, int(math.ceil(size / 2)) * 45))

        replaceBsWrapper = wx.BoxSizer(wx.VERTICAL)

        self.replaceFileNames = []
        self.replaceFilePaths = []
        for i in range(int(math.ceil(size / 2))):
            gSizer = wx.GridSizer(1, 2, 0, 0)
            replaceBsI = wx.BoxSizer(wx.HORIZONTAL)
            replaceBsI.SetMinSize(wx.Size(-1, 20))

            replaceFilePathI = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(500, -1), 0)
            replaceBsI.Add(replaceFilePathI, 0, wx.ALL, 5)
            self.replaceFilePaths.append(replaceFilePathI)

            replaceFileNameI = wx.StaticText(self, wx.ID_ANY, 'file' + str(i*2 + 1), wx.DefaultPosition, wx.DefaultSize, 0)
            replaceFileNameI.Wrap(-1)
            replaceFileNameI.SetMinSize(wx.Size(260, -1))
            replaceBsI.Add(replaceFileNameI, 0, wx.ALL, 5)
            self.replaceFileNames.append(replaceFileNameI)

            gSizer.Add(replaceBsI, 1, wx.EXPAND, 5)

            if i*2 + 2 <= size:
                replaceBsI2 = wx.BoxSizer(wx.HORIZONTAL)
                replaceBsI2.SetMinSize(wx.Size(-1, 20))

                replaceFilePathI2 = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(500, -1), 0)
                replaceBsI2.Add(replaceFilePathI2, 0, wx.ALL, 5)
                self.replaceFilePaths.append(replaceFilePathI2)

                replaceFileNameI2 = wx.StaticText(self, wx.ID_ANY, 'file' + str(i * 2 + 2), wx.DefaultPosition, wx.DefaultSize, 0)
                replaceFileNameI2.Wrap(-1)
                replaceFileNameI2.SetMinSize(wx.Size(260, -1))
                replaceBsI2.Add(replaceFileNameI2, 0, wx.ALL, 5)
                self.replaceFileNames.append(replaceFileNameI2)

                gSizer.Add(replaceBsI2, 1, wx.EXPAND, 5)

            replaceBsWrapper.Add(gSizer, 1, wx.EXPAND, 5)

        replaceBsBtn = wx.BoxSizer(wx.HORIZONTAL)
        replaceBsBtn.SetMinSize(wx.Size(-1, 20))
        self.replaceAndRestartBtn = wx.Button(self, 2001, '全部替换并重启', wx.DefaultPosition, wx.DefaultSize, 0)
        replaceBsBtn.Add(self.replaceAndRestartBtn, 0, wx.ALL, 5)
        self.replaceAndRestartBtnInTime = wx.Button(self, 2008, '全部替换并同时重启', wx.DefaultPosition, wx.DefaultSize, 0)
        replaceBsBtn.Add(self.replaceAndRestartBtnInTime, 0, wx.ALL, 5)
        self.replaceBtn = wx.Button(self, 2002, '仅替换', wx.DefaultPosition, wx.DefaultSize, 0)
        replaceBsBtn.Add(self.replaceBtn, 0, wx.ALL, 5)
        self.restartBtn = wx.Button(self, 2003, '仅重启', wx.DefaultPosition, wx.DefaultSize, 0)
        replaceBsBtn.Add(self.restartBtn, 0, wx.ALL, 5)
        self.selectReplaceAndRestartBtn = wx.Button(self, 2004, '选择替换并重启', wx.DefaultPosition, wx.DefaultSize, 0)
        replaceBsBtn.Add(self.selectReplaceAndRestartBtn, 0, wx.ALL, 5)
        self.selectReplaceBtn = wx.Button(self, 2005, '选择仅替换', wx.DefaultPosition, wx.DefaultSize, 0)
        replaceBsBtn.Add(self.selectReplaceBtn, 0, wx.ALL, 5)
        self.selectRestartBtn = wx.Button(self, 2006, '选择仅重启', wx.DefaultPosition, wx.DefaultSize, 0)
        replaceBsBtn.Add(self.selectRestartBtn, 0, wx.ALL, 5)
        self.selectCloseBtn = wx.Button(self, 2007, '选择关闭', wx.DefaultPosition, wx.DefaultSize, 0)
        replaceBsBtn.Add(self.selectCloseBtn, 0, wx.ALL, 5)
        self.selectCloseBtn = wx.Button(self, 2100, 'testdp发版', wx.DefaultPosition, wx.DefaultSize, 0)
        replaceBsBtn.Add(self.selectCloseBtn, 0, wx.ALL, 5)
        replaceBsWrapper.Add(replaceBsBtn, 1, wx.EXPAND, 5)

        self.SetSizer(replaceBsWrapper)
        self.Layout()

        self.Centre(wx.BOTH)
        # 绑定事件
        self.Bind(wx.EVT_CLOSE, self._when_close)
        self.replaceAndRestartBtn.Bind(wx.EVT_BUTTON, self.about_tomcat)
        self.replaceAndRestartBtnInTime.Bind(wx.EVT_BUTTON, self.about_tomcat)
        self.replaceBtn.Bind(wx.EVT_BUTTON, self.about_tomcat)
        self.restartBtn.Bind(wx.EVT_BUTTON, self.about_tomcat)
        self.selectReplaceAndRestartBtn.Bind(wx.EVT_BUTTON, self.about_tomcat)
        self.selectReplaceBtn.Bind(wx.EVT_BUTTON, self.about_tomcat)
        self.selectRestartBtn.Bind(wx.EVT_BUTTON, self.about_tomcat)
        self.selectCloseBtn.Bind(wx.EVT_BUTTON, self.about_tomcat)

        # 加载要替换的文件
        self.load_replace_file()

    # 操作tomcat
    def about_tomcat(self, event):
        if event.GetId() == 2001:  # 全部替换并重启
            TestThread(self.replace_dic, self.project)
            self.Close()
        elif event.GetId() == 2002:  # 仅替换
            TestThread(self.replace_dic, self.project, need_close=False, need_start=False)
            self.Close()
        elif event.GetId() == 2003:  # 仅重启
            TestThread({}, self.project, need_replace=False)
            self.Close()
        elif event.GetId() == 2004:  # 选择替换并重启
            ChooseTargetIp(self, self.project).Show()
        elif event.GetId() == 2005:  # 选择仅替换
            ChooseTargetIp(self, self.project, need_close=False, need_start=False).Show()
        elif event.GetId() == 2006:  # 选择仅重启
            ChooseTargetIp(self, self.project, need_replace=False).Show()
        elif event.GetId() == 2007:  # 选择关闭
            ChooseTargetIp(self, self.project, need_replace=False, need_start=False).Show()
        elif event.GetId() == 2008:  # 全部替换并同时重启
            for i, ip in enumerate(self.project['ips']):
                target_ips = [''] * len(self.project['ips'])
                target_ips[i] = ip
                TestThread(self.replace_dic, self.project, target_ips)
            self.Close()
        elif event.GetId() == 2100:  # Test 测试服务器发版
            self.load_compiled_replace_file(self.project['compiled_location'])
            TestThread(self.replace_dic, self.project, need_delete_all_exist=True)
            self.Close()

    # 加载要替换的文件
    def load_replace_file(self):
        project = self.project
        index = 0
        for filename in glob.glob(replace_project_dir + '\\**\\*', recursive=True):
            if os.path.isfile(filename) and filename.find(project['project_name'] + '\\') != -1:
                rel_remote_location = filename.split(project['project_name'])[1].replace('\\', '/')
                self.replace_dic[filename] = project['app_location'] + rel_remote_location
                # 设置显示label标签
                label = os.path.basename(filename)
                # 超过的部分不再显示
                if index < size:
                    self.replaceFileNames[index].SetLabel(label)
                    self.replaceFilePaths[index].SetValue(rel_remote_location)
                    index += 1

    # testdp发版 加载编译后文件
    def load_compiled_replace_file(self, compiled_location):
        global replace_project_dir
        replace_project_dir = compiled_location
        project = self.project
        self.replace_dic = {}
        for filename in glob.glob(compiled_location + '\\**\\*', recursive=True):
            if os.path.isfile(filename) and filename.find(project['project_name'] + '\\') != -1:
                rel_remote_location = filename.split(project['project_name'])[1].replace('\\', '/')
                self.replace_dic[filename] = project['app_location'] + rel_remote_location

    def current_project(self):
        global projects
        project = {}
        if self.menu_id == 201:
            project = projects['prod']['gccce']
        if self.menu_id == 202:
            project = projects['prod']['task']
        if self.menu_id == 203:
            project = projects['prod']['bg']
        if self.menu_id == 204:
            project = projects['prod']['api']
        if self.menu_id == 205:
            project = projects['prod']['master']
        if self.menu_id == 206:
            project = projects['prod']['dws-hw']
        if self.menu_id == 207:
            project = projects['prod']['dws-yz']
        if self.menu_id == 208:
            project = projects['prod']['water-backend']
        if self.menu_id == 209:
            project = projects['prod']['bid-data-interface']

        if self.menu_id == 301:
            project = projects['recycle']['api']
        if self.menu_id == 302:
            project = projects['recycle']['master']
        if self.menu_id == 303:
            project = projects['recycle']['bid_data_interface']
        return project

    @staticmethod
    def _when_close(event):
        global searchFileThreadFlag
        searchFileThreadFlag = False
        event.Skip()

    def __del__(self):
        pass


class ChooseTargetIp(wx.Frame):
    def __init__(self, parent, project, need_replace=True, need_close=True, need_start=True):
        self.parent = parent
        self.project = project
        self.need_replace = need_replace
        self.need_close = need_close
        self.need_start = need_start

        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title='选择IP', pos=wx.DefaultPosition,
                          size=wx.Size(400, 400), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(wx.Colour(223, 223, 223))

        self.buttons = []
        self.mainGridSizer = wx.GridSizer(3, 3, 5, 5)

        self.SetSizer(self.mainGridSizer)
        self.Layout()
        self.Centre(wx.BOTH)

        # Connect Events
        for i, ip in enumerate(project['ips']):
            self.create_grid()
            self.buttons[i].SetLabel(ip)
            self.buttons[i].Bind(wx.EVT_LEFT_DOWN, self.about_tomcat)

    def __del__(self):
        pass

    def about_tomcat(self, event):
        btn = event.GetEventObject()

        target_ips = [''] * pow(grid_count, 2)
        target_ips[self.buttons.index(btn)] = btn.GetLabel()
        TestThread(self.parent.replace_dic, self.project, target_ips,
                   need_replace=self.need_replace, need_close=self.need_close, need_start=self.need_start)
        self.Close()
        self.parent.Close()

    def create_grid(self):
        bSizer = wx.BoxSizer(wx.VERTICAL)
        m_button = wx.Button(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer.Add(m_button, 0, wx.ALL, 5)
        self.mainGridSizer.Add(bSizer, 1, wx.EXPAND, 5)
        self.buttons.append(m_button)


def send_wx_pub(content, index, project):
    wx.CallAfter(pub.sendMessage, 'update%s' % index, log_out_index=index, project=project,
                 log_out=[bytes(content, encoding='utf-8')])
