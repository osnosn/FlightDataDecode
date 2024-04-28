#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
 解码的值,以json, int, float 写入 DataFile文件。压缩或者不压缩。
 读取 DataFile 文件中的参数。导入 pandas.DataFrame().
    author: osnosn@126.com
"""
import pandas as pd
import struct
import json
import lzma
import bz2
import gzip

class DATAFILE():
    def __init__(self,fname=''):
        self.data_filename=''
        self.data_header=None
        self.data_paramtable=None
        if len(fname)>0:
            self.data_file(fname)
    def data_file(self,data_filename):
        '''
        打开文件，读取文件头和参数表
        '''
        self.data_filename=data_filename
        with open(self.data_filename,'rb') as fp:
            tag=fp.read(22)
            if tag != b'QAR_Decoded_DATA_V1.0\0':
                print('DataFile "{}" formart ERROR.'.format(self.data_filename))
                return False
            else:
                #读取 Header
                self.data_header = bytearray(fp.read(4))
                size = struct.unpack('<L',self.data_header)[0]
                self.data_header.extend(fp.read(size - 4 - len(tag)))
                #读取 Parameter_Table
                self.data_paramtable = bytearray(fp.read(4))
                size = struct.unpack('<L',self.data_paramtable)[0]
                self.data_paramtable.extend(fp.read(size - 4))
    def paramlist(self):
        '''
        返回文件头的说明，和参数表
        '''
        if self.data_header is None or self.data_paramtable is None:
            return None,None
        # 文件头的说明部分
        size = struct.unpack('<L',self.data_header[0:4])[0]
        tmp = self.data_header[4:size].split(b'\0',3)
        header = (tmp[0].decode(), tmp[1].decode() )

        # Parameter_Table 的参数名称
        param=[]
        point=4
        while point < len(self.data_paramtable):
            size=struct.unpack('<H',self.data_paramtable[point:point+2])[0]
            tmp = self.data_paramtable[point+22:point+size].split(b'\0',3)
            if len(tmp)<3:
                print('Parameter Table ERROR.',tmp)
                return header,param
            #param.append([tmp[0].decode(),tmp[1].decode(),tmp[2].decode()])
            param.append(tmp[0].decode() )
            point += size
        return header, param
    def getparam(self,pm):
        '''
        取出,解压,单个参数
        '''
        data=None
        if self.data_paramtable is None:
            return data
        point=4
        found=False
        while point < len(self.data_paramtable):
            size=struct.unpack('<H',self.data_paramtable[point:point+2])[0]
            tmp = self.data_paramtable[point+22:point+size].split(b'\0',3)
            if len(tmp)<3:
                print('Parameter Table ERROR.',tmp)
                return data
            elif pm.encode() == tmp[0]:
                found=True
                break
            point += size
        if found:
            data_point=struct.unpack('<Q',self.data_paramtable[point+2:point+10])[0]
            data_len=struct.unpack('<L',self.data_paramtable[point+10:point+14])[0]
            value_size=struct.unpack('<H',self.data_paramtable[point+14:point+16])[0]
            rate=struct.unpack('<h',self.data_paramtable[point+16:point+18])[0]
            frameID=struct.unpack('<l',self.data_paramtable[point+18:point+22])[0]
            #print(tmp)
            #print(data_point,data_len,value_size,rate,frameID)
            with open(self.data_filename,'rb') as fp:
                fp.seek(data_point)
                data=fp.read(data_len)

            ### 解压缩
            if tmp[1] == b'xz':
                data=lzma.decompress(data,format=lzma.FORMAT_XZ)    #有完整性检查
            elif tmp[1] == b'lzma':
                data=lzma.decompress(data,format=lzma.FORMAT_ALONE)  #无完整性检查
            elif tmp[1] == b'bzip2':
                data=bz2.decompress(data)
            elif tmp[1] == b'gzip':
                data=gzip.decompress(data)
            else:  #其他值,不解压缩
                pass

            ### 解值
            if tmp[2] == b'int':
                if value_size == 4:
                    data_v=[ vv[0] for vv in struct.iter_unpack('<i',data)]
                else:
                    print('value_size ERROR.')
            elif tmp[2] == b'float':
                if value_size == 4:
                    data_v=[ vv[0] for vv in struct.iter_unpack('<f',data)]
                    data=data_v
                else:
                    print('value_size ERROR.')
            else:  #其他文本格式,不处理
                data=data.decode()
                pass
            ### FrameID
            if tmp[2] == b'int'or tmp[2] == b'float':
                if rate >0:
                    data_t=[vv*(1/float(rate)) for vv in range(0,len(data_v)) ]
                else:
                    data_t=[vv*(-1*float(rate)) for vv in range(0,len(data_v)) ]
                #data=list(zip(data_t,data_v))
                return (data_t,data_v)
        return data
    def pick_param(self,PARAM):
        '''
        挑出选取的参数, 单独写入,自定义格式的单文件
        '''
        if self.data_paramtable is None:
            return
        #抄原来的 header
        datafile_header=bytearray(b"QAR_Decoded_DATA_V1.0\0")  #tag
        datafile_header.extend(self.data_header)

        #准备Parameter_Table
        parameter_table=bytearray(b"\0\0\0\0") #Parameter_Table size
        point=4
        while point < len(self.data_paramtable):
            size=struct.unpack('<H',self.data_paramtable[point:point+2])[0]
            tmp = self.data_paramtable[point+22:point+size].split(b'\0',3)
            if len(tmp)<3:
                print('Parameter Table ERROR.',tmp)
                return
            elif tmp[0].decode() in PARAM:
                #加入Parameter_Table, 抄原来的 one_param表.
                parameter_table.extend(self.data_paramtable[point:point+size])
            point += size
        #参数找完
        #填入 Parameter_Table 的 size
        parameter_table[0:4]=struct.pack('<L',len(parameter_table)) #long,4byte,Little-Endion
        #重写 Parameter_Table 中DATA 的起始位置, 
        #并保存原来的位置,用于读取DATA
        data_old_point_size=[]
        point=4
        data_point=len(datafile_header)+len(parameter_table)
        while point < len(parameter_table)-8:
            #读取原位置,size,并保存
            data_old_point = struct.unpack('<Q',parameter_table[point+2:point+10])[0]  #long long,8byte
            data_old_size = struct.unpack('<L',parameter_table[point+10:point+14])[0]  #long,4byte
            data_old_point_size.append((data_old_point,data_old_size))
            #填入 Parameter01_DATA 新的起始位置
            parameter_table[point+2:point+10] = struct.pack('<Q',data_point)   #long long,8byte,Little-Endion
            data_point += data_old_size
            one_param_size = struct.unpack('<H',parameter_table[point:point+2])[0]   #short,2byte
            point += one_param_size
        #写dat文件
        with open(WFNAME,'wb') as wfp:
            wfp.write(datafile_header)
            wfp.write(parameter_table)
            with open(self.data_filename,'rb') as oldfp:
                for point,size in data_old_point_size:
                    oldfp.seek(point)
                    wfp.write(oldfp.read(size))
        return
    def close(self):
        '清除,保留的所有配置和数据'
        self.data_filename=''
        self.data_header=None
        self.data_paramtable=None

def main():
    global FNAME,WFNAME
    global PARAMLIST

    datafile=DATAFILE()
    datafile.data_file(FNAME)

    if PARAMLIST:
        #读取Header和参数表
        header, param=datafile.paramlist()
        #显示
        print(header[0])
        print(' -----------------')
        print(header[1])
        print(' -----------------')
        ii=0
        for vv in param:
            if ii % 8 ==0:
                print()
            print(vv, end='\t')
            ii += 1
        print()
        print('  -----Total {}-----'.format(ii)) 
    elif len(PARAM)>0:
        if WFNAME is not None and WFNAME.endswith('.dat'):
            #写 xx.dat，单独处理
            datafile.pick_param(PARAM)
            print('Data Write into "{}"'.format(WFNAME))
        else:
            #写 xx.csv 或 xx.csv.gz 
            print(PARAM)
            df_all=pd.DataFrame()
            for pm in PARAM:
                #取一个参数的DATA
                one_pm = datafile.getparam(pm)
                if one_pm is None:
                    continue
                if isinstance(one_pm, tuple):
                    #非文本格式, 即 int,float格式
                    #导入DataFrame,多个参数合并
                    df = pd.DataFrame(one_pm[1],index=one_pm[0],columns=[pm,])
                    df_all=pd.concat([df_all,df],axis=1, ignore_index=False)
                else:
                    #文本格式
                    data=json.loads(one_pm)
                    data_t,data_v=zip(*data)
                    #导入DataFrame,多个参数合并
                    df = pd.DataFrame(data_v,index=data_t,columns=[pm,])
                    df_all=pd.concat([df_all,df],axis=1, ignore_index=False)
            if WFNAME is not None and len(WFNAME) >0:  
                #写csv文件
                df_all.to_csv(WFNAME)
                print('Data Write into "{}"'.format(WFNAME))
            else:
                #显示到屏幕
                #pd.set_option('display.max_rows', None)
                pd.set_option('display.min_rows', 30)
                print(df_all)

    print('mem:',sysmem())
    datafile.close()
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
    print('   -l, --paramlist           列出所有的参数。')
    print(' * -p, --param  VRTG,GW      获取指定的参数内容。多个参数用逗号分隔,中间不要有空格。')
    print('   -w out/xxx.dat            把 -p 挑选的参数,压缩/不压缩写入单文件"out/xxx.dat"')
    print('   -w out/xxx.csv            把 -p 挑选的参数,写入csv文件"out/xxx.csv"')
    print('   -w out/xxx.csv.gz         把 -p 挑选的参数,写入压缩的csv文件"out/xxx.csv.gz"')
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
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hw:lf:p:',['help','file=','paramlist','param='])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    WFNAME=None
    PARAMLIST=False
    PARAM=[]
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-f','--file'):
            FNAME=value
        elif op in('-w',):
            WFNAME=value
        elif op in('-l','--paramlist',):
            PARAMLIST=True
        elif op in('-p','--param',):
            if value.find(',')>0:
                PARAM=value.split(',')
            else:
                PARAM.append(value)
    if len(args)>0:  #命令行剩余参数
        FNAME=args[0]  #只取第一个
    if FNAME is None:
        usage()
        exit()
    if os.path.isfile(FNAME)==False:
        print(FNAME,'Not a file')
        exit()

    main()

