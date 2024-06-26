#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
  解码所有参数，写入DataFile文件。压缩或者不压缩。解码的值,以二进制写入。改进的方式。
    我的测试 Intel CPU i9,x64,主频3.3GHz, BogoMIPS:6600。
    原始文件 raw 20MB，压缩包为5.5MB。有参数 2600 个, 航段170分钟。
      174行,同时写入t,v:
            pm_data=[struct.pack('<fl',vv['t'],vv['v']) for vv in pm_list]
          解所有参数，写入单文件,LZMA压缩,  18MB，耗时2m50s.
          解所有参数，写入单文件,bzip2压缩, 46MB，耗时1m51s.

      174行,仅写入v:
            pm_data=[struct.pack('<l',vv['v']) for vv in pm_list]
          解所有参数，写入单文件,LZMA压缩,  3.6MB，耗时1m51s.
          解所有参数，写入单文件,bzip2压缩, 3.9MB，耗时1m46s.
        原始文件 raw 115MB，压缩包为23MB。有参数 2770 个, 航段960分钟。
          解所有参数，写入单文件,bzip2压缩, 8.3MB，耗时8m13s. 内存占用320-520MB.
        原始文件 raw 21MB，压缩包为5.5MB。有参数 2270 个, 航段170分钟。
          解所有参数，写入单文件,bzip2压缩, 2.3MB，耗时1m19s. 内存占用160-210MB.
    author: osnosn@126.com
