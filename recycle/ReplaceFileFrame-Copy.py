import wx
import wx.xrc
import os
import pysftp
import re
import time
import glob
import json
from threading import Thread
from wx.lib.pubsub import pub

searchFileThreadFlag = True
# 项目配置
projects = {
    'prod': {
        'gccce': {
            'project_name': 'gcj_customer_service',
            'ips': ['10.126.15.196', '10.126.15.197', '10.126.15.202', '10.126.15.203'],
            'username': 'paas',
            'password': '123qwe!@#',
            'tomcat_location': '/opt/apache-tomcat-7.0.47_8080',
            'app_location': '/opt/project/webapps_8080/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        },
        'task': {
            'project_name': 'gcj_cstm_task_manager',
            'ips': ['10.126.15.208', '10.126.15.231', '10.126.15.232'],
            'username': 'paas',
            'password': '123qwe!@#',
            'tomcat_location': '/opt/apache-tomcat-7.0.47_8080',
            'app_location': '/opt/project/webapps_8080/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        },
        'bg': {
            'project_name': 'member_center_bg',
            'ips': ['10.126.15.184', '10.126.15.185'],
            'username': 'paas',
            'password': '123qwe!@#',
            'tomcat_location': '/opt/apache-tomcat-7.0.47_8080',
            'app_location': '/opt/project/webapps_8080/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        },
        'api': {
            'project_name': 'member_center_api',
            'ips': ['10.126.15.182', '10.126.15.183', '10.126.14.63'],
            'username': 'paas',
            'password': '123qwe!@#',
            'tomcat_location': '/opt/apache-tomcat-7.0.47_8080',
            'app_location': '/opt/project/webapps_8080/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        },
        'master': {
            'project_name': 'gcw_master_site',
            'ips': ['10.126.15.139', '10.126.15.140', '10.126.15.141', '10.126.15.142'],
            'username': 'paas',
            'password': '123qwe!@#',
            'tomcat_location': '/opt/apache-tomcat-7.0.47_8080',
            'app_location': '/opt/project/webapps_8080/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        }
    },
    'recycle': {
        'api': {
            'project_name': 'member_center_api',
            'ips': ['192.168.133.177', '192.168.133.177'],
            'username': 'root',
            'password': '123qwe!@#',
            'tomcat_location': '/opt/tomcats/apache-tomcat-member-center-api',
            'app_location': '/opt/tomcats/apache-tomcat-member-center-api/webapps/ROOT',
            'logs_tail_size': 20,
            'logs_line_length': 1000
        }
    }
}

# 替换文件
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None


def operate_tomcat(replace_dic, project, target_ips):
    if len(target_ips) == 0:
        target_ips = project['ips']
    for i, ip in enumerate(target_ips):
        print('【准备进行操作 %d/%d IP:%s】' % (i + 1, len(target_ips), ip))
        result = replace_file(replace_dic, log_out_index=i, ip=ip, project=project)
        if result != 'success':
            break
        else:
            print('【操作已完成 %d/%d IP:%s】\n' % (i + 1, len(target_ips), ip))


def replace_file(replace_dic, log_out_index, ip, project):
    with pysftp.Connection(host=ip, username=project['username'], password=project['password'], cnopts=cnopts) as sftp:
        # with sftp.cd('/opt/project/webapps_8080/ROOT'):
        replace_flag = False
        restart_flag = False
        # 替换文件
        with sftp.cd(project['app_location']):
            valid = True
            for (source, target) in replace_dic.items():
                print('来源文件:' + source + '   目标文件:' + target + '  ' + str(sftp.exists(target)))
                valid = valid & sftp.exists(target)
                restart_flag = restart_flag | (str(source).endswith('.class') | str(source).endswith('Mapper.xml'))
            if valid:
                print('校验成功 正在替换文件')
                for (source, target) in replace_dic.items():
                    sftp.get(target, str(source).replace('replaceFiles', 'recycle'),
                             preserve_mtime=True)  # 保存被替换的文件，以防出问题
                    sftp.put(source, target)
                replace_flag = True
                print('替换文件成功')
            if not restart_flag and len(replace_dic) > 0:
                print('未发现.class文件，无需重启tomcat')
                wx.CallAfter(pub.sendMessage, 'update' + str(log_out_index), log_out_index=log_out_index,
                             project=project,
                             log_out=[bytes("已替换完成，无需重启tomcat", encoding='utf-8')])
                return 'success'
        # 关闭当前tomcat进程
        if replace_flag and (restart_flag or len(replace_dic) == 0):
            print('正在重启tomcat')
            with sftp.cd(project['tomcat_location']):
                grep = sftp.execute('ps -ef | grep ' + project['tomcat_location'][-10:])
                for g in grep:
                    gStr = str(g, 'utf-8')
                    if re.search(project['tomcat_location'], gStr) is not None:
                        pid = re.split('\s+', gStr)[1]
                        sftp.execute('kill -9 ' + pid)
                sftp.execute(sftp.getcwd() + '/bin/catalina.sh start')
                return tailLog(sftp, log_out_index, ip, project, [], False)


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
        if re.search('Server startup in [\d|,]+ ms\Z', line) is not None and first_flag:
            restart = True
            wx.CallAfter(pub.sendMessage, 'update' + str(log_out_index), log_out_index=log_out_index, project=project,
                         log_out=[b'------------- Tomcat Restart Success! --------------'])
            print(line)
            print('-------------' + ip + ' Tomcat 重新启动成功 --------------')
    if not restart:
        time.sleep(1)
        return tailLog(sftp, log_out_index, ip, project, out, True)
    if restart:
        return 'success'


class TestThread(Thread):
    def __init__(self, replace_dic, project, target_ips=()):
        Thread.__init__(self)
        self.replace_dic = replace_dic
        self.project = project
        self.target_ips = target_ips
        self.start()

    def run(self):
        # 停止先前的日志输出
        wx.CallAfter(pub.sendMessage, 'stop_all')
        time.sleep(1)
        operate_tomcat(replace_dic=self.replace_dic, project=self.project, target_ips=self.target_ips)


class SearchFilesThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.start()

    def run(self):
        while searchFileThreadFlag:
            time.sleep(1)
            files = glob.glob(os.path.join(os.getcwd(), 'replaceFiles/*'))
            files.sort(key=os.path.getctime)
            wx.CallAfter(pub.sendMessage, 'search_files', files=files)


# 替换文件的窗口
class ReplaceFileFrame(wx.Frame):
    def __init__(self, parent, menu_id):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title='文件替换', pos=wx.DefaultPosition,
                          size=wx.Size(1000, 500), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)
        self.files = []
        self.replace_dic = {}
        self.menu_id = menu_id
        self.project = self.current_project()
        global searchFileThreadFlag
        searchFileThreadFlag = True

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(wx.Colour(223, 223, 223))

        replaceBsWrapper = wx.BoxSizer(wx.VERTICAL)

        replaceBs1 = wx.BoxSizer(wx.HORIZONTAL)
        replaceBs1.SetMinSize(wx.Size(-1, 20))
        self.replaceFileName1 = wx.StaticText(self, wx.ID_ANY, 'file1', wx.DefaultPosition, wx.DefaultSize, 0)
        self.replaceFileName1.Wrap(-1)
        self.replaceFileName1.SetMinSize(wx.Size(260, -1))
        replaceBs1.Add(self.replaceFileName1, 0, wx.ALL, 5)
        self.replaceFilePath1 = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(800, -1), 0)
        replaceBs1.Add(self.replaceFilePath1, 0, wx.ALL, 5)
        replaceBsWrapper.Add(replaceBs1, 1, wx.EXPAND, 5)

        replaceBs2 = wx.BoxSizer(wx.HORIZONTAL)
        replaceBs2.SetMinSize(wx.Size(-1, 20))
        self.replaceFileName2 = wx.StaticText(self, wx.ID_ANY, 'file2', wx.DefaultPosition, wx.DefaultSize, 0)
        self.replaceFileName2.Wrap(-1)
        self.replaceFileName2.SetMinSize(wx.Size(260, -1))
        replaceBs2.Add(self.replaceFileName2, 0, wx.ALL, 5)
        self.replaceFilePath2 = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(800, -1), 0)
        replaceBs2.Add(self.replaceFilePath2, 0, wx.ALL, 5)
        replaceBsWrapper.Add(replaceBs2, 1, wx.EXPAND, 5)

        replaceBs3 = wx.BoxSizer(wx.HORIZONTAL)
        replaceBs3.SetMinSize(wx.Size(-1, 20))
        self.replaceFileName3 = wx.StaticText(self, wx.ID_ANY, 'file3', wx.DefaultPosition, wx.DefaultSize, 0)
        self.replaceFileName3.Wrap(-1)
        self.replaceFileName3.SetMinSize(wx.Size(260, -1))
        replaceBs3.Add(self.replaceFileName3, 0, wx.ALL, 5)
        self.replaceFilePath3 = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(800, -1), 0)
        replaceBs3.Add(self.replaceFilePath3, 0, wx.ALL, 5)
        replaceBsWrapper.Add(replaceBs3, 1, wx.EXPAND, 5)

        replaceBs4 = wx.BoxSizer(wx.HORIZONTAL)
        replaceBs4.SetMinSize(wx.Size(-1, 20))
        self.replaceFileName4 = wx.StaticText(self, wx.ID_ANY, 'file4', wx.DefaultPosition, wx.DefaultSize, 0)
        self.replaceFileName4.Wrap(-1)
        self.replaceFileName4.SetMinSize(wx.Size(260, -1))
        replaceBs4.Add(self.replaceFileName4, 0, wx.ALL, 5)
        self.replaceFilePath4 = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(800, -1), 0)
        replaceBs4.Add(self.replaceFilePath4, 0, wx.ALL, 5)
        replaceBsWrapper.Add(replaceBs4, 1, wx.EXPAND, 5)

        replaceBs5 = wx.BoxSizer(wx.HORIZONTAL)
        replaceBs5.SetMinSize(wx.Size(-1, 20))
        self.replaceFileName5 = wx.StaticText(self, wx.ID_ANY, 'file5', wx.DefaultPosition, wx.DefaultSize, 0)
        self.replaceFileName5.Wrap(-1)
        self.replaceFileName5.SetMinSize(wx.Size(260, -1))
        replaceBs5.Add(self.replaceFileName5, 0, wx.ALL, 5)
        self.replaceFilePath5 = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(800, -1), 0)
        replaceBs5.Add(self.replaceFilePath5, 0, wx.ALL, 5)
        replaceBsWrapper.Add(replaceBs5, 1, wx.EXPAND, 5)

        replaceBs6 = wx.BoxSizer(wx.HORIZONTAL)
        replaceBs6.SetMinSize(wx.Size(-1, 20))
        self.replaceFileName6 = wx.StaticText(self, wx.ID_ANY, 'file6', wx.DefaultPosition, wx.DefaultSize, 0)
        self.replaceFileName6.Wrap(-1)
        self.replaceFileName6.SetMinSize(wx.Size(260, -1))
        replaceBs6.Add(self.replaceFileName6, 0, wx.ALL, 5)
        self.replaceFilePath6 = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(800, -1), 0)
        replaceBs6.Add(self.replaceFilePath6, 0, wx.ALL, 5)
        replaceBsWrapper.Add(replaceBs6, 1, wx.EXPAND, 5)

        replaceBs7 = wx.BoxSizer(wx.HORIZONTAL)
        replaceBs7.SetMinSize(wx.Size(-1, 20))
        self.replaceFileName7 = wx.StaticText(self, wx.ID_ANY, 'file7', wx.DefaultPosition, wx.DefaultSize, 0)
        self.replaceFileName7.Wrap(-1)
        self.replaceFileName7.SetMinSize(wx.Size(260, -1))
        replaceBs7.Add(self.replaceFileName7, 0, wx.ALL, 5)
        self.replaceFilePath7 = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(800, -1), 0)
        replaceBs7.Add(self.replaceFilePath7, 0, wx.ALL, 5)
        replaceBsWrapper.Add(replaceBs7, 1, wx.EXPAND, 5)

        replaceBs8 = wx.BoxSizer(wx.HORIZONTAL)
        replaceBs8.SetMinSize(wx.Size(-1, 20))
        self.replaceFileName8 = wx.StaticText(self, wx.ID_ANY, 'file8', wx.DefaultPosition, wx.DefaultSize, 0)
        self.replaceFileName8.Wrap(-1)
        self.replaceFileName8.SetMinSize(wx.Size(260, -1))
        replaceBs8.Add(self.replaceFileName8, 0, wx.ALL, 5)
        self.replaceFilePath8 = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(800, -1), 0)
        replaceBs8.Add(self.replaceFilePath8, 0, wx.ALL, 5)
        replaceBsWrapper.Add(replaceBs8, 1, wx.EXPAND, 5)

        replaceBs9 = wx.BoxSizer(wx.HORIZONTAL)
        replaceBs9.SetMinSize(wx.Size(-1, 20))
        self.replaceFileName9 = wx.StaticText(self, wx.ID_ANY, 'file9', wx.DefaultPosition, wx.DefaultSize, 0)
        self.replaceFileName9.Wrap(-1)
        self.replaceFileName9.SetMinSize(wx.Size(260, -1))
        replaceBs9.Add(self.replaceFileName9, 0, wx.ALL, 5)
        self.replaceFilePath9 = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(800, -1), 0)
        replaceBs9.Add(self.replaceFilePath9, 0, wx.ALL, 5)
        replaceBsWrapper.Add(replaceBs9, 1, wx.EXPAND, 5)

        replaceBs10 = wx.BoxSizer(wx.HORIZONTAL)
        replaceBs10.SetMinSize(wx.Size(-1, 20))
        self.replaceFileName10 = wx.StaticText(self, wx.ID_ANY, 'file10', wx.DefaultPosition, wx.DefaultSize, 0)
        self.replaceFileName10.Wrap(-1)
        self.replaceFileName10.SetMinSize(wx.Size(260, -1))
        replaceBs10.Add(self.replaceFileName10, 0, wx.ALL, 5)
        self.replaceFilePath10 = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(800, -1), 0)
        replaceBs10.Add(self.replaceFilePath10, 0, wx.ALL, 5)
        replaceBsWrapper.Add(replaceBs10, 1, wx.EXPAND, 5)

        replaceBsBtn = wx.BoxSizer(wx.HORIZONTAL)
        replaceBsBtn.SetMinSize(wx.Size(-1, 20))
        self.replaceAndRestartBtn = wx.Button(self, 2001, '全部替换并重启', wx.DefaultPosition, wx.DefaultSize, 0)
        replaceBsBtn.Add(self.replaceAndRestartBtn, 0, wx.ALL, 5)
        # self.replaceBtn = wx.Button(self, 2002, '仅替换', wx.DefaultPosition, wx.DefaultSize, 0)
        # replaceBsBtn.Add(self.replaceBtn, 0, wx.ALL, 5)
        self.restartBtn = wx.Button(self, 2003, '重启', wx.DefaultPosition, wx.DefaultSize, 0)
        replaceBsBtn.Add(self.restartBtn, 0, wx.ALL, 5)
        self.selectReplaceAndRestartBtn = wx.Button(self, 2004, '选择替换并重启', wx.DefaultPosition, wx.DefaultSize, 0)
        replaceBsBtn.Add(self.selectReplaceAndRestartBtn, 0, wx.ALL, 5)
        self.selectRestartBtn = wx.Button(self, 2004, '选择重启', wx.DefaultPosition, wx.DefaultSize, 0)
        replaceBsBtn.Add(self.selectRestartBtn, 0, wx.ALL, 5)
        replaceBsWrapper.Add(replaceBsBtn, 1, wx.EXPAND, 5)

        self.SetSizer(replaceBsWrapper)
        self.Layout()

        self.Centre(wx.BOTH)
        # 绑定事件
        self.Bind(wx.EVT_CLOSE, self._when_close)
        self.replaceAndRestartBtn.Bind(wx.EVT_BUTTON, self.about_tomcat)
        self.restartBtn.Bind(wx.EVT_BUTTON, self.restart_tomcat)
        self.selectReplaceAndRestartBtn.Bind(wx.EVT_BUTTON, self.select_about_tomcat)
        self.selectRestartBtn.Bind(wx.EVT_BUTTON, self.select_restart_tomcat)

        self.replaceFileNames = [self.replaceFileName1, self.replaceFileName2, self.replaceFileName3,
                                 self.replaceFileName4,
                                 self.replaceFileName5, self.replaceFileName6, self.replaceFileName7,
                                 self.replaceFileName8,
                                 self.replaceFileName9, self.replaceFileName10]
        self.replaceFilePaths = [self.replaceFilePath1, self.replaceFilePath2, self.replaceFilePath3,
                                 self.replaceFilePath4,
                                 self.replaceFilePath5, self.replaceFilePath6, self.replaceFilePath7,
                                 self.replaceFilePath8,
                                 self.replaceFilePath9, self.replaceFileName10]
        pub.subscribe(self.search_files, 'search_files')
        SearchFilesThread()

    # 循环遍历要替换的文件列表
    def search_files(self, files):
        former_dict = {}
        if os.path.exists('./dict'):
            with open(os.path.abspath('./dict'), 'r') as f:
                former_dict = json.loads(f.read())
        self.files = files
        for i, file in enumerate(files):
            self.replaceFileNames[i].SetLabel(file.split('\\')[-1])
            if former_dict.get(file):
                self.replaceFilePaths[i].SetValue(former_dict[file])
                # self.files = os.listdir(os.path.join(os.getcwd(), 'replaceFiles'))

    # 替换并重启tomcat
    def about_tomcat(self, event):
        self.load_replace_dic()
        TestThread(self.replace_dic, self.project)

    # 仅重启tomcat
    def restart_tomcat(self, event):
        TestThread({}, self.project)

    # 选择替换并重启
    def select_about_tomcat(self, event):
        self.load_replace_dic()
        ChooseTargetIp(self, self.project).Show()

    # 选择仅重启
    def select_restart_tomcat(self, event):
        self.load_replace_dic()
        ChooseTargetIp(self, self.project).Show()

    # 加载要替换的文件
    def load_replace_dic(self):
        global searchFileThreadFlag
        searchFileThreadFlag = False
        project = self.project
        json_dict = {}
        for i, file in enumerate(self.files):
            key = os.path.abspath('replaceFiles\\' + self.replaceFileNames[i].GetLabel())
            self.replace_dic[key] = project['app_location'] + \
                                    str(self.replaceFilePaths[i].GetValue()).split(project['project_name'])[1].replace(
                                        '\\', '/') + '/' + self.replaceFileNames[i].GetLabel()
            json_dict[key] = self.replaceFilePaths[i].GetValue()
            # '/opt/project/webapps_8080/ROOT' + str(self.replaceFilePaths[i].GetValue()).split(project_name[0])[1].replace('\\', '/') + '/' + self.replaceFileNames[i].GetLabel()
        # 保存文件对应路径
        with open(os.path.abspath('./dict'), 'w') as f:
            f.write(json.dumps(json_dict, indent=4))

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

        if self.menu_id == 301:
            project = projects['recycle']['api']
        return project

    @staticmethod
    def _when_close(event):
        global searchFileThreadFlag
        searchFileThreadFlag = False
        event.Skip()

    def __del__(self):
        pass


