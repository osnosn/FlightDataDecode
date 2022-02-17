#!/usr/bin/python3
# -*- coding: utf-8 -*-

import pandas as pd
import Get_param_from_arinc717_aligned as A717

def main():
    global FNAME,WFNAME,DUMPDATA
    global PARAM,PARAMLIST

    print('mem:',sysmem())
    #myQAR=A717.ARINC717(FNAME)
    myQAR=A717.ARINC717('')
    print('mem:',sysmem())
    myQAR.qar_file(FNAME)
    print('mem:',sysmem())

    if PARAMLIST:
        #-----------列出记录中的所有参数名称--------------
        regularlist,superlist=myQAR.paramlist()
        #---regular parameter
        ii=0
        for vv in regularlist:
            print(vv, end=',\t')
            if ii % 10 ==0:
                print()
            ii+=1
        print()
        print('--------------------------------------------')
        #---superframe parameter
        ii=0
        for vv in superlist:
            print(vv, end=',\t')
            if ii % 10 ==0:
                print()
            ii+=1
        print()
        print('mem:',sysmem())

        #-----------参数写入csv文件--------------------
        if WFNAME is not None and len(WFNAME)>0:
            print('Write into file "%s".' % WFNAME)
            df_pm=pd.concat([pd.DataFrame(regularlist),pd.DataFrame(superlist)])
            df_pm.to_csv(WFNAME,sep='\t',index=False)
            return
        return

    if PARAM is None:
        #-----------打印参数的配置内容-----------------
        for vv in ('ALT_STD','AC_TAIL7'):
            fra=myQAR.getFRA(vv)
            if len(fra)<1:
                print('Empty dataVer.')
                continue
            print('parameter:',vv)
            print('Word/SEC:{0[0]}, synchro len:{0[1]} bit, sync1:{0[2]}, sync2:{0[3]}s, sync3:{0[4]}, sync4:{0[5]}, '.format(fra['1']))
            print('   superframe counter:subframe:{0[6]:<5}, word:{0[7]:<5}, bitOut:{0[8]:<5}, bitLen:{0[9]:<5}, value in 1st frame:{0[10]:<5}, '.format(fra['1']) )
            for vv in fra['2']:
                print('Part:{0[0]:<5}, recordRate:{0[1]:<5}, subframe:{0[2]:<5}, word:{0[3]:<5}, bitOut:{0[4]:<5}, bitLen:{0[5]:<5}, bitIn:{0[6]:<5}, type:{0[7]:<5}, '.format(vv) )
            print()
        print('DataVer:',myQAR.dataVer())
    else:
        #-----------获取一个参数--------------------
        pm_list=myQAR.get_param(PARAM)
        #print(pm_list)
        if len(pm_list)<1:
            PARAM=PARAM.upper()
            print('参数 "%s" 没找到, 或者获取失败.'% PARAM)
            print(pm_list)
            print('DataVer:',myQAR.dataVer())
            return
        print('Result[0]:',pm_list[0]) #打印第一组值
        print('DataVer:',myQAR.dataVer())

        df_pm=pd.DataFrame(pm_list)

        #-----------参数写入csv文件--------------------
        if WFNAME is not None and len(WFNAME)>0:
            print('Write into file "%s".' % WFNAME)
            #df_pm.to_csv(WFNAME,index=False)
            df_pm.to_csv(WFNAME,sep='\t',index=False)
            return

        #-----------显示参数的部分内容--------------------
        pd.set_option('display.min_row',200)
        if len(pm_list)>1200:
            print( df_pm['v'][1000:1200].tolist() )
        else:
            print( df_pm['v'][10:90].tolist() )

    print('mem:',sysmem())
    myQAR.close()
    print('closed.')
    print('mem:',sysmem())
    return

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
    print(u' 读取 wgl中 raw.dat,根据参数编码规则,解码一个参数。')

    print(sys.argv[0]+' [-h|--help]')
    print('   * (必要参数)')
    print('   -h, --help                 print usage.')
    print(' * -f, --file xxx.wgl.zip     "....wgl.zip" filename')
    print(' * -p, --param alt_std        show "ALT_STD" param. 自动全部大写。')
    print('   --paramlist                list all param name.')
    print('   -w xxx.csv            参数写入文件"xxx.csv"')
    print('   -w xxx.csv.gz         参数写入文件"xxx.csv.gz"')
    print(u'\n               author:南方航空,LLGZ@csair.com')
    print(u' 认为此项目对您有帮助，请发封邮件给我，让我高兴一下.')
    print(u' If you think this project is helpful to you, please send me an email to make me happy.')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hw:df:p:',['help','file=','paramlist','param=',])
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
        elif op in('--paramlist',):
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