"""
import pandas as pd
import Get_param_from_arinc717_aligned as A717
import struct
import json

def main():
    global FNAME,WFNAME
    global ALLPARAM

    #print('mem:',sysmem())
    myQAR=A717.ARINC717('')
    #print('mem:',sysmem())
    myQAR.qar_file(FNAME)
    print('mem:',sysmem())

    if ALLPARAM:
        #准备Header
        datafile_header=bytearray(b"QAR_Decoded_DATA_V1.0\0")
        point=len(datafile_header)
        datafile_header.extend(b"\0\0\0\0")
        meta={
                "MetaData": {
                    "DataVersion":8888,
                    "ParamConfigFile":"",
                    "Tail":".B-8888",
                    "Type":"A320",
                    "FlightNum":"CXX8888",
                    "DepICAO":"ZGGL",
                    "DepRunway":"01",
                    "ArrICAO":"ZGSZ",
                    "ArrRunway":"15L",
                    "DepDateTime":"20240102T160555Z",
                    "ArrDateTime":"20240102T170922Z",
                    "TakeOffDateTime":"20240102T162359Z",
                    "LandingDateTime":"20240102T170101Z",
                    "AirborneDuration":161,
                    "FlightDuration":173,
                    "DecodeDateTime":"20240401T122359Z",
                    "FileName":"B-8888_20010102171005-10888.wgl",
                    },
                "other":123,
                "info":"This is a test.",
                }
        datafile_header.extend(json.dumps(meta,separators=(',',':'),ensure_ascii=False).encode())
        datafile_header.append(0)  #补'\0'
        with open('Custom_DataFile_Format_Description.txt','rb') as fp:
            datafile_header.extend(fp.read())
        datafile_header.append(0)  #补'\0'
        #填入 Header size
        datafile_header[point:point+4]=struct.pack('<L',len(datafile_header)) #long,4byte,Little-Endion

        #准备Parameter_Table
        parameter_table=bytearray(b"\0\0\0\0") #Parameter_Table size

        parameter_data=bytearray() #存放 压缩/未压缩 的解码数据
        #-----------列出记录中的所有参数名称--------------
        regularlist,superlist=myQAR.paramlist()  #已经去重
        #这里需要对这两个列表, 去重. 因为有重复的参数名
        total_pm=0
        #---regular parameter
        ii=0
        for vv in regularlist:
            one_param_table=bytearray(b"\0\0")  #Parameter01 size
            one_param_table.extend(b"\0\0\0\0\0\0\0\0") #Parameter01_DATA 指针
            one_param_table.extend(b"\0\0\0\0") #Parameter01_DATA size

            print(vv,flush=True)
            ii +=1
            if ii==1: continue  #第一个不是参数
            pm_list=myQAR.get_param(vv)
            pm_par=getPAR(vv,myQAR.par)
            other_info=json.dumps(pm_par,separators=(',',':'),ensure_ascii=False).encode()+b'\0'
            pm_name="{}.{}".format(ii,vv)
            data_len, data_type, value_size, compress_type=write_datafile(parameter_data,pm_name,pm_list)
            data_rate=pm_list[1]['t']-pm_list[0]['t']
            #print(pm_list[1]['t'],pm_list[0]['t'],data_rate,flush=True)
            if data_rate<=1 and data_rate !=0:
                data_rate= 1/data_rate
            else:
                data_rate *= -1
            #print(data_rate,flush=True)

            one_param_table.extend(struct.pack('<h',value_size))     #value size
            one_param_table.extend(struct.pack('<h',int(data_rate))) #rate
            #start_frameID一定是个整数, 0.0, 1.0
            one_param_table.extend(struct.pack('<f',pm_list[0]['t']))  #start FrameID, f32
            one_param_table.extend(bytes(vv,'utf8')+b'\0')  #参数名称
            one_param_table.extend(compress_type)           #压缩算法
            one_param_table.extend(data_type)          #数据类型
            one_param_table.extend(other_info)         #其他信息
            #填入 Parameter01 size
            one_param_table[0:2]=struct.pack('<H',len(one_param_table)) #short,2byte,Little-Endion
            #填入Parameter01_DATA size
            one_param_table[10:14]=struct.pack('<L',data_len) #long,4byte,Little-Endion

            #加入Parameter_Table
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

            print(vv,flush=True)
            ii +=1
            if ii==1: continue  #第一个不是参数
            pm_list=myQAR.get_param(vv)
            pm_par=getPAR(vv,myQAR.par)
            pm_par['Super']=1 #这是个超级帧参数
            other_info=json.dumps(pm_par,separators=(',',':'),ensure_ascii=False).encode()+b'\0'
            pm_name="{}.{}".format(ii,vv)
            data_len, data_type, value_size, compress_type=write_datafile(parameter_data,pm_name,pm_list)
            data_rate=pm_list[1]['t']-pm_list[0]['t']
            if data_rate<=1 and data_rate !=0:
                data_rate= 1/data_rate
            else:
                data_rate *= -1
            #print(data_rate,flush=True)

            one_param_table.extend(struct.pack('<h',value_size))     #value size
            one_param_table.extend(struct.pack('<h',int(data_rate))) #rate
            #start_frameID一定是个整数, 0.0, 1.0
            one_param_table.extend(struct.pack('<f',pm_list[0]['t']))  #start FrameID, f32
            one_param_table.extend(bytes(vv,'utf8')+b'\0')  #参数名称
            one_param_table.extend(compress_type)           #压缩算法
            one_param_table.extend(data_type)          #数据类型
            one_param_table.extend(other_info)         #其他信息
            #填入 Parameter01 size
            one_param_table[0:2]=struct.pack('<H',len(one_param_table)) #short,2byte,Little-Endion
            #填入Parameter01_DATA size
            one_param_table[10:14]=struct.pack('<L',data_len) #long,4byte,Little-Endion

            #加入Parameter_Table
            parameter_table.extend(one_param_table)
        print("super:{}".format(ii))
        total_pm += ii-1
        print()
        print("total_param:{}".format(total_pm))
        print('mem:',sysmem())
        #填入 Parameter_Table 的 size
        parameter_table[0:4]=struct.pack('<L',len(parameter_table)) #long,4byte,Little-Endion
        point=4
        data_point=len(datafile_header)+len(parameter_table)
        while point < len(parameter_table)-8:
            #填入 Parameter01_DATA 的起始位置
            parameter_table[point+2:point+10] = struct.pack('<Q',data_point)   #long long,8byte,Little-Endion
            data_point += struct.unpack('<L',parameter_table[point+10:point+14])[0]  #long,4byte
            one_param_size = struct.unpack('<H',parameter_table[point:point+2])[0]   #short,2byte
            point += one_param_size

        if WFNAME is not None and len(WFNAME)>0:
            with open(WFNAME,'wb') as mydatafile:
                mydatafile.write(datafile_header)
                mydatafile.write(parameter_table)
                mydatafile.write(parameter_data)

    print('mem:',sysmem())
    myQAR.close()
    print('closed.')
    print('mem:',sysmem())
    return

import lzma
import bz2
import gzip
def write_datafile(parameter_data,pm_name, pm_list):
    #-----------参数写入data文件--------------------
    data_len=0
    data_type=b'txt\0'
    value_size=0
    if parameter_data is None:
        #不写文件,就打印到终端
        if len(pm_list)>0:
            print([vv['v'] for vv in pm_list[0:10] ])
    else:
        if len(pm_list)<1:
                #参数没有值
                print('=>ERROR,',pm_name,pm_list,'此参数无值,可能是配置文件不匹配.')
                tmp_str=b'"none"'
                data_type=b'json\0'
                value_size=0
        else:
            if isinstance(pm_list[0]['v'], int) :
                #pm_data=[struct.pack('<fl',vv['t'],vv['v']) for vv in pm_list]
                pm_data=[struct.pack('<l',vv['v']) for vv in pm_list]
                tmp_str=b"".join(pm_data)
                data_type=b'int\0'
                value_size=4
            elif isinstance(pm_list[0]['v'], float) :
                #pm_data=[struct.pack('<ff',vv['t'],vv['v']) for vv in pm_list]
                pm_data=[struct.pack('<f',vv['v']) for vv in pm_list]
                tmp_str=b"".join(pm_data)
                data_type=b'float\0'
                value_size=4
            else:
                ### 获取解码参数的 json 数据
                df_pm=pd.DataFrame(pm_list)
                #tmp_str=df_pm.to_csv(None,sep='\t',index=False)
                #tmp_str=df_pm.to_json(None,orient='split',index=False)
                #tmp_str=df_pm.to_json(None,orient='records')
                #tmp_str=df_pm.to_json(None,orient='index')
                tmp_str=df_pm.to_json(None,orient='values')
                #tmp_str=df_pm.to_json(None,orient='table',index=False)

                tmp_str=bytes(tmp_str,'utf8')
                data_type=b'json\0'
                value_size=0

        ### 解码数据的压缩
        ### lzma占用内存大,bzip2占用内存小,bzip2速度快,两者压缩率在此场景下差不多
        #tmp_b=lzma.compress(tmp_str,format=lzma.FORMAT_XZ)    #有完整性检查
        #compress_type=b'xz\0'
        #tmp_b=lzma.compress(tmp_str,format=lzma.FORMAT_ALONE)  #无完整性检查
        #compress_type=b'lzma\0'
        tmp_b=bz2.compress(tmp_str,compresslevel=9)
        compress_type=b'bzip2\0'
        #tmp_b=gzip.compress(tmp_str,compresslevel=9)
        #compress_type=b'gzip\0'

        data_len=len(tmp_b)
        parameter_data.extend(tmp_b)
        print('mem:',sysmem())
    return data_len, data_type, value_size, compress_type

def getPAR(param,par):
    param=param.upper()  #改大写
    pm_find=None  #临时变量
    for row in par:  #找出第一条匹配的记录, par中只会有一条记录
        if row[0] == param:
            pm_find=row
            break
    if pm_find is None:
        return {}
    else:
        tmp_part=[]
        if isinstance(pm_find[39], list):
            #DISCRETE Options
            for ii in range(len(pm_find[39])):
                tmp_part.append([
                    int(pm_find[39][ii]),
                    pm_find[40][ii],
                    ])
    #print(pm_find)
    info={}
    info["RecFormat"]= pm_find[2]
    if len(pm_find[11])>0:
        info["Offset"]=pm_find[11]
    if len(pm_find[12])>0:
        info["Resol"]=pm_find[12]
    info["Mode"]=pm_find[17]
    info["显示位数"]=pm_find[20]
    if len(pm_find[21])>0:
        info["Unit"]=pm_find[21]
    if len(pm_find[25])>0:
        info["Type"]=pm_find[25]
    info["Rate"]=int(pm_find[24])
    if pm_find[29] is not None:
        info["Ares"]=pm_find[29]
    if pm_find[30] is not None:
        info["B"]=pm_find[30]
    if pm_find[32] is not None:
        info["X"]=pm_find[32]
    if pm_find[33] is not None:
        info["Y"]=pm_find[33]
    if pm_find[34] is not None:
        info["A"]=pm_find[34]
    if pm_find[35] is not None:
        info["Power"]=pm_find[35]
    if len(tmp_part)>0:
        info["Options"]= tmp_part
    info["LongName"]= pm_find[1].strip()
    return info

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

