import time
from threading import Thread
import pysftp
import wx
import wx.xrc
from wx.lib.pubsub import pub

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

threadFlag = False
tailLogFlag = [True, True, True, True]  # 是否追踪日志


# 监控tomcat输出日志
def tail_log(sftp, log_out_index, ip, project, outs):
    out = sftp.execute('tail -n ' + str(project['logs_tail_size']) + ' ' + project['tomcat_location'] + '/logs/catalina.out')
    if tailLogFlag[log_out_index]:
        new_out = [i for i in out if i not in outs and len(i) < project['logs_line_length']]
        wx.CallAfter(pub.sendMessage, 'update' + str(log_out_index), log_out_index=log_out_index, project=project, log_out=new_out)
    else:
        wx.CallAfter(pub.sendMessage, 'update' + str(log_out_index), log_out_index=log_out_index, project=project, tail_log_flag=False)
    time.sleep(1)
    if threadFlag:
        tail_log(sftp, log_out_index, ip, project, out)


cnopts = pysftp.CnOpts()
cnopts.hostkeys = None


def connect_tomcat(log_out_index, ip, project):
    with pysftp.Connection(ip, username=project['username'], password=project['password'], cnopts=cnopts) as sftp:
        print(ip)
        tail_log(sftp, log_out_index, ip, project, [])


class TestThread(Thread):
    def __init__(self, log_out_index, ip, project):
        Thread.__init__(self)
        self.log_out_index = log_out_index
        self.ip = ip
        self.project = project
        self.start()

    def run(self):
        time.sleep(self.log_out_index * 1.5)
        connect_tomcat(log_out_index=self.log_out_index, ip=self.ip, project=self.project)


def start_thread(project):
    for i, ip in enumerate(project['ips']):
        TestThread(i, ip, project)


