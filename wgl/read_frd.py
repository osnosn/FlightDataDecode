#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
读解码库，参数配置文件 vec 中 xx.fra 文件。比如 010412.fra
   787xx 的frad 库，则读 xxx.frd 文件,
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

    frad=False
    if str(int(FNAME)).startswith('787'):
        frad=True

    pd.set_option('display.max_columns',18)
    pd.set_option('display.width',156)
    pd.set_option('display.min_row',33)
    pd.set_option('display.min_row',330)
    #print(FRA)
    print(FRA.keys())

    if PARAM is not None and len(PARAM)>0:  #显示单个参数名
        if frad:
            print('Not supported.')
        else:
            param=PARAM.upper()
            tmp=FRA['2']
            tmp2=tmp[ tmp.iloc[:,0]==param ].copy() #dataframe
            tmp=tmp.iloc[[0,]].append( tmp2,  ignore_index=False )
            print(tmp)
        return

    if frad:
        print_fra(FRA, '1', [
            'ARINC Version',
            'File Revision',
            'File Date',
            'File Comment',
            'Source Doc',
            'File Name']
            )
    else:
        print_fra(FRA, '1', [
            'Frame Type(C/S)',
            'Word/Sec',
            'Synchro Word Length',
            'Synchro1',
            'Synchro2',
            'Synchro3',
            'Synchro4',
            '1(Subframe)',
            '1(Word)',
            '1(Bit Out)',
            '1(Data Bits)',
            'Value in 1st Frame (0/1)',
            'S/F End Synchro',
            '2(Subframe)',
            '2(Word)',
            '2(Bit Out)',
            '2(Data Bits)',
            'Value in 1st Frame for Frame Counter 2(0/1)',
            ]
            )

    if frad:
        print_fra(FRA, '2', [
        'Frame Id', 'Frame Name', 'Frame rate', 'Frame rate', 'Parameter Nr for this frame id', 'Recording Phase']
            )
    else:
        print_fra(FRA, '2', [
            'Regular Parameter Name',
            'Part (1,2 or 3)',
            'RecordRate',
            '(Subframe)',
            '(Word)',
            '(Bit Out)',
            '(Data Bits)',
            '(Bit In)',
            '(Imposed or Computed)',
            'Recorded Range Min',
            'Recorded Range Max',
            'Recorded Resolution',
            'Occurence No']
            )

    if frad:
        print_fra(FRA, '3', ['Frame Id', 'Parameter order', 'Parameter Long Name', 'Parameter Mnemonic']
            )
    else:
        print_fra(FRA, '3', [
            'Superframe No',
            '(Subframe)',
            '(Word)',
            '(Bit Out)',
            '(Data Bits)',
            '',]
            )

    if frad:
        print_fra(FRA, '4', ['Parameter Long Name', 'Parameter Name'] )
    else:
        print_fra(FRA, '4', [
            'Superframe Parameter Name',
            'Part (1,2 or 3)',
            'Period Of',
            'Superframe No',
            'Frame',
            '(Bit Out)',
            '(Data Bits)',
            '(Bit In)',
            'Range Min',
            'Range Max',
            'Resolution']
            )

    if PARAMLIST:
        ii=0
        if frad:
            #print(FRA['4'].iloc[:,1].tolist())
            for vv in FRA['4'].iloc[:,1].tolist():
                print(vv, end=',\t')
                if ii % 9 ==0:
                    print()
                ii+=1
        else:
            #print(FRA['2'].iloc[:,0].tolist())
            for vv in FRA['2'].iloc[:,0].tolist():
                print(vv, end=',\t')
                if ii % 9 ==0:
                    print()
                ii+=1

    memsize=0
    for kk in FRA:
        memsize+=getsizeof(FRA[kk],False)
    print('FRA(%d):'%len(FRA),showsize(memsize))

    print('end mem:',sysmem())
    if TOCSV:
        csv_fname='%d.csv' % int(FNAME)
        #FRA.to_csv(csv_fname)

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
    dataver='%06d' % dataver  #6位字符串

    frad=False
    if str(int(dataver)).startswith('787'):
        frad=True

    if frad:
        filename_zip=dataver+'.frd'     #.vec压缩包内的文件名
    else:
        filename_zip=dataver+'.fra'     #.vec压缩包内的文件名
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
            if not frad and line.startswith('//') and tmp1[0] == '3':     # "3|..." 的标题比较特殊，末尾少了一个tab
                tmp1[1] += '\t'
            if line.startswith('//') and tmp1[0] == '7':     # "7|..." 的标题比较特殊，起始多了一个tab
                tmp1[1]=tmp1[0].lstrip()
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
    print(u' 读解码库，参数配置文件 vec 中 xx.fra 文件。比如 010412.fra')
    print(u'    787xx 的frad 库，则读 xxx.frd 文件')
    print(u'      ARINC-647A-1 的xml配置文件找不到。所以可能无法解码。')
    print(u' 命令行工具。')
    print(sys.argv[0]+' [-h|--help] [-f|--file]  ')
    print('   -h, --help        print usage.')
    print('   -v, --ver=10412   dataver 中的参数配置表')
    print('   --csv            save to "dataver.csv" file.')
    print('   --paramlist      list all param name.')
    print('   --param alt_std  show "alt_std" param.')
    print(u'               author:南方航空,LLGZ@csair.com')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hvf:',['help','ver=','csv','paramlist','param='])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    DUMPDATA=False
    TOCSV=False
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
            TOCSV=True
        elif op in('--paramlist',):
            PARAMLIST=True
        elif op in('--param',):
            PARAM=value
    if len(args)>0:  #命令行剩余参数
        FNAME=args[0]  #只取第一个
    if FNAME is None:
        usage()
        exit()

    main()
    print('mem:',sysmem())

