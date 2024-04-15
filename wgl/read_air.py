#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
 读取 aircraft.air 文件。机尾号与解码库的对应表。
    author: osnosn@126.com
"""
#import struct
#from datetime import datetime
import pandas as pd
import config_vec as conf

def main(reg):
    global FNAME,DUMPDATA
    global ALLREG,ALLVER,ALLTYPE
    global TOCSV

    FNAME=conf.aircraft

    df_flt=csv(FNAME)
    columns=df_flt.columns

    if ALLREG:
        #----------显示所有机尾号-------------
        tmp=df_flt.iloc[1:,0]  #series
        ii=1
        for vv in tmp.to_list():
            if vv.startswith('//'):
                continue
            print(vv, end=',\t')
            if ii % 10 ==0:
                print()
            ii+=1
        print()
        if len(TOCSV)>4:
            print('Write to CSV file:',TOCSV)
            #tmp=df_flt.iloc[1:,0]  #series
            #tmp=df_flt.iloc[1:,[0,2,3,6,12,13]]  #DataFrame
            tmp=df_flt.iloc[1:,[0,12]]  #DataFrame
            tmp.to_csv(TOCSV,sep='\t')
        return

    if ALLVER:
        #----------显示所有解码库号-------------
        tmp=df_flt.iloc[1:,12].unique()  #numpy.ndarray
        tmp.sort()
        ii=1
        for vv in tmp.tolist():
            print(vv, end=',\t')
            if ii % 5 ==0:
                print()
            ii+=1
        print()
        return

    if ALLTYPE:
        #----------显示所有解码库号-------------
        print('All aircraft Type:')
        tmp=df_flt.iloc[1:,3].unique()  #numpy.ndarray
        ii=1
        for vv in tmp.tolist():
            print(vv, end=',\t')
            if ii % 5 ==0:
                print()
            ii+=1
        print()
        print('All aircraft COMP:')
        tmp=df_flt.iloc[1:,2].unique()  #numpy.ndarray
        ii=1
        for vv in tmp.tolist():
            print(vv, end=',\t')
            if ii % 5 ==0:
                print()
            ii+=1
        print()
        return

    if reg is not None and len(reg)>0: #给出特定机尾号的记录
        reg=reg.upper()
        if not reg.startswith('B-'):
            reg = 'B-'+reg
        print(reg)

        pd.set_option('display.max_columns',64)
        pd.set_option('display.width',156)
        #pd.set_option('display.width',256)
        #tmp=df_flt[ df_flt[columns[0]]==reg].copy()  #dataframe
        tmp2=df_flt[ df_flt.iloc[:,0]==reg].copy()  #dataframe
        tmp=tmp2.append(tmp2, ignore_index=False )
        if len(tmp2)<1:
            print('Aircraft registration %s not found.' % reg)
            print()
            return
        tmp.iloc[1]=[x for x in range(len(columns))] #添加一个数字序列，用来标记column的index
        tmp.dropna(axis=1,inplace=True)
        tmp.iat[1,0]='col序列-->'
        print(tmp)
        return

    #print(len(columns))
    print(columns)
    col=['// A/C tail', 'Reception date', 'Airline', 'A/C type',
            'A/C type wired no', 'A/C ident', #'A/C serial number',
    #        'A/C in operation (1=YES/0=NO)', 'QAR/DAR recorder model',
    #        'QAR/DAR recorder 2 model', 'FDR recorder model',
    #        'FDR recorder 2 model',
            'Version for analysis/QAR/DAR',
            'Version for analysis/QAR/DAR 2',
    #        'Version for analysis/FDR',
    #        'Version for analysis/FDR2', '//AGS'
            ]
    print(df_flt[col])
    #print(df_flt)

    if len(TOCSV)>4:
        print('Write to CSV file:',TOCSV)
        df_flt.to_csv(TOCSV)
    return


def csv(csv_filename):
    #print('   read "%s"'%csv_filename)
    if not os.path.exists(csv_filename):
        print('   "%s" Not Found.'%csv_filename)
        return
    fp=open(csv_filename,'r',encoding='utf16')
    head1=fp.readline().strip()
    head2=fp.readline().strip()
    fp.close()
    head=(head1+'\t'+head2).split('\t')
    for ii in range(len(head)):
        if head[ii]=='(Spare)': #处理重复项目
            head[ii]+=str(ii)
    '''
    df_flt=pd.read_csv(csv_filename,
                   header=0,
                   #skiprows=[0,1,2,3,4,6,7,8,9],
                   skiprows=[1,],    #aircraft.air
                   index_col=None,sep='\t',
                   #nrows=10000,
                   engine='c',
                   encoding='utf16'
                   )
    '''
    df_flt=pd.read_table(csv_filename,
                   #header=0,
                   header=None,
                   names=head,
                   #skiprows=[0,1,2,3,4,6,7,8,9],
                   skiprows=[0,1,],    #aircraft.air
                   index_col=None,sep='\t',
                   #nrows=10000,
                   #on_bad_lines='warn',
                   engine='c',
                   encoding='utf16'
                   )
    return df_flt





import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'   命令行工具。')
    print(u' 读取 aircraft.air 文件。机尾号与解码库的对应表。')
    print(sys.argv[0]+' [-h|--help] ')
    print('   -h, --help      print usage.')
    print('   -d                 dump "aircraft.air" file.')
    print('   --csv xx.csv       save to "xx.csv" file.')
    print('   --csv xx.csv.gz    save to "xx.csv.gz" file.')
    print('   -r,--reg b-1843    show recorder of aircraft,"B-1843" ')
    print('   --allreg           list all REGistration number from "aircraft.air" file.')
    print('   --allver           list all DataVer number from "aircraft.air" file.')
    print('   --alltype          list all aircraft Type from "aircraft.air" file.')
    print(u'\n               author: osnosn@126.com')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hdr:',['help','allreg','allver','alltype','reg=','csv=',])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    REG=None
    ALLREG=False
    ALLVER=False
    ALLTYPE=False
    DUMPDATA=False
    TOCSV=''
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-r','--reg'):
            REG=value
        elif op in('--allver',):
            ALLVER=True
        elif op in('--alltype',):
            ALLTYPE=True
        elif op in('--allreg',):
            ALLREG=True
        elif op in('-d',):
            DUMPDATA=True
        elif op in('--csv',):
            TOCSV=value
    if len(args)>0:  #命令行剩余参数
        REG=args[0]  #只取第一个

    if ALLTYPE or ALLREG or ALLVER or DUMPDATA or REG or len(TOCSV)>0:
        main(REG)
    else:
        print('Do nothing.')

