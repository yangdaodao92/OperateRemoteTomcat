import pysftp
import pprint
import re
import time

# 监控tomcat输出日志，判断是否重启成功
def tailLog(sftp, outs):
    out = sftp.execute('tail -n 20 /opt/tomcats/apache-tomcat-member-center-api/logs/catalina.out')
    newOut = [i for i in out if i not in outs]
    restart = False
    for o in newOut:
        print(o)
        line = str(o, 'utf-8').replace('\n', '')
        print(line)
        if re.search('Server startup in [\d|,]+ ms\Z', line) is not None:
            restart = True
            print('------------- Tomcat 重新启动成功 --------------')
    if not restart:
        time.sleep(1)
        tailLog(sftp, out)

# 杀死当前进程，并重启tomcat
# 注意可能会有多个tomcat进程
def fun2():
    with pysftp.Connection('192.168.133.177', username='root', password='123qwe!@#') as sftp:
        with sftp.cd('/opt/tomcats/apache-tomcat-bid-data-interface'):
            grep = sftp.execute('ps -ef | grep "tomcat-member-center-api"')
            for g in grep:
                gStr = str(g, 'utf-8')
                if re.search('apache-tomcat-member-center-api', gStr) is not None:
                    pid = re.split('\s+', gStr)[1]
                    sftp.execute('kill -9 ' + pid)
            sftp.execute(sftp.getcwd() + '/bin/catalina.sh start')
            time.sleep(3)
            tailLog(sftp, [])


# 测试删除所有文件
def fun1():
    with pysftp.Connection('192.168.133.177', username='root', password='123qwe!@#') as sftp:
        with sftp.cd('/opt/tomcats/apache-tomcat-bid-data-interface'):
            sftp.execute('rm -rf ' + sftp.getcwd() + '/webapps/ROOT/*')


if __name__ == '__main__':
    fun1()