class ChooseTargetIp(wx.Frame):
    def __init__(self, parent, project):
        self.parent = parent
        self.project = project

        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title='选择IP', pos=wx.DefaultPosition,
                          size=wx.Size(300, 300), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(wx.Colour(223, 223, 223))

        mainGridSizer = wx.GridSizer(2, 2, 5, 5)
        bSizer1 = wx.BoxSizer(wx.VERTICAL)
        self.m_button1 = wx.Button(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer1.Add(self.m_button1, 0, wx.ALL, 5)
        mainGridSizer.Add(bSizer1, 1, wx.EXPAND, 5)

        bSizer2 = wx.BoxSizer(wx.VERTICAL)
        self.m_button2 = wx.Button(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.m_button2, 0, wx.ALL, 5)
        mainGridSizer.Add(bSizer2, 1, wx.EXPAND, 5)

        bSizer3 = wx.BoxSizer(wx.VERTICAL)
        self.m_button3 = wx.Button(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer3.Add(self.m_button3, 0, wx.ALL, 5)
        mainGridSizer.Add(bSizer3, 1, wx.EXPAND, 5)

        bSizer4 = wx.BoxSizer(wx.VERTICAL)
        self.m_button4 = wx.Button(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer4.Add(self.m_button4, 0, wx.ALL, 5)
        mainGridSizer.Add(bSizer4, 1, wx.EXPAND, 5)

        self.SetSizer(mainGridSizer)
        self.Layout()
        self.Centre(wx.BOTH)

        self.buttons = [self.m_button1, self.m_button2, self.m_button3, self.m_button4]
        # Connect Events
        for i, ip in enumerate(project['ips']):
            self.buttons[i].SetLabel(ip)
            self.buttons[i].Bind(wx.EVT_LEFT_DOWN, self.about_tomcat)

    def __del__(self):
        pass

    def about_tomcat(self, event):
        btn = event.GetEventObject()
        cur_ip = btn.GetLabel()
        TestThread(self.parent.replace_dic, self.project, (cur_ip,))
        self.Close()
