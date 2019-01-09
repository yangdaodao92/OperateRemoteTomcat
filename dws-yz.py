print(11)

# import classes.ReplaceFileFrame as ReplaceFileFrame
# import os
# import glob
# import sys
#
# replace_project_dir = ReplaceFileFrame.replace_project_dir
# project = ReplaceFileFrame.projects['prod']['dws-yz']
# # project = ReplaceFileFrame.projects['recycle']['api']
# replace_dic = {}
#
#
# # 加载要替换的文件
# def load_replace_file():
#     for filename in glob.glob(replace_project_dir + '\\**\\*', recursive=True):
#         if os.path.isfile(filename) and filename.find(project['project_name'] + '\\') != -1:
#             rel_remote_location = filename.split(project['project_name'])[1].replace('\\', '/')
#             replace_dic[filename] = project['app_location'] + rel_remote_location
#
#
# # 全部替换并同时重启
# def replaceAndRestartBtnInTime():
#     for i, ip in enumerate(project['ips']):
#         target_ips = [''] * len(project['ips'])
#         target_ips[i] = ip
#         ReplaceFileFrame.TestThread(replace_dic, project, target_ips)
#
#
# # 仅替换
# def replaceBtn():
#     ReplaceFileFrame.TestThread(replace_dic, project, need_close=False, need_start=False)
#
#
# # 仅重启
# def restartBtn():
#     ReplaceFileFrame.TestThread({}, project, need_replace=False)
#
#
# if __name__ == '__main__':
#     # app = wx.App()
#
#     load_replace_file()
#     argv = sys.argv
#     print(argv)
#     # if len(argv) > 1:
#     #     if argv[1] == 'replace_and_restart':
#     #         replaceAndRestartBtnInTime()
#     #     if argv[1] == 'replace':
#     #         replaceBtn()
#     #     if argv[1] == 'restart':
#     #         restartBtn()
