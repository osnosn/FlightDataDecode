#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
 读取 wgl中 raw.tag 。可以得到机尾号，用于确定解码库。其他没什么用。
    author: osnosn@126.com
 修改 raw.tag 中的日期,用于脱敏处理。
"""
import struct
from datetime import datetime  #非必须库
import zipfile

def main():
    global FNAME,DUMPDATA

    try:
        fzip=zipfile.ZipFile(FNAME,'r') #打开zip文件
    except zipfile.BadZipFile as e:
        print('ERR,FailOpenZipFile',e,FNAME,flush=True)
        raise(Exception('ERR,FailOpenZipFile'))
    filename_zip='raw.tag'
    buf=fzip.read(filename_zip)
    fzip.close()

    '''
    fp=open(FNAME,'rb')
    buf=fp.read()
    fp.close()
    '''

    ss=struct.Struct('8s')
    ttl_size=len(buf)
    #print(buf[12:20])
    #print(buf[32:40])
    #print(ss.unpack_from(buf[12:20]))
    if WNAME is not None:
        wfp=open(WNAME,'wb')
    for ii in range(0,ttl_size,20):
        #print(buf[ii:ii+20])
        tm=struct.unpack('<l',buf[ii:ii+4])[0]
        print(datetime.utcfromtimestamp(tm).strftime('%Y-%m-%d_%H:%M:%S'),end=',\t')
        #----------根据需要，手工修改这行代码------------
        tm=tm-2*(365*24*3600)-11*(24*3600) #修改日期
        print(datetime.utcfromtimestamp(tm).strftime('%Y-%m-%d_%H:%M:%S'),end=',\t')
        #----------根据需要，手工修改这行代码------------
        tm2=struct.unpack('<l',buf[ii+4:ii+8])[0]
        #print(datetime.utcfromtimestamp(tm2).strftime('%Y-%m-%d_%H:%M:%S'),end=',\t')
        print(tm2,end=',\t')
        tm3=struct.unpack('<l',buf[ii+8:ii+12])[0]
        #print(datetime.utcfromtimestamp(tm3).strftime('%Y-%m-%d_%H:%M:%S'),end=',\t')
        print(tm3,end=',\t')
        print(buf[ii+12:ii+20].strip(b'\0').decode(),end=',\t')
        print()
        if WNAME is not None:
            wfp.write(struct.pack('<l',tm))
            wfp.write(struct.pack('<l',tm2))
            wfp.write(struct.pack('<l',tm3))
            wfp.write(buf[ii+12:ii+20])

    if WNAME is not None:
        wfp.close()




import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'   命令行工具。')
    print(u' 读取 wgl中 raw.tag 。可以得到机尾号，用于确定解码库。其他没什么用。')
    print(sys.argv[0]+' [-h|--help]')
    print('   -h, --help     print usage.')
    print('   -f, --file=    "....wgl.zip" filename')
    print('   -W raw.tag     write "raw.tag" ,用于脱敏处理')
    print(u'\n               author: osnosn@126.com')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hvdf:W:',['help','file=','pd'])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    WNAME=None
    DUMPDATA=False
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-f','--file'):
            FNAME=value
        elif op in('-W',):
            WNAME=value
        elif op in('-d',):
            DUMPDATA=True
    if len(args)>0:  #命令行剩余参数
        FNAME=args[0]  #只取第一个
    if FNAME is None:
        usage()
        exit()
    if os.path.isfile(FNAME)==False:
        print(FNAME,'Not a file')
        exit()

    main()