# 主窗口
class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title='日志查看', pos=wx.DefaultPosition, size=wx.Size(1700, 980),
                          style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)
        # 主页面元素
        self.StIps = []
        self.TcLogOuts = []
        # 状态变量
        self.cur_label = ''

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(wx.Colour(223, 223, 223))

        mainGridSizer = wx.GridSizer(2, 2, 5, 5)

        # 第一个日志输出
        boxSizer1 = wx.BoxSizer(wx.VERTICAL)
        self.ip1 = wx.StaticText(self, 1011, 'ip1', wx.DefaultPosition, wx.DefaultSize, 0)
        self.ip1.Wrap(-1)
        boxSizer1.Add(self.ip1, 0, wx.ALL, 5)
        self.logOut1 = wx.TextCtrl(self, 1012, wx.EmptyString,
                                   wx.DefaultPosition, wx.Size(2000, 2000),
                                   wx.TE_MULTILINE)
        self.logOut1.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), 70, 90, 90, False, wx.EmptyString))
        boxSizer1.Add(self.logOut1, 0, wx.ALL, 5)
        # 第一个日志输出结束

        # 第二个日志输出
        boxSizer2 = wx.BoxSizer(wx.VERTICAL)
        self.ip2 = wx.StaticText(self, 1021, 'ip2', wx.DefaultPosition, wx.DefaultSize, 0)
        self.ip2.Wrap(-1)
        boxSizer2.Add(self.ip2, 0, wx.ALL, 5)
        self.logOut2 = wx.TextCtrl(self, 1022, wx.EmptyString,
                                   wx.DefaultPosition, wx.Size(2000, 2000),
                                   wx.TE_CHARWRAP | wx.TE_MULTILINE | wx.TE_WORDWRAP)
        self.logOut2.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), 70, 90, 90, False, wx.EmptyString))
        boxSizer2.Add(self.logOut2, 0, wx.ALL, 5)
        # 第二个日志输出结束

        # 第三个日志输出
        boxSizer3 = wx.BoxSizer(wx.VERTICAL)
        self.ip3 = wx.StaticText(self, 1031, 'ip3', wx.DefaultPosition, wx.DefaultSize, 0)
        self.ip3.Wrap(-1)
        boxSizer3.Add(self.ip3, 0, wx.ALL, 5)
        self.logOut3 = wx.TextCtrl(self, 1032, wx.EmptyString,
                                   wx.DefaultPosition, wx.Size(2000, 2000),
                                   wx.TE_CHARWRAP | wx.TE_MULTILINE | wx.TE_WORDWRAP)
        self.logOut3.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), 70, 90, 90, False, wx.EmptyString))
        boxSizer3.Add(self.logOut3, 0, wx.ALL, 5)
        # 第三个日志输出结束

        # 第四个日志输出
        boxSizer4 = wx.BoxSizer(wx.VERTICAL)
        self.ip4 = wx.StaticText(self, 1041, 'ip4', wx.DefaultPosition, wx.DefaultSize, 0)
        self.ip4.Wrap(-1)
        boxSizer4.Add(self.ip4, 0, wx.ALL, 5)
        self.logOut4 = wx.TextCtrl(self, 1042, wx.EmptyString,
                                   wx.DefaultPosition, wx.Size(2000, 2000),
                                   wx.TE_CHARWRAP | wx.TE_MULTILINE | wx.TE_WORDWRAP)
        self.logOut4.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), 70, 90, 90, False, wx.EmptyString))
        boxSizer4.Add(self.logOut4, 0, wx.ALL, 5)
        # 第四个日志输出结束
        self.StIps.append(self.ip1)
        self.StIps.append(self.ip2)
        self.StIps.append(self.ip3)
        self.StIps.append(self.ip4)
        self.TcLogOuts.append(self.logOut1)
        self.TcLogOuts.append(self.logOut2)
        self.TcLogOuts.append(self.logOut3)
        self.TcLogOuts.append(self.logOut4)

        mainGridSizer.Add(boxSizer1, 1, wx.EXPAND, 5)
        mainGridSizer.Add(boxSizer2, 2, wx.EXPAND, 5)
        mainGridSizer.Add(boxSizer3, 3, wx.EXPAND, 5)
        mainGridSizer.Add(boxSizer4, 4, wx.EXPAND, 5)

        self.SetSizer(mainGridSizer)
        self.Layout()

        # 菜单栏
        self.mainMenuBar = wx.MenuBar(0)
        # menu1
        self.menu1 = wx.Menu()
        self.gccce = wx.MenuItem(self.menu1, wx.ID_ANY, 'gccce', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu1.Append(self.gccce)
        self.task = wx.MenuItem(self.menu1, wx.ID_ANY, 'task', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu1.Append(self.task)
        self.bg = wx.MenuItem(self.menu1, wx.ID_ANY, 'bg', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu1.Append(self.bg)
        self.api = wx.MenuItem(self.menu1, wx.ID_ANY, 'api', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu1.Append(self.api)
        self.master = wx.MenuItem(self.menu1, wx.ID_ANY, 'master', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu1.Append(self.master)
        self.test = wx.MenuItem(self.menu1, wx.ID_ANY, '测试api', wx.EmptyString, wx.ITEM_NORMAL)
        self.menu1.Append(self.test)
        self.mainMenuBar.Append(self.menu1, '选择项目')

        self.SetMenuBar(self.mainMenuBar)

        # 绑定事件
        self.Bind(wx.EVT_MENU, self.run_thread, self.gccce)
        self.Bind(wx.EVT_MENU, self.run_thread, self.task)
        self.Bind(wx.EVT_MENU, self.run_thread, self.bg)
        self.Bind(wx.EVT_MENU, self.run_thread, self.api)
        self.Bind(wx.EVT_MENU, self.run_thread, self.master)
        self.Bind(wx.EVT_MENU, self.run_thread, self.test)
        # 切换日志跟踪
        self.logOut1.Bind(wx.EVT_LEFT_DCLICK, self.toggle_scroll_logout)
        self.logOut2.Bind(wx.EVT_LEFT_DCLICK, self.toggle_scroll_logout)
        self.logOut3.Bind(wx.EVT_LEFT_DCLICK, self.toggle_scroll_logout)
        self.logOut4.Bind(wx.EVT_LEFT_DCLICK, self.toggle_scroll_logout)

        self.Centre(wx.BOTH)
        # 更新日志输出
        pub.subscribe(self.update_display, 'update0')
        pub.subscribe(self.update_display, 'update1')
        pub.subscribe(self.update_display, 'update2')
        pub.subscribe(self.update_display, 'update3')
        # 清空日志输出
        pub.subscribe(self.empty_content, 'empty')
        pub.subscribe(self.empty_content_all, 'empty_all')
        pub.subscribe(self.stop_thread, 'stop_all')

    # 停止日志滚动
    def toggle_scroll_logout(self, event):
        global tailLogFlag
        target_id = event.GetId()
        if target_id == 1012:
            tailLogFlag[0] = not tailLogFlag[0]
        elif target_id == 1022:
            tailLogFlag[1] = not tailLogFlag[1]
        elif target_id == 1032:
            tailLogFlag[2] = not tailLogFlag[2]
        elif target_id == 1042:
            tailLogFlag[3] = not tailLogFlag[3]
            # self.ScrollLogOutFlag[3] = True
            # self.ScrollLogOutLineNum[3] = self.TcLogOuts[3].GetInsertionPoint()-200
        event.Skip()

    # 输出日志
    def update_display(self, log_out_index, project, log_out=(), tail_log_flag=True):
        cur_ip = self.StIps[log_out_index]
        cur_log_out = self.TcLogOuts[log_out_index]
        if tail_log_flag:
            cur_ip.SetLabel(self.cur_label + '  ' + project['ips'][log_out_index])
            if cur_log_out.GetNumberOfLines() > 1000:
                cur_log_out.Remove(1, 800)
            local_log = ''
            for o in log_out:
                local_log += str(o, 'utf-8').replace('\n', '') + '\r\n'
            cur_log_out.AppendText(local_log)
            # if self.ScrollLogOutFlag[log_out_index]:
            #     cur_log_out.ShowPosition(self.ScrollLogOutLineNum[log_out_index])
        else:
            cur_ip.SetLabel(self.cur_label + '  ' + project['ips'][log_out_index] + '    已暂停')

    # 停止跟踪日志
    def stop_thread(self):
        global threadFlag
        threadFlag = False
        time.sleep(1)
        self.empty_content_all()
        threadFlag = True

    # 启动日志查看
    def run_thread(self, event):
        self.stop_thread()
        is_selected = event.GetId()
        menu = event.GetEventObject()
        self.cur_label = menu.GetLabelText(is_selected)
        label = self.cur_label

        project = {}
        if label == 'gccce':
            project = projects['prod']['gccce']
        elif label == 'task':
            project = projects['prod']['task']
        elif label == 'bg':
            project = projects['prod']['bg']
        elif label == 'api':
            project = projects['prod']['api']
        elif label == 'master':
            project = projects['prod']['master']
        elif label == '测试api':
            project = projects['recycle']['api']
        start_thread(project)

    # 清除所有的日志
    def empty_content_all(self):
        self.empty_content(1)
        self.empty_content(2)
        self.empty_content(3)
        self.empty_content(4)

    # 清除特定的日志
    def empty_content(self, frame_count):
        if frame_count == 1:
            self.ip1.SetLabel('ip1')
            self.logOut1.SetLabel('')
            tailLogFlag[0] = True
        if frame_count == 2:
            self.ip2.SetLabel('ip2')
            self.logOut2.SetLabel('')
            tailLogFlag[1] = True
        if frame_count == 3:
            self.ip3.SetLabel('ip3')
            self.logOut3.SetLabel('')
            tailLogFlag[2] = True
        if frame_count == 4:
            self.ip4.SetLabel('ip4')
            self.logOut4.SetLabel('')
            tailLogFlag[3] = True

    def __del__(self):
        pass


if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame(None).Show()
    app.MainLoop()
