#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
  解码所有参数，写入DataFile文件。压缩或者不压缩。解码的值,以json写入。早期的方式。
    我的测试 Intel CPU i9,x64,主频3.3GHz, BogoMIPS:6600。
    原始文件 raw 20MB，压缩包为5.5MB。有参数 2600 个, 航段170分钟。
        解所有参数，写入单文件,XZ压缩,    24MB，耗时3m51s. 最大内存占用216MB.
        解所有参数，写入单文件,LZMA压缩,  24MB，耗时3m45s. 最大内存占用216MB.
        解所有参数，写入单文件,bzip2压缩, 48MB，耗时2m11s. 最大内存占用205MB.
        解所有参数，写入单文件,gzip压缩,  85MB，耗时2m21s. 最大内存占用196MB.
        sysmem()显示，内存占用不超过 220MB.
    author: osnosn@126.com
"""
import pandas as pd
import Get_param_from_arinc717_aligned as A717
import struct

def main():
    global FNAME,WFNAME
    global ALLPARAM

    #print('mem:',sysmem())
    myQAR=A717.ARINC717('')
    #print('mem:',sysmem())
    myQAR.qar_file(FNAME)
    print('mem:',sysmem())

    if ALLPARAM:
        datafile_header=bytearray(b"QAR_Decoded_DATA_V1.0\0")
        point=len(datafile_header)
        datafile_header.extend(b"\0\0\0\0")
        datafile_header.extend(b"This is a test.\0")
        with open('Custom_DataFile_Format_Description.txt','rb') as fp:
            datafile_header.extend(fp.read())
        datafile_header.append(0)  #补'\0'
        #填入 Header size
        datafile_header[point:point+4]=struct.pack('<L',len(datafile_header)) #long,4byte,Little-Endion

        parameter_table=bytearray(b"\0\0\0\0") #Parameter_Table size

        mydatafile=None
        if WFNAME is not None and len(WFNAME)>0:
            mydatafile=open(WFNAME+'.tmp','wb')
        #-----------列出记录中的所有参数名称--------------
        regularlist,superlist=myQAR.paramlist()
        total_pm=0
        #---regular parameter
        ii=0
        for vv in regularlist:
            one_param_table=bytearray(b"\0\0")  #Parameter01 size
            one_param_table.extend(b"\0\0\0\0\0\0\0\0") #Parameter01_DATA 指针
            one_param_table.extend(b"\0\0\0\0") #Parameter01_DATA size
            one_param_table.extend(b"\0\0")       #value size
            one_param_table.extend(b"\0\0")       #rate
            one_param_table.extend(b"\0\0\0\0")   #start FrameID
            one_param_table.extend(bytes(vv,'utf8')+b'\0')  #参数名称

            print(vv,flush=True)
            ii +=1
            if ii==1: continue  #第一个不是参数
            pm_list=myQAR.get_param(vv)
            pm_name="{}.{}".format(ii,vv)
            data_len, compress_type=write_datafile(mydatafile,pm_name,pm_list)

            one_param_table.extend(compress_type)   #压缩算法
            one_param_table.extend(b'json\0')       #数据类型
            #填入 Parameter01 size
            one_param_table[0:2]=struct.pack('<H',len(one_param_table)) #short,2byte,Little-Endion
            #填入Parameter01_DATA size
            one_param_table[10:14]=struct.pack('<L',data_len) #long,4byte,Little-Endion

            parameter_table.extend(one_param_table)

        print("ragular:{}".format(ii))
        total_pm += ii-1
        print()
        print('--------------------------------------------')
        #---superframe parameter
        ii=0
        for vv in superlist:
            one_param_table=bytearray(b"\0\0")  #Parameter01 size
            one_param_table.extend(b"\0\0\0\0\0\0\0\0") #Parameter01_DATA 指针
            one_param_table.extend(b"\0\0\0\0") #Parameter01_DATA size
            one_param_table.extend(b"\0\0")       #value size
            one_param_table.extend(b"\0\0")       #rate
            one_param_table.extend(b"\0\0\0\0")   #start FrameID
            one_param_table.extend(bytes(vv,'utf8')+b'\0')  #参数名称

            print(vv,flush=True)
            ii +=1
            if ii==1: continue  #第一个不是参数
            pm_list=myQAR.get_param(vv)
            pm_name="{}.{}".format(ii,vv)
            data_len, compress_type=write_datafile(mydatafile,pm_name,pm_list)

            one_param_table.extend(compress_type)   #压缩算法
            one_param_table.extend(b'json\0')       #数据类型
            #填入 Parameter01 size
            one_param_table[0:2]=struct.pack('<H',len(one_param_table)) #short,2byte,Little-Endion
            #填入Parameter01_DATA size
            one_param_table[10:14]=struct.pack('<L',data_len) #long,4byte,Little-Endion

            parameter_table.extend(one_param_table)
        print("super:{}".format(ii))
        total_pm += ii-1
        print()
        print("total_param:{}".format(total_pm))
        print('mem:',sysmem())
        #填入 Parameter_Table 的 size
        parameter_table[0:4]=struct.pack('<L',len(parameter_table)) #long,4byte,Little-Endion
        if mydatafile is not None:
            mydatafile.close()

            point=4
            data_point=len(datafile_header)+len(parameter_table)
            while point < len(parameter_table)-8:
                #填入 Parameter01_DATA 的起始位置
                parameter_table[point+2:point+10] = struct.pack('<Q',data_point)   #long long,8byte,Little-Endion
                data_point += struct.unpack('<L',parameter_table[point+10:point+14])[0]  #long,4byte
                one_param_size = struct.unpack('<H',parameter_table[point:point+2])[0]   #short,2byte
                point += one_param_size

            with open(WFNAME,'wb') as fp:
                fp.write(datafile_header)
                fp.write(parameter_table)
                with open(WFNAME+'.tmp','rb') as ftmp:
                    fp.write(ftmp.read())
            # rm WFNAME+'.tmp'
            os.remove(WFNAME+'.tmp')

    print('mem:',sysmem())
    myQAR.close()
    print('closed.')
    print('mem:',sysmem())
    return

import lzma
import bz2
import gzip
def write_datafile(mydatafile,pm_name, pm_list):
    df_pm=pd.DataFrame(pm_list)
    #-----------参数写入data文件--------------------
    data_len=0
    compress_type=b'none\0'
    if mydatafile is None:
        if len(df_pm)>0:
            print(df_pm['v'][0:10].tolist())
    else:
        ### 获取解码参数的 json 数据
        #tmp_str=df_pm.to_csv(None,sep='\t',index=False)
        #tmp_str=df_pm.to_json(None,orient='split',index=False)
        #tmp_str=df_pm.to_json(None,orient='records')
        #tmp_str=df_pm.to_json(None,orient='index')
        tmp_str=df_pm.to_json(None,orient='values')
        #tmp_str=df_pm.to_json(None,orient='table',index=False)

        ### 解码数据的压缩
        #tmp_b=lzma.compress(bytes(tmp_str,'utf8'),format=lzma.FORMAT_XZ)    #有完整性检查
        #compress_type=b'xz\0'
        tmp_b=lzma.compress(bytes(tmp_str,'utf8'),format=lzma.FORMAT_ALONE)  #无完整性检查
        compress_type=b'lzma\0'
        #tmp_b=bz2.compress(bytes(tmp_str,'utf8'),compresslevel=9)
        #compress_type=b'bzip2\0'
        #tmp_b=gzip.compress(bytes(tmp_str,'utf8'),compresslevel=9)
        #compress_type=b'gzip\0'

        data_len=len(tmp_b)
        mydatafile.write(tmp_b)
        print('mem:',sysmem())
    return data_len, compress_type

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
    print('   -w out/xxx.dat            参数压缩/不压缩写入单文件"out/xxx.dat"')
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

