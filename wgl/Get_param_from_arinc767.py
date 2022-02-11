#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
读取 CPL 原始数据。
  --------------------------
 Boeing787, ARINC 767, 
    每个frame的头部是 header，header包含5个内容：
      Sync word (2bytes):  0xEB90 
      Frame length: total size of the frame, up to 2048 bytes(include header and tailer) 16bits
      Time Stamp: "c time" field of 32bits 
      Frame Type/ID attributes: 8bits frame type can either be used for separate classifications or combined with the 1-byte Frame ID for identification purposes.
     For a given Frame ID, the Parameters are recorded, 
  and the necessary bits for each are used. If certain 
  parameter rates result in the Frame Length to be 
  exceeded, a second frame at the same rate is used 
  (multiple frames are expected for the most common 
  recording rate of 1 Hz). 
      The Frame Trailer again contains Header Frame 
   Type/ID fields, and is used if difficulties existed in 
   recording the frame; if a problem transpired in 
   recording the Frame Header, the Trailer can be used to 
   process the parameters. 
  --------------------------
  实际读取数据。header 和 tailer 中的 type,id 都是一一对应。
     timestamp 似乎是 毫秒。
     但, 所有的 type=0, id 有 1,3,4,5,7,8,10,11 这几种。
"""
#import struct
#from datetime import datetime
import zipfile
import psutil
from io import BytesIO

def main():
    global FNAME,WFNAME,DUMPDATA

    print('mem:',sysmem())

    #----------打开zip压缩文件-----------
    try:
        fzip=zipfile.ZipFile(FNAME,'r') #打开zip文件
    except zipfile.BadZipFile as e:
        print('ERR,FailOpenZipFile',e,FNAME,flush=True)
        raise(Exception('ERR,FailOpenZipFile'))
    names=fzip.namelist()
    buf=fzip.read(names[0]) #读取第一个文件内容,放入内存
    fzip.close()

    sync767=0xEB90  #同步字
    ttl_len=len(buf)

    #----------寻找起始位置-----------
    frame_pos=0  #frame开始位置,字节指针
    while frame_pos<ttl_len -2:  #寻找frame开始位置
        word=getWord(buf,frame_pos)
        if word == sync767:
            print('==>Mark,x%X'%(frame_pos,))
            break
        frame_pos +=1
    if frame_pos >= ttl_len -2:
        print('ERR,SYNC1 not found.',flush=True)
        raise(Exception('ERR,SYNC1 not found.'))
    
    #----------验证同步字位置，header内容, tailer内容-----------
    ii=0    #计数
    pm_list=[] #参数列表
    pm_sec=0.0   #参数的时间轴,秒数
    while frame_pos<ttl_len -2:
        #----------同步字--------
        sync_word=getWord(buf,frame_pos) #当前位置的同步字
        if sync_word == sync767:
            print('==>Found sync767.%X,x%X'%(sync_word,frame_pos))
        else:
            print('==>notFound sync767.%X,x%X'%(sync_word,frame_pos))
            break

        #----------frame size-------
        frame_size=getWord(buf,frame_pos+2) #size
        print('Size: %d(%X)'%(frame_size,frame_size))

        #----------timestamp--------
        tm=getWord(buf,frame_pos+4) #timestamp
        tm=(tm <<16) | getWord(buf,frame_pos+6) #timestamp
        SS,MS = divmod(tm,1000)
        MM,SS = divmod(SS,60)
        HH,MM = divmod(MM,60)
        if MS % 10 >0:
            MS_str= '%03d'% MS
            print('ERR,time 3')
        else:
            MS_str= '%02d'% (MS/10)
        print('Frame time1: %02d:%02d:%02d.%s'%(HH,MM,SS,MS_str))
        #print('Frame time2: %d(%X)'%(tm,tm))

        #----------type & id--------
        frame_id=getWord(buf,frame_pos+8) # type & id
        frame_type= frame_id >> 8
        frame_id &= 0xff
        print('Frame type: %X' % frame_type)
        print('Frame id:   %X' % frame_id)

        #----------tailer: type & id--------
        frame_tail=getWord(buf,frame_pos+frame_size-2) # type & id
        frame_type= frame_tail >> 8
        frame_id = frame_tail & 0xff
        print('Frame tail type: %X' % frame_type)
        print('Frame tail id:   %X' % frame_id)

        #----------frame data size--------
        data_size=frame_size -10
        print('Frame data size: %d'% data_size)

        frame_pos += frame_size
    if frame_pos>=ttl_len -2:
        print('End of file.')

    print('mem:',sysmem())

def getWord(buf,pos):
    '''
    读取两个字节，拼为一个16 bit word
       author:南方航空,LLGZ@csair.com
    '''
    #print(type(buf), type(buf[pos]), type(buf[pos+1])) #bytes, int, int

    ttl=len(buf)  #读数据的时候,开始位置加上偏移，可能会超限
    if pos+1 >= ttl:
        print('Read out of range.')
        return 0
    else:
        return ((buf[pos] << 8 ) | buf[pos +1] )

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
    print(u' 读取 wgl中 raw.dat 。把12bit的frame展开为16bit，高4bit填0。方便下一步处理。')
    print(u' 命令行工具。')
    print(sys.argv[0]+' [-h|--help] [-f|--file]  ')
    print('   -h, --help     print usage.')
    print('   -f, --file=    "....wgl.zip" filename')
    #print('   -w xxx.dat     写入文件"xxx.dat"')
    print(u'\n               author:南方航空,LLGZ@csair.com')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hw:df:',['help','file=',])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    WFNAME=None
    DUMPDATA=False
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-f','--file'):
            FNAME=value
        elif op in('-w',):
            WFNAME=value
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

