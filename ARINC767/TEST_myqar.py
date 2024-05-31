#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''
      author: osnosn@126.com
'''
#import pandas as pd
import Get_param_from_arinc767 as A767

def main():
    global FNAME,WFNAME,DUMPDATA,PARAM

    print('mem0:',sysmem())
    #myQAR=A767.ARINC767(FNAME)
    myQAR=A767.ARINC767('')
    myQAR.qar_file(FNAME)
    print('mem0:',sysmem())

    reg=myQAR.getREG()
    dataver=myQAR.dataVer()

    print('Registration:',reg,', DataVer:',dataver)
    print()

    if PARAMLIST:
        pmlist=myQAR.paramlist()
        #print(pmlist)
        for frame_id in pmlist:
            print('--- %s: %s ----'%(frame_id, pmlist[frame_id]['info']) )
            jj=0
            for pm in pmlist[frame_id]['pm']:
                jj+=1
                print(pm, end=',\t')
                if jj %6 == 0:
                    print()
            if jj %6 != 0:
                    print('\n')

        print('mem:',sysmem())
        return

    if PARAM is None:
        myQAR.data_file_info(DUMPDATA)
    else:
        #-----------获取一个参数--------------------
        param_val=myQAR.get_param(PARAM)
        #print(param_val)

        #------打印各个param_val 前20个值 ----
        print('------ DumpData(first 20)-----')
        if len(param_val)>20:
            for ii in range(20):
                print('{:>8}, {}'.format(param_val[ii]['time'],param_val[ii]['val'],) )
        else:
            for ii in range(len(param_val)):
                print('{:>8}, {} '.format(param_val[ii]['time'],param_val[ii]['val'],) )
        #-----------参数写入csv文件--------------------
        if WFNAME is not None and len(WFNAME)>0:
            if len(param_val)<1:
                print('Empty value, skip write CSV file.')
            else:
                print('Write to CSV file:',WFNAME)
                if WFNAME.endswith('.gz'):
                    fp=gzip.open(WFNAME,'wt',encoding='utf8')
                else:
                    fp=open(WFNAME,'w',encoding='utf8')
                ii=0
                fp.write(str(ii)+'\ttime\tvalue\n')
                for row in param_val:
                    fp.write('{}\t{}\t{}\n'.format(ii,row['time'],row['val']) )
                    ii+=1
                fp.close()

    print('mem:',sysmem())

def showsize(size):
    '''
    显示，为了 human readable
    '''
    if size<1024.0*2:
        return '%.0f B'%(size)
    size /=1024.0
    if size<1024.0*2:
        return '%.2f K'%(size)
    size /=1024.0
    if size<1024.0*2:
        return '%.2f M'%(size)
    size /=1024.0
    if size<1024.0*2:
        return '%.2f G'%(size)
import psutil         #非必需库
def sysmem():
    '''
    获取本python程序占用的内存大小
    '''
    size=psutil.Process(os.getpid()).memory_info().rss #实际使用的物理内存，包含共享内存
    #size=psutil.Process(os.getpid()).memory_full_info().uss #实际使用的物理内存，不包含共享内存
    return showsize(size)


import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'   命令行工具。')
    print(u' 读取,来源于PC卡的原始数据文件。尝试解码一个参数。')
    print(sys.argv[0]+' [-h|--help]')
    print('   -h, --help                print usage.')
    print('   -f, --file="....wgl.zip"     filename')
    print('   -p, --param ALT_STD       show "ALT_STD" param. 大小写敏感。')
    print('   -l, --paramlist           list all param name.')
    print('   -w xxx.csv                参数写入文件"xxx.csv"')
    print('   -w xxx.csv.gz             参数写入文件"xxx.csv.gz"')
    print(u'\n               author: osnosn@126.com')
    print(u' 认为此项目对您有帮助，请发封邮件给我，让我高兴一下.')
    print(u' If you think this project is helpful to you, please send me an email to make me happy.')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hw:df:p:l',['help','file=','paramlist','param=',])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    WFNAME=None
    DUMPDATA=False
    PARAMLIST=False
    PARAM=None
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-f','--file'):
            FNAME=value
        elif op in('-w',):
            WFNAME=value
        elif op in('-d',):
            DUMPDATA=True
        elif op in('-l','--paramlist',):
            PARAMLIST=True
        elif op in('-p','--param',):
            PARAM=value
    if len(args)>0:  #命令行剩余参数
        FNAME=args[0]  #只取第一个
    if FNAME is None:
        usage()
        exit()
    if os.path.isfile(FNAME)==False:
        print(FNAME,'Not a file')
        exit()

    main()

