#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
 读解码库，参数配置文件 vec 中 xx.par 文件。比如 010XXX.par
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
    PAR=read_parameter_file(FNAME)

    if PARAMLIST:
        #----------显示所有参数名-------------
        ii=0
        for vv in PAR.iloc[:,0].tolist():
            print(vv, end=',\t')
            if ii % 9 ==0:
                print()
            ii+=1
        print()
        if len(TOCSV)>4:
            print('Write to CSV file:',TOCSV)
            PRA.iloc[:,0].to_csv(TOCSV,sep='\t')

        if 0:
            dict2=PAR.iloc[:,[0,2,7,8,17,36,37,38]].to_dict('split')
            #print(dict2)
            #print(dict2['data'])
            for vv in dict2['data']:
                if not isinstance(vv[7],list) or len(vv[7])<1:
                    continue
                print(vv)
        return

    if PARAM is not None and len(PARAM)>0:
        #----------显示单个参数的配置内容-------------
        param=PARAM.upper()
        tmp=PAR
        tmp2=tmp[ tmp.iloc[:,0]==param ].copy() #dataframe
        tmp=tmp.iloc[[0,]].append( tmp2,  ignore_index=False )
        pd.set_option('display.max_columns',48)
        pd.set_option('display.width',156)
        print(len(tmp.columns))
        print(tmp)
        return

    pd.set_option('display.max_columns',18)
    pd.set_option('display.width',156)
    pd.set_option('display.min_row',33)
    pd.set_option('display.min_row',330)
    tmp=PAR[[0,2,3,4,5,6,7,8,9,17,20]]
    tmp.iat[0,2]='1-Equip/Label/SDI'  # Source1 (Equip/Label/SDI)
    tmp.iat[0,3]='2-Equip/Label/SDI'  # Source2 (Equip/Label/SDI)
    tmp.iat[0,5]='S_Bit' # Sign Bit
    tmp.iat[0,7]='D_Bits'  # Data Bits
    tmp.iat[0,9]='FormatMode'   # Display Format Mode
    tmp.iat[0,10]='字段长.分数部分'   # Field Length.Fractional Part
    print(tmp)
    #print(tmp.iat[0,9])
    #print(tmp.iat[0,10])
    tmp=PAR[[0,24,25,36,37,38,39,40]]
    tmp.iat[0,2]='InternalFormat' # Internal Format (Float ,Unsigned or Signed)
    print(tmp)

    '''
    ii=0
    for vv1 in PAR:
        print(vv1,'\n')
        ii +=1
        if ii>4:
            break
    '''

    print('PAR(%d):'%len(PAR))
    print('PAR:',getsizeof(PAR))
    print('end mem:',sysmem())
    #print(PAR.loc[:,2].unique() ) #列出所有的Type
    #print(PAR.loc[:,6].unique() ) #列出所有的SignBit
    #print(PAR.loc[:,7].unique() ) #列出所有的MSB
    #print(PAR.loc[:,8].unique() ) #列出所有的DataBit
    #print(PAR.loc[:,12].unique() ) #列出所有的Computation:Value=Constant Value or Resol=Coef...
    #print(PAR.loc[:,29].dropna().tolist() ) #列出所有的 Coef A(Res) ,有数组
    #print(PAR.loc[:,30].dropna().tolist() ) #列出所有的 Coef b,有数组
    #print(PAR.loc[:,31].dropna().tolist() ) #列出所有的 Dot,都是None
    #print(PAR.loc[:,32].dropna().tolist() ) #列出所有的 X,都是None
    #print(PAR.loc[:,33].dropna().tolist() ) #列出所有的 Y,都是None
    #print(PAR.loc[:,34].unique() ) #列出所有的 Coef A,都是None
    #print(PAR.loc[:,35].unique() ) #列出所有的 Power,都是None
    #print(PAR.loc[0] ) #列出所有的column
    if len(TOCSV)>0:
        print('Write to CSV file:',TOCSV)
        PAR.to_csv(TOCSV)

def read_parameter_file(dataver):

    dataver='%06d' % int(dataver)  #6位字符串

    filename_zip=dataver+'.par'     #.vec压缩包内的文件名
    zip_fname=os.path.join(conf.vec,dataver+'.vec')  #.vec文件名

    if os.path.isfile(zip_fname)==False:
        print('ERR,ZipFileNotFound',zip_fname,flush=True)
        raise(Exception('ERR,ZipFileNotFound'))

    try:
        fzip=zipfile.ZipFile(zip_fname,'r') #打开zip文件
    except zipfile.BadZipFile as e:
        print('ERR,FailOpenZipFile',e,zip_fname,flush=True)
        raise(Exception('ERR,FailOpenZipFile'))
    
    PAR=[]
    with StringIO(fzip.read(filename_zip).decode('utf16')) as fp:
    #with open(vec_fname,'r',encoding='utf16') as fp:
        ki=-1
        offset=0  #总偏移
        PAR_offset={}  #各行记录的，偏移和长度
        one_par={}  #单个参数的记录汇总
        for line in fp.readlines():
            line=line.strip('\r\n //')
            tmp1=line.split('|',1)
            tmp2=tmp1[1].split('\t')
            if tmp1[0] == '1':  #记录的开始行
                ki +=1
                if ki>0:
                    #print('one_par:',one_par,'\n')
                    PAR.append( one_PAR(PAR_offset,one_par) )
                    #if ki==1:
                    #    print('PAR(%d):'%len(PAR), PAR,'\n')
                    #    print('PAR_offset:',PAR_offset,'\n')
                    #if ki>2:
                    #    break
                one_par={}
            if tmp1[0] == '13': #记录的结束行
                continue
            if ki==0:  #文件头,记录的注释头
                if tmp1[0] in PAR_offset: #文件头中不应该有重复
                    raise(Exception('ERROR, "%s" in PAR_offset' % (tmp1[0]) ))
                else:
                    PAR_offset[ tmp1[0] ]=[ offset , len(tmp2) ]  #记录各组记录，应在整条记录的位置
                    offset += len(tmp2)  #总偏移
            #记录完整的一个参数的记录
            if tmp1[0] not in one_par:
                one_par[ tmp1[0] ]=[]
                for jj in tmp2:
                    one_par[ tmp1[0] ].append( [jj,] )
            else:
                for jj in range( len(tmp2) ):
                    one_par[ tmp1[0] ][jj].append( tmp2[jj] )
        PAR.append( one_PAR(PAR_offset,one_par) )

    fzip.close()

    return pd.DataFrame(PAR)  #返回dataframe
    #return PAR       #返回list

def one_PAR(PAR_offset,one_par):
    '''
    拼装 一行记录. 一个参数的记录
       author:南方航空,LLGZ@csair.com
    '''
    ONE=[]
    for kk in PAR_offset:  #每个记录 子行
        for jj in range( PAR_offset[ kk ][1] ):  #根据子行的长度，全部初始化为空list
            ONE.append([])
        if kk in one_par:
            if PAR_offset[kk][1] != len(one_par[kk]):  #对应记录的数目不正确
                raise(Exception('one_par[%s] length require %d not %d' % (kk, PAR_offset[kk][1], len(one_par))))

            offset=PAR_offset[ kk ][0]
            for jj in range( len(one_par[ kk ]) ):  #把one_par的对应项extend 到ONE的对应位置
                ONE[offset+jj].extend( one_par[kk][jj] )
    for jj in range( len(ONE) ):  #整理记录。只有一条记录的，去除list
        if len(ONE[jj])==0:
            ONE[jj]=None
        elif len(ONE[jj])==1:
            ONE[jj]=ONE[jj][0]

    #print('ONE(%d):'%len(ONE),  ONE, '\n')
    return ONE


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
def getsizeof(buf):
    size=sys.getsizeof(buf)
    return showsize(size)
def sysmem():
    size=psutil.Process(os.getpid()).memory_info().rss #实际使用的物理内存，包含共享内存
    #size=psutil.Process(os.getpid()).memory_full_info().uss #实际使用的物理内存，不包含共享内存
    return showsize(size)



import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'   命令行工具。')
    print(u' 读解码库，参数配置文件 vec 中 xx.par 文件。比如 010XXX.par')
    print(sys.argv[0]+' [-h|--help]')
    print('   -h, --help        print usage.')
    print('   -v, --ver=10XXX      dataver 中的参数配置表')
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
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hv:p:f:',['help','ver=','csv=','paramlist','param='])
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
        elif op in('-p','--param',):
            PARAM=value
    if len(args)>0:  #命令行剩余参数
        FNAME=args[0]  #只取第一个
    if FNAME is None:
        usage()
        exit()

    main()
    print('mem:',sysmem())

