#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
 读解码库，参数配置文件 vec 中 xx.par 文件。比如 010XXX.par
    author:南方航空,LLGZ@csair.com
"""
import os
import zipfile
import gzip
import csv
from io import StringIO
import config_vec as conf

#PAR=None  #保存读入的配置. 当作为模块,被调用时使用.
#DataVer=None

def main():
    global FNAME,DUMPDATA
    global TOCSV
    global PARAMLIST
    global PARAM
    par_conf=read_parameter_file(FNAME)

    if PARAMLIST:
        #----------显示所有参数名-------------
        ii=0
        for vv in par_conf:
            print(vv[0], end=',\t')
            if ii % 10 ==0:
                print()
            ii+=1
        print()

        if len(TOCSV)>4:
            print('Write to CSV file:',TOCSV)
            if TOCSV.endswith('.gz'):
                fp=gzip.open(TOCSV,'wt',encoding='utf8')
            else:
                fp=open(TOCSV,'w',encoding='utf8')
            ii=0
            for row in par_conf:
                fp.write(str(ii)+'\t'+row[0]+'\n')
                ii+=1
        return

    if PARAM is not None and len(PARAM)>0:
        #----------显示单个参数的配置内容-------------
        param=PARAM.upper()
        idx=[]
        ii=0
        for row in par_conf: #找出所有记录
            if row[0] == param: idx.append(ii)
            ii +=1
        if len(idx)>0:
            for ii in range(len(par_conf[0])):
                print(ii,end=',\t')
                for jj in idx:
                    print(par_conf[jj][ii], end=',\t')
                print(par_conf[0][ii])
        else:
            print('Parameter %s not found in Regular parameter.'%param)
        '''
        # 只找出第一条记录，通常par参数只会有一条记录
        idx=0
        for row in par_conf:
            if row[0] == param: break
            idx +=1
        if idx < len(par_conf):
            for ii  in range(len(par_conf[0])):
                print(ii, par_conf[idx][ii], par_conf[0][ii], sep=',\t')
        else:
            print('Parameter %s not found in Regular parameter.'%param)
        '''
        print()
        return

    #loc=(0,2,3,4,5,6,7,8,9,17,20)
    #tmp.iat[0,2]='1-Equip/Label/SDI'  # Source1 (Equip/Label/SDI)
    #tmp.iat[0,3]='2-Equip/Label/SDI'  # Source2 (Equip/Label/SDI)
    #tmp.iat[0,5]='S_Bit' # Sign Bit
    #tmp.iat[0,7]='D_Bits'  # Data Bits
    #tmp.iat[0,9]='FormatMode'   # Display Format Mode
    #tmp.iat[0,10]='字段长.分数部分'   # Field Length.Fractional Part
    #loc=(0,24,25,36,37,38,39,40)

    loc=(0,2,3,4,5,6,7,8,9,17,20,24,25,36,37,38,39,40)
    #tmp.iat[0,2]='InternalFormat' # Internal Format (Float ,Unsigned or Signed)
    par_len=len(par_conf)-1
    print('---------- recorder num:',par_len,'------------')
    for ii in range(len(par_conf[0])):
        print(ii,end=',')
        for jj in range(1,6):
            print('\t',par_conf[jj][ii], end=',')
        print('\t',par_conf[0][ii])


    #----写CSV文件--------
    if len(TOCSV)>4:
        print('Write to CSV file:',TOCSV)
        if TOCSV.endswith('.gz'):
            fp=gzip.open(TOCSV,'wt',encoding='utf8')
        else:
            fp=open(TOCSV,'w',encoding='utf8')
        buf=csv.writer(fp,delimiter='\t')
        buf.writerows(par_conf)
        fp.close()
    return

def read_parameter_file(dataver):
    #global PAR
    #global DataVer

    dataver='%06d' % int(dataver)  #6位字符串
    #if PAR is not None and DataVer==dataver:
    #    return PAR
    #else:
    #    DataVer=dataver
    #    PAR=None

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
    
    par_conf=[]
    with StringIO(fzip.read(filename_zip).decode('utf16')) as fp:
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
                    par_conf.append( one_PAR(PAR_offset,one_par) )
                    #if ki==1:
                    #    print('par_conf(%d):'%len(par_conf), par_conf,'\n')
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
        par_conf.append( one_PAR(PAR_offset,one_par) )

    fzip.close()

    #PAR=par_conf
    return par_conf       #返回list

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
        elif op in('-p','--param',):
            PARAM=value
    if len(args)>0:  #命令行剩余参数
        FNAME=args[0]  #只取第一个
    if FNAME is None:
        usage()
        exit()

    main()

