#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
读解码库， 787xx 的 ARINC 767 记录格式，则读 xxx.frd 文件,
   ARINC-647A-1 的xml配置文件找不到。所以可能无法解码。
      author:南方航空,LLGZ@csair.com
"""
import sys
import os
import psutil   #非必须库
#from datetime import datetime
#pandas 可以不使用, read_parameter_file() 可以返回list, 不返回DataFrame。
import pandas as pd
import zipfile
from io import StringIO
import config_vec as conf

def main():
    global FNAME,DUMPDATA
    global TOCSV
    global PARAMLIST
    global PARAM
    print('begin mem:',sysmem())
    FRA=read_parameter_file(FNAME)
    if FRA is None:
        return

    pd.set_option('display.max_columns',18)
    pd.set_option('display.width',156)
    pd.set_option('display.min_row',33)
    pd.set_option('display.min_row',330)
    #print(FRA)
    #print(FRA.keys())

    if PARAMLIST:
        #----------显示所有参数名-------------
        ii=0
        #print(FRA['4'].iloc[:,1].tolist())
        for vv in FRA['4'].iloc[:,1].tolist():
            print(vv, end=',\t')
            if ii % 9 ==0:
                print()
            ii+=1
        if len(TOCSV)>4:
            print('Write to CSV file:',TOCSV)
            FRA['4'].iloc[:,1].to_csv(TOCSV,sep='\t')
        return

    if PARAM is not None and len(PARAM)>0:  #显示单个参数名
        #----------显示单个参数的配置内容-------------
        print_fra(FRA, '1', [  #这个也显示一下
            'ARINC Version',
            'File Revision',
            'File Date',
            'File Comment',
            'Source Doc',
            'File Name']
            )

        param=PARAM.upper()
        tmp=FRA['4']
        tmp2=tmp[ tmp.iloc[:,1]==param ].copy() #dataframe
        pm_tb4=tmp.iloc[[0,]].append( tmp2,  ignore_index=False )
        if len(tmp2)<1:
            print(pm_tb4)
            print()
            print('Parameter %s not found.'%param)
            print()
            return
        pm_longName=tmp2.iat[0,0]

        tmp=FRA['3']
        tmp2=tmp[ tmp.iloc[:,2]==pm_longName ].copy() #dataframe
        pm_tb3=tmp.iloc[[0,]].append( tmp2,  ignore_index=False )
        frameID=tmp2.iat[0,0]
        frameOrder=tmp2.iat[0,1]

        tmp=FRA['2']
        tmp2=tmp[ tmp.iloc[:,0]==frameID ].copy() #dataframe
        pm_tb2=tmp.iloc[[0,]].append( tmp2,  ignore_index=False )

        print(pm_tb2)
        print()
        print(pm_tb3)
        print()
        print(pm_tb4)
        print()
        return

    print_fra(FRA, '1', [
            'ARINC Version',
            'File Revision',
            'File Date',
            'File Comment',
            'Source Doc',
            'File Name']
            )

    print_fra(FRA, '2', [
        'Frame Id', 'Frame Name', 'Frame rate', 'Frame rate', 'Parameter Nr for this frame id', 'Recording Phase']
            )

    print_fra(FRA, '3', ['Frame Id', 'Parameter order', 'Parameter Long Name', 'Parameter Mnemonic']
            )

    print_fra(FRA, '4', ['Parameter Long Name', 'Parameter Name'] )
    #print(FRA['3'].loc[:,1].dropna().tolist() ) #列出所有的 ParamOrder
    #show=FRA['3'].loc[1:,1].unique().astype(int)  #列出所有的 ParamOrder
    #show.sort()
    #print(FRA['3'].loc[:,1].unique() ) #列出所有的 Coef A,都是None
    show=FRA['3']
    #show=show[show.iloc[:,0]=='3']  #列出所有的 ParamID=3 的 ParamOrder
    #show=show[show.iloc[:,0]=='5']  #列出所有的 ParamID=5 的 ParamOrder

    show=show[show.iloc[:,0]=='11']  #列出所有的 ParamID=11 的 ParamOrder
    show=show.loc[:,1].astype(int).sort_values()
    #print(show.tolist())

    #-----打印frame id 的参数个数
    show=FRA['3']
    ids=(0,1,2,3,4,5,6,7,8,9,0xA,0xB,0xC)
    print(' id', 'param num',sep='\t')
    for vv in ids:
        vv=str(vv)
        tmp=show[show.iloc[:,0]==vv]
        print(' %X'%int(vv), len(tmp.index),sep='\t')


    memsize=0
    for kk in FRA:
        memsize+=getsizeof(FRA[kk],False)
    print('FRA(%d):'%len(FRA),showsize(memsize))

    print('end mem:',sysmem())
    if len(TOCSV)>4:
        #FRA.to_csv(TOCSV)
        print('==>ERR,  There has 4 tables. Can not save to 1 CSV.')

def print_fra(FRA, frakey,colname):
    if frakey not in FRA:
        print('ERR, %s not in list' % frakey)
        return
    tmp=pd.concat([FRA[frakey][0:1],FRA[frakey]])
    #print(tmp.iloc[0].values.tolist())

    print(frakey, end=')')
    for vv in tmp.iloc[0].values:
        print(vv, end='||')
    print()

    tmp.iloc[1]=colname
    print(tmp[1:])
    print('----------------')

def read_parameter_file(dataver):
    if isinstance(dataver,(str,float)):
        dataver=int(dataver)
    if not str(dataver).startswith('787'):
        print('ERR,dataver %s not support.' % (dataver,) )
        print('Use "read_fra.py instead.')
        return None
    dataver='%06d' % dataver  #6位字符串

    filename_zip=dataver+'.frd'     #.vec压缩包内的文件名
    zip_fname=os.path.join(conf.vec,dataver+'.vec')  #.vec文件名

    if os.path.isfile(zip_fname)==False:
        print('ERR,ZipFileNotFound',zip_fname,flush=True)
        raise(Exception('ERR,ZipFileNotFound,%s'%(zip_fname)))

    try:
        fzip=zipfile.ZipFile(zip_fname,'r') #打开zip文件
    except zipfile.BadZipFile as e:
        print('ERR,FailOpenZipFile',e,zip_fname,flush=True)
        raise(Exception('ERR,FailOpenZipFile,%s'%(zip_fname)))
    
    FRA={}
    with StringIO(fzip.read(filename_zip).decode('utf16')) as fp:
    #with open(vec_fname,'r',encoding='utf16') as fp:
        for line in fp.readlines():
            line_tr=line.strip('\r\n //')
            tmp1=line_tr.split('|',1)
            #if line.startswith('//') and tmp1[0] == '7':     # "7|..." 的标题比较特殊，起始多了一个tab
            #    tmp1[1]=tmp1[0].lstrip()
            tmp2=tmp1[1].split('\t')
            if tmp1[0] in FRA:
                if FRA[ tmp1[0]+'_len' ] != len(tmp2):
                    print('ERR,data(%s) length require %d, but %d.' % (tmp1[0], FRA[ tmp1[0]+'_len' ], len(tmp2)) )
                    #raise(Exception('ERR,DataLengthNotSame,data(%s) require %d but %d.'% (tmp1[0], FRA[ tmp1[0]+'_len' ], len(tmp2)) ))
                FRA[ tmp1[0] ].append( tmp2 )
            else:
                FRA[ tmp1[0] ]=[ tmp2, ]
                FRA[ tmp1[0]+'_len' ]=len(tmp2)


    fzip.close()

    df_FRA={}
    for kk in FRA:
        if kk.endswith('_len'):
            continue
        df_FRA[kk]=pd.DataFrame(FRA[kk])
    return df_FRA     #返回dataframe
    #return FRA       #返回list

def showsize(size):
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
def getsizeof(buf,mode=True):
    size=sys.getsizeof(buf)
    if mode:
        return showsize(size)
    else:
        return size
def sysmem():
    size=psutil.Process(os.getpid()).memory_info().rss #实际使用的物理内存，包含共享内存
    #size=psutil.Process(os.getpid()).memory_full_info().uss #实际使用的物理内存，不包含共享内存
    return showsize(size)



import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'   命令行工具。')
    print(u' 读解码库，787xx 的frad库,参数配置文件 vec 中 xx.frd 文件。比如 078XXX.fra')
    print(u'      ARINC-647A-1 的xml配置文件找不到。所以可能无法解码。')
    print(sys.argv[0]+' [-h|--help]')
    print('   -h, --help         print usage.')
    print('   -v, --ver=78727      dataver 中的参数配置表')
    print('   --csv xxx.csv        save to "xxx.csv" file.')
    print('   --csv xxx.csv.gz     save to "xxx.csv.gz" file.')
    print('   --paramlist          list all param name.')
    print('   -p,--param alt_std   show "alt_std" param.')
    print(u'\n               author:南方航空,LLGZ@csair.com')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hvp:f:',['help','ver=','csv=','paramlist','param='])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    DUMPDATA=False
    TOCSV=''
    PARAMLIST=False
    PARAM=None
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-v','--ver'):
            FNAME=value
        elif op in('-d',):
            DUMPDATA=True
        elif op in('--csv',):
            TOCSV=value
        elif op in('--paramlist',):
            PARAMLIST=True
        elif op in('--param','-p',):
            PARAM=value
    if len(args)>0:  #命令行剩余参数
        FNAME=args[0]  #只取第一个
    if FNAME is None:
        usage()
        exit()

    main()
    print('mem:',sysmem())

