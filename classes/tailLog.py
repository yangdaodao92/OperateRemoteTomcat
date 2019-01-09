import paramiko
import select
import re
import sys
import io
import wx
from wx.lib.pubsub import pub
import pysftp
import time
import conf

threadFlag = False
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def connect_tomcat(log_out_index, ip, project):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(ip, username=project['username'], password=project['password'])
    tail_log(client, project, log_out_index)


def tail_log(client, project, log_out_index):
    transport = client.get_transport()
    channel = transport.open_session()
    remote_command = 'tail -f ' + project['tomcat_location'] + '/logs/catalina.out'
    channel.exec_command(remote_command)

    BUF_SIZE = 1024
    LeftOver = b''
    while transport.is_active() and threadFlag:
        try:
            rl, wl, xl = select.select([channel], [], [], 0.0)
            if len(rl) > 0:
                buf = channel.recv(BUF_SIZE)
                if len(buf) > 0:
                    lines_to_process = LeftOver + buf
                    EOL = lines_to_process.rfind(b'\n')
                    if EOL != len(lines_to_process) - 1:
                        LeftOver = lines_to_process[EOL + 2:]
                        lines_to_process = lines_to_process[:EOL + 1]
                    else:
                        LeftOver = b''
                    if lines_to_process.rfind(b'\n') == len(lines_to_process) - 1:
                        new_out = [i for i in lines_to_process.splitlines() if len(i) < project['logs_line_length']]
                        if len(new_out) > 0:
                            if conf.tailLogFlag[log_out_index]:
                                wx.CallAfter(pub.sendMessage, 'update' + str(log_out_index), log_out_index=log_out_index,
                                             project=project, log_out=new_out)
                            else:
                                wx.CallAfter(pub.sendMessage, 'update' + str(log_out_index),
                                             log_out_index=log_out_index, project=project, tail_log_flag=False)
                            # for line in lines_to_process.splitlines():
                                # print(str(line, 'utf-8'))

        except (KeyboardInterrupt, SystemExit):
            print('got ctrl+c')
            break

    if not threadFlag:
        client.close()


# # 监控tomcat输出日志
# def tail_log(sftp, log_out_index, ip, project, outs):
#     out = sftp.execute('tail -n ' + str(project['logs_tail_size']) + ' ' + project['tomcat_location'] + '/logs/catalina.out')
#     if tailLogFlag[log_out_index]:
#         new_out = [i for i in out if i not in outs and len(i) < project['logs_line_length']]
#         wx.CallAfter(pub.sendMessage, 'update' + str(log_out_index), log_out_index=log_out_index, project=project, log_out=new_out)
#     else:
#         wx.CallAfter(pub.sendMessage, 'update' + str(log_out_index), log_out_index=log_out_index, project=project, tail_log_flag=False)
#     time.sleep(1)
#     if threadFlag:
#         tail_log(sftp, log_out_index, ip, project, out)
#
#
# cnopts = pysftp.CnOpts()
# cnopts.hostkeys = None
#
#
# def connect_tomcat(log_out_index, ip, project):
#     with pysftp.Connection(ip, username=project['username'], password=project['password'], cnopts=cnopts) as sftp:
#         print(ip)
#         tail_log(sftp, log_out_index, ip, project, [])