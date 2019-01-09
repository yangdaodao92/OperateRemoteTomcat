import time
from threading import Thread
import pysftp
import os
import wx
import wx.xrc
import conf
from wx.lib.pubsub import pub
from classes.ReplaceFileFrame import ReplaceFileFrame
from classes.ReplaceFileFrame import projects
from classes.ReplaceFileFrame import replace_project_dir
from classes import tailLog


class TestThread(Thread):
    def __init__(self, log_out_index, ip, project):
        Thread.__init__(self)
        self.log_out_index = log_out_index
        self.ip = ip
        self.project = project
        self.start()

    def run(self):
        time.sleep(self.log_out_index * 1.5)
        tailLog.connect_tomcat(log_out_index=self.log_out_index, ip=self.ip, project=self.project)


def start_thread(project):
    for i, ip in enumerate(project['ips']):
        TestThread(i, ip, project)


# 主窗口
class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title='日志查看', pos=wx.DefaultPosition, size=wx.Size(1800, 1000),
                          style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(wx.Colour(223, 223, 223))
        # 主页面元素数组
        self.StIps = []
        self.TcLogOuts = []
        self.tail_opts = []
        self.replace_menu_dic = {}
        # 状态变量
        self.cur_label = ''
        self.project = {}

        self.grid_count = conf.grid_count
        self.mainGridSizer = wx.GridSizer(self.grid_count, self.grid_count, 5, 5)
        for index in range(pow(self.grid_count, 2)):
            self.create_grid(index+1)
            # 更新日志输出
            pub.subscribe(self.update_display, 'update' + str(index))
        self.SetSizer(self.mainGridSizer)
        self.Layout()

        # 菜单栏
        self.mainMenuBar = wx.MenuBar(0)
        # menu1
        self.menu1 = wx.Menu()
        self.mainMenuBar.Append(self.menu1, '选择项目')
        self.create_menu(self.menu1, name='prod_gccce', bind_func=self.run_thread)
        self.create_menu(self.menu1, name='prod_task', bind_func=self.run_thread)
        self.create_menu(self.menu1, name='prod_bg', bind_func=self.run_thread)
        self.create_menu(self.menu1, name='prod_api', bind_func=self.run_thread)
        self.create_menu(self.menu1, name='prod_master', bind_func=self.run_thread)
        self.create_menu(self.menu1, name='prod_dws-hw', bind_func=self.run_thread)
        self.create_menu(self.menu1, name='prod_dws-yz', bind_func=self.run_thread)
        self.create_menu(self.menu1, name='prod_water-backend', bind_func=self.run_thread)
        self.create_menu(self.menu1, name='prod_bid-data-interface', bind_func=self.run_thread)
        self.create_menu(self.menu1, name='recycle_api', bind_func=self.run_thread)
        self.create_menu(self.menu1, name='recycle_master', bind_func=self.run_thread)

        # menu2
        self.menu2 = wx.Menu()
        self.mainMenuBar.Append(self.menu2, '替换生产文件')
        self.replace_menu_dic['gcj_customer_service'] = self.create_menu(self.menu2, name='替换gccce', wx_id=201, bind_func=self.open_replace_window)
        self.replace_menu_dic['gcj_cstm_task_manager'] = self.create_menu(self.menu2, name='替换task', wx_id=202, bind_func=self.open_replace_window)
        self.replace_menu_dic['member_center_bg'] = self.create_menu(self.menu2, name='替换bg', wx_id=203, bind_func=self.open_replace_window)
        self.replace_menu_dic['member_center_api'] = self.create_menu(self.menu2, name='替换api', wx_id=204, bind_func=self.open_replace_window)
        self.replace_menu_dic['gcw_master_site'] = self.create_menu(self.menu2, name='替换master', wx_id=205, bind_func=self.open_replace_window)
        self.replace_menu_dic['gcj_dws_hw_online'] = self.create_menu(self.menu2, name='替换dws-hw', wx_id=206, bind_func=self.open_replace_window)
        self.replace_menu_dic['gcj_dws_yz'] = self.create_menu(self.menu2, name='替换dws-yz', wx_id=207, bind_func=self.open_replace_window)
        self.replace_menu_dic['waterdrop_admin_online'] = self.create_menu(self.menu2, name='替换water-backend', wx_id=208, bind_func=self.open_replace_window)
        self.replace_menu_dic['bid_data_interface_online'] = self.create_menu(self.menu2, name='替换bid-data-interface', wx_id=209, bind_func=self.open_replace_window)

        # menu3 测试服务器
        self.menu3 = wx.Menu()
        self.mainMenuBar.Append(self.menu3, '替换测试文件')
        self.replace_menu_dic['member_center_api-test'] = self.create_menu(self.menu3, name='替换测试api', wx_id=301, bind_func=self.open_replace_window)
        self.replace_menu_dic['gcw_master_site-test'] = self.create_menu(self.menu3, name='替换测试master', wx_id=302, bind_func=self.open_replace_window)
        self.replace_menu_dic['bid_data_interface-test'] = self.create_menu(self.menu3, name='替换测试bid_data_interface', wx_id=303, bind_func=self.open_replace_window)

        self.SetMenuBar(self.mainMenuBar)
        self.Centre(wx.BOTH)

        # 清空日志输出
        pub.subscribe(self.empty_content, 'empty')
        pub.subscribe(self.empty_content_all, 'empty_all')
        pub.subscribe(self.stop_thread, 'stop_all')

        # 检测是否需要替换文件
        self.trigger_open_replace_window()

    def trigger_open_replace_window(self):
        if not os.path.exists(os.path.abspath(replace_project_dir)):
            os.mkdir(os.path.abspath(replace_project_dir))

        if len(os.listdir(replace_project_dir)) > 0:
            project_name = os.listdir(replace_project_dir)[0]
            if time.time() - os.path.getctime(os.path.join(replace_project_dir, project_name)) < 15*60:
                trigger_menu = self.replace_menu_dic.get(project_name)
                if trigger_menu:
                    # evt = wx.PyCommandEvent(wx.EVT_MENU.typeId, trigger_menu.GetId())
                    evt = wx.MenuEvent(wx.wxEVT_MENU, trigger_menu.GetId(), self.menu2)
                    wx.PostEvent(self, evt)

    # 停止日志滚动
    def toggle_scroll_logout(self, event):
        tailLogFlag = conf.tailLogFlag
        target_id = event.GetId()

        index = (target_id - 1013) // 10
        tailLogFlag[index] = not tailLogFlag[index]
        wx.CallAfter(pub.sendMessage, 'update' + str(index),
                     log_out_index=index, project=self.project, tail_log_flag=tailLogFlag[index])

        event.Skip()

    # 输出日志
    def update_display(self, log_out_index, project, log_out=(), tail_log_flag=True):
        cur_ip = self.StIps[log_out_index]
        tail_opt = self.tail_opts[log_out_index]
        cur_log_out = self.TcLogOuts[log_out_index]
        if tail_log_flag:
            cur_ip.SetLabel(self.cur_label + '  ' + project['ips'][log_out_index])
            if cur_log_out.GetNumberOfLines() > 1000:
                cur_log_out.Remove(1, 800)
            local_log = ''
            for o in log_out:
                local_log += str(o, 'utf-8').replace('\n', '') + '\r\n'
            cur_log_out.AppendText(local_log)
            tail_opt.SetLabel('跟踪中')
        else:
            tail_opt.SetLabel('已暂停')

    # 停止跟踪日志
    def stop_thread(self):
        tailLog.threadFlag = False
        self.set_tail_opt('未启动')
        time.sleep(1)
        self.empty_content_all()
        tailLog.threadFlag = True

    # 启动日志查看
    def run_thread(self, event):
        self.stop_thread()
        is_selected = event.GetId()
        menu = event.GetEventObject()
        self.cur_label = menu.GetLabelText(is_selected)
        label = self.cur_label

        labels = str(label).split('_', 2)

        self.project = projects[labels[0]][labels[1]]
        start_thread(self.project)

    # 清除所有的日志
    def empty_content_all(self):
        for index in range(pow(self.grid_count, 2)):
            self.empty_content(index)
        self.set_tail_opt('未启动')

    # 清除特定的日志
    def empty_content(self, frame_index):
        self.StIps[frame_index].SetLabel('ip' + str(frame_index+1))
        self.TcLogOuts[frame_index].SetLabel('')
        conf.tailLogFlag[frame_index] = True

    # 打开替换tomcat文件的窗口
    def open_replace_window(self, event):
        menu = event.GetEventObject()
        if not menu:
            menu = event.Menu
        self.cur_label = menu.GetLabelText(event.GetId())
        # 到这里啦：接下来需要把当前 按钮的信息 传入到子窗口中，以便判断到底是点了哪个替换
        ReplaceFileFrame(self, event.GetId()).Show()

    def set_tail_opt(self, display=''):
        for tail_opt in self.tail_opts:
            tail_opt.SetLabel(display)

    # 创建日志显示窗体
    def create_grid(self, count):
        id_offset = count * 10

        boxSizer = wx.BoxSizer(wx.VERTICAL)
        boxSizerTitle = wx.BoxSizer(wx.HORIZONTAL)
        ip = wx.StaticText(self, 1001 + id_offset, 'ip' + str(count), wx.DefaultPosition, wx.DefaultSize, 0)
        ip.Wrap(-1)
        self.StIps.append(ip)

        tail_opt = wx.Button(self, 1003 + id_offset, '未启动', wx.DefaultPosition, wx.Size(-1, 25), 0)
        tail_opt.Bind(wx.EVT_LEFT_DOWN, self.toggle_scroll_logout)
        self.tail_opts.append(tail_opt)

        boxSizerTitle.Add(tail_opt, 0, wx.ALL, 2)
        boxSizerTitle.Add(ip, 0, wx.ALL, 5)
        boxSizer.Add(boxSizerTitle, 0, wx.ALL, 0)
        logOut = wx.TextCtrl(self, 1002 + id_offset, wx.EmptyString,
                                   wx.DefaultPosition, wx.Size(2000, 2000),
                                   wx.TE_MULTILINE)
        logOut.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), 70, 90, 90, False, wx.EmptyString))
        boxSizer.Add(logOut, 0, wx.ALL, 5)
        self.TcLogOuts.append(logOut)
        self.mainGridSizer.Add(boxSizer, 1, wx.EXPAND, 5)

    def create_menu(self, menu, name, bind_func, wx_id=wx.ID_ANY):
        sub_menu = wx.MenuItem(menu, wx_id, name, wx.EmptyString, wx.ITEM_NORMAL)
        menu.Append(sub_menu)
        self.Bind(wx.EVT_MENU, bind_func, sub_menu)
        return sub_menu

    def __del__(self):
        pass


if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame(None).Show()
    app.MainLoop()
