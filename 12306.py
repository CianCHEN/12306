#!/usr/bin/env python
#coding:utf-8
"""Train tickets query from CLI.

Usage:
    tickets [-dcgktz] <from> <to> <date>

Options:
    -h --help     Show this screen.
    -d            动车
    -c            城际列车
    -g            高铁
    -k            快速
    -t            特快
    -z            直达
"""
import requests
import stations
import sys,time
from datetime import datetime,timedelta
from requests.packages.urllib3.exceptions import InsecureRequestWarning
#need to install
from prettytable import PrettyTable
from docopt import docopt
from colorama import Fore


#忽略requests 的告警
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = '次序 车次 出发车站/到达车站 出发时间/到达时间 历时 一等座 二等座 软卧 硬卧 软座 硬座 无座 状态'.split()

data_list=[]
def trains(last):
    '''
    格式化12306 URL 的原始数据，加入need_print和parse_train_data取出最终数据，yield返回一个生成器(供最后打印表格使用)
    '''
    global flag
    flag = 0
    for j in last:
        flag+=1
        data_list=j.split("|")
        #print data_list
        #yield parse_train_data(data_list).values()
        if need_print(data_list):
            yield parse_train_data(data_list)
		
def colored(color,string):
    '''
    颜色输出函数，默认是红色
    '''
    return ''.join([getattr(Fore,color.upper(),Fore.RED),string,Fore.RESET])
		

def parse_train_data(data_list):
    '''
    格式化从12306 url 取出的数据，通过排序取出
    '''
    d1 = {
            '0_flag': flag,
            'a_station_nu': colored("yellow",data_list[3]),
            'b_train_from_to': '/'.join([colored("green",stations.get_name(data_list[6])),colored("ss",stations.get_name(data_list[7]))]),
            'c_train_start_end': '/'.join([data_list[8],data_list[9]]),
            'd_use_time': data_list[10],
            'e_yd': data_list[31] or '--',
            'f_ed': data_list[30] or '--',
            'g_rw': data_list[23] or '--',
            'h_yw': data_list[28] or '--',
            'i_rz': data_list[24] or '--',
            'j_yz': data_list[29] or '--',
            'k_wz': data_list[26] or '--',
            'l_status': colored("green",data_list[1]) or '--'
        }
    if data_list[1] == u'\u5217\u8f66\u505c\u8fd0':
        d1['l_status'] = colored("ss",data_list[1])
    items = d1.items()
    #返回list 元素是tunple
    items.sort()
    return [value for key,value in items]

def pretty_table():
    '''
    生成最后的表格输出 
    '''
    pt = PrettyTable()
    pt._set_field_names(headers)
    try :
        for i in trains(last):
            pt.add_row(i)
        print pt
    #except NameError as e :
        #print e
    except Exception as e :
        print e
        #print colored("red","Something Error Occurred! Please check your Code... exit...")
        exit(120)      

def need_print(data_list):
    '''
    定义需要打印的列车信息，取出-g-c-k-d-z等，过滤列车信息
    '''
    station_train_code = data_list[3]
    initial = station_train_code[0].lower()
    return (not options or initial in options)

def _get_leave_time(ltime):
    """
    获取出发时间，这个函数的作用是为了：时间可以输入两种格式：2018-08-25、20180825
    """
    leave_time = ltime 
    if len(leave_time) == 8:
        return '{0}-{1}-{2}'.format(leave_time[:4],leave_time[4:6],leave_time[6:])

    if '-' in leave_time:
        return leave_time

def get_lasttime():
    '''
    29天之后的日期，12306的购票为30天
    '''
    #当天时间
    now = datetime.today()
    #当前日期 日 
    nowday = now.strftime('%d')
    day = 29
    #ag = int(nowday)+int(day)
    #15天之后的日期'月份-日'转换，涉及单位进制
    delta = timedelta(days=day)
    #15天之后
    daylast = (now + delta).strftime('%Y-%m-%d')
    return daylast

def check_arguments_validity():
    '''
    判断输入的参数是否正确，加入判断当前时间是否在23-7点，跳过12306维护时间
    '''
    from_station = stations.get_telecode(arguments['<from>'])
    to_station = stations.get_telecode(arguments['<to>'])
    tt=time.strftime('%H:%M:%S',time.localtime())
    if from_station is None or to_station is None:
        print colored("ss",'请输入有效的车站名称')
        exit()
    try:
        #if datetime.strptime(self.date, '%Y-%m-%d') < datetime.now():
        if datetime.today().strftime('%Y-%m-%d') > _get_leave_time(arguments['<date>']) or _get_leave_time(arguments['<date>'])  > get_lasttime():
            raise ValueError
    except:
        print colored("s",'请输入有效日期')
        exit()
    try:
        if '07:00:00' > tt or tt > '23:00:00':
            raise ValueError
    except:
        print colored("s",'12306 正在维护哦，不能买票了_ ^ ^ _')

if __name__ == '__main__':
    arguments = docopt(__doc__, version='Tickets 1.0')
    options = ''.join([key for key, value in arguments.items() if value is True])
    check_arguments_validity()
    url='https://kyfw.12306.cn/otn/leftTicket/queryX?leftTicketDTO.train_date={0}&leftTicketDTO.from_station={1}&leftTicketDTO.to_station={2}&purpose_codes=ADULT'.format(
             _get_leave_time(arguments['<date>']),stations.get_telecode(arguments['<from>']),stations.get_telecode(arguments['<to>']))
    #print url
    #requests.packages.urllib3.disable_warnings() 
    header = { 
            "Accept":"text/html,application/json,application/xml;",
            "Accept-Encoding":"gzip",
            "Accept-Language":"zh-CN",
            "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
            }
            #"User-Agent":"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)",

    r=requests.get(url,verify=False,headers=header)
    arguments.items()
    print r.text
    last=r.json()['data']['result']
    pretty_table()
#    try:
#        #if datetime.today().strftime('%Y-%m-%d') <= _get_leave_time(arguments['<date>']) <= get_lasttime():
#        if datetime.today().strftime('%Y-%m-%d') > _get_leave_time(arguments['<date>']) or _get_leave_time(arguments['<date>'])  > get_lasttime():
#            raise ValueError
#    except:
#        print colored("red","请检查输入的日期是否正确")
#        exit(100)
#    else:
#        last=r.json()['data']['result']
#        pretty_table()
