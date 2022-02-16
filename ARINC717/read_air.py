#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
 读取 aircraft.air 文件。机尾号与解码库的对应表。
    author:南方航空,LLGZ@csair.com
"""
import csv
import config_vec as conf
import gzip

AIR=None  #保存读入的配置. 当作为模块,被调用时使用.

def main(reg):
    global FNAME,DUMPDATA
    global ALLREG,ALLVER,ALLTYPE
    global TOCSV

    FNAME=conf.aircraft

    air_csv=air(FNAME)
    #第一行是标题。第二行,是第一行的继续
    #从第三行开始，是数据表
    #最后一行，是个注释
    columns=air_csv[0]

    if ALLREG:
        #----------显示所有机尾号-------------
        #第0列是机尾号
        ii=1
        for vv in air_csv:
            if vv[0].startswith('//'):
                continue
            print(vv[0], end=',\t')
            if ii % 10 ==0:
                print()
            ii+=1
        print()
        #----写CSV文件--------
        if len(TOCSV)>4:
            print('Write to CSV file:',TOCSV)
            if TOCSV.endswith('.gz'):
                fp=gzip.open(TOCSV,'wt',encoding='utf8')
            else:
                fp=open(TOCSV,'w',encoding='utf8')
            loc=(0,2,3,6,12,13)
            loc=(0,12)
            ii=-1
            for row in air_csv:
                ii+=1
                if len(row)<2:
                    continue
                fp.write(str(ii))
                for cc in loc:
                    fp.write('\t'+row[cc])
                fp.write('\n')
            fp.close()
        return

    if ALLVER:
        #----------显示所有解码库号-------------
        dataVer=[]
        for row in air_csv:
            if len(row)<2: continue
            if row[12] not in dataVer:
                dataVer.append(row[12])
        dataVer.sort()
        ii=1
        for vv in dataVer:
            print(vv, end=',\t')
            if ii % 5 ==0:
                print()
            ii+=1
        print()
        return

    if ALLTYPE:
        #----------显示所有机型号-------------
        print('All aircraft Type:')
        acType=[]
        for row in air_csv:
            if len(row)<2: continue
            if row[3] not in acType:
                acType.append(row[3])
        acType.sort()
        ii=1
        for vv in acType:
            print(vv, end=',\t')
            if ii % 5 ==0:
                print()
            ii+=1
        print()

        print('All aircraft BASE:')
        acBase=[]
        for row in air_csv:
            if len(row)<2: continue
            if row[2] not in acBase:
                acBase.append(row[2])
        acBase.sort()
        ii=1
        for vv in acBase:
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
        index=0
        for row in air_csv: #找机尾号
            if row[0]==reg: break
            index +=1
        if index>=len(air_csv):
            print('Aircraft registration %s not found.' % reg)
            print()
            return
        for ii in range(len(air_csv[index])):
            print(ii,air_csv[index][ii],air_csv[0][ii],sep=',\t')
        print()
        return

    #--------------DUMP------------
    #---显示columns---
    #print(len(columns))
    print('Columns:')
    ii=0
    for row in columns:
        print('   ',ii,'\t',row)
        ii +=1
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
    #---显示 指定列的 前后5行---
    print('Dump head row:')
    show_col=(0,1,2,3,4,5,12,13,14,15)
    ttl_rows=len(air_csv)
    ii=-1
    for row in air_csv:
        ii +=1
        if len(row)<2:
            continue
        if ii==30:
            print('   ... ...')
        if ii>10 and ii< ttl_rows-10:
            continue
        print(len(row),ii,end='\t')
        for cc in show_col:
            print(row[cc]+',',end='\t')
        print()

    #----写CSV文件--------
    if len(TOCSV)>4:
        print('Write to CSV file:',TOCSV)
        if TOCSV.endswith('.gz'):
            fp=gzip.open(TOCSV,'wt',encoding='utf8')
        else:
            fp=open(TOCSV,'w',encoding='utf8')
        buf=csv.writer(fp,delimiter='\t')
        buf.writerows(air_csv)
        fp.close()
    return


def air(csv_filename):
    global AIR
    if AIR is not None:
        return AIR
    if not os.path.exists(csv_filename):
        print('   "%s" Not Found.'%csv_filename)
        return
    air_csv=[]
    with open(csv_filename,'r',encoding='utf16') as fp:
        buf=csv.reader(fp,delimiter='\t')
        for row in buf:
            air_csv.append(row)
    #第一行和第二行合并,删除第二行 
    air_csv[0].append(','.join(air_csv[1]))
    del air_csv[1]
    AIR=air_csv
    return AIR



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
    print(u'\n               author:南方航空,LLGZ@csair.com')
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

