#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
  解码所有参数，写入csv文件。压缩或者不压缩。建议写入一个目录。
    我的测试 Intel CPU i9,x64,主频3.3GHz, BogoMIPS:6600。
    原始文件 raw 20MB，压缩包为5.5MB。有参数 2600 个, 航段170分钟。
        解所有参数，写入单文件,zip文件LZMA压缩,    22MB，耗时3m58s. 最大内存占用227MB.
        解所有参数，写入单文件,zip文件deflated压缩,85MB，耗时2m25s.
        解所有参数，写入单文件,zip文件bzip2压缩,   48MB，耗时2m34s.
        解所有参数，写入目录,  gz文件              92MB，耗时2m58s.
        解所有参数，写入目录,  csv文件不压缩,     397MB，耗时2m18s.
        sysmem()显示，内存占用不超过 230MB.
    author: osnosn@126.com OR LLGZ@csair.com
"""
import pandas as pd
import zipfile
import Get_param_from_arinc717_aligned as A717

def main():
    global FNAME,WFNAME
    global ALLPARAM

    print('mem:',sysmem())
    myQAR=A717.ARINC717('')
    print('mem:',sysmem())
    myQAR.qar_file(FNAME)
    print('mem:',sysmem())

    if ALLPARAM:
        #分离写入路径，为了在文件名总插入"参数名称"
        wpath=''    #目录
        wbase=''    #文件名
        suffix=''   #后缀
        myzip=None
        if WFNAME is not None and len(WFNAME)>0:
            wpath=os.path.dirname(WFNAME)
            wbase=os.path.basename(WFNAME)
            dot=wbase.find('.')  #文件名中的第一个点,全部作为后缀
            if dot>0:
                suffix=wbase[dot:]  #文件名后缀
                wbase=wbase[:dot]
            else:
                suffix=''
            if suffix.endswith('.zip'):
                myzip=zipfile.ZipFile(WFNAME,'w',compression=zipfile.ZIP_LZMA)
                #myzip=zipfile.ZipFile(WFNAME,'w',compression=zipfile.ZIP_DEFLATED)
                #myzip=zipfile.ZipFile(WFNAME,'w',compression=zipfile.ZIP_BZIP2)
        #-----------列出记录中的所有参数名称--------------
        regularlist,superlist=myQAR.paramlist()
        total_pm=0
        #---regular parameter
        ii=0
        for vv in regularlist:
            print(vv,flush=True)
            ii +=1
            if ii==1: continue  #第一个不是参数
            pm_list=myQAR.get_param(vv)
            df_pm=pd.DataFrame(pm_list)
            pm_name="{}.{}".format(ii,vv)
            write_csv(myzip,wpath,wbase,suffix,pm_name,df_pm)
        print("ragular:{}".format(ii))
        total_pm += ii-1
        print()
        print('--------------------------------------------')
        #---superframe parameter
        ii=0
        for vv in superlist:
            print(vv,flush=True)
            ii +=1
            if ii==1: continue  #第一个不是参数
            pm_list=myQAR.get_param(vv)
            df_pm=pd.DataFrame(pm_list)
            pm_name="{}.{}".format(ii,vv)
            write_csv(myzip,wpath,wbase,suffix,pm_name,df_pm)
        print("super:{}".format(ii))
        total_pm += ii-1
        print()
        print("total_param:{}".format(total_pm))
        print('mem:',sysmem())
        if myzip is not None:
            myzip.close()

    print('mem:',sysmem())
    myQAR.close()
    print('closed.')
    print('mem:',sysmem())
    return

def write_csv(myzip,wpath,wbase,suffix,pm_name, df_pm):
    #-----------参数写入csv文件--------------------
    if len(wbase)>0:
        if myzip is None:
            wfile="{}_{}{}".format(wbase,pm_name,suffix)
            wpath_file=os.path.join(wpath,wfile)
            print('Write into file "{}".'.format(wpath_file))
            df_pm.to_csv(wpath_file,sep='\t',index=False)
            return
        else:
            myzip.writestr(pm_name,df_pm.to_csv(None,sep='\t',index=False))
            #print('mem:',sysmem())
            return
    else:
        if len(df_pm)>0:
            print(df_pm['v'][0:10].tolist())
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
    print(' * -a, --allparam            解码所有的参数。')
    print('   -w out/xxx.csv            参数不压缩写入多个文件"out/xxx_参数名.csv"')
    print('   -w out/xxx.csv.gz         参数压缩写入多个文件"out/xxx_参数名.csv.gz"')
    print('   -w out/xxx.zip            参数压缩写入单文件"out/xxx.zip"')
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
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hw:af:',['help','file=','allparam',])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    WFNAME=None
    ALLPARAM=False
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-f','--file'):
            FNAME=value
        elif op in('-w',):
            WFNAME=value
        elif op in('-a','--allparam',):
            ALLPARAM=True
    if len(args)>0:  #命令行剩余参数
        FNAME=args[0]  #只取第一个
    if FNAME is None:
        usage()
        exit()
    if os.path.isfile(FNAME)==False:
        print(FNAME,'Not a file')
        exit()

    main()

