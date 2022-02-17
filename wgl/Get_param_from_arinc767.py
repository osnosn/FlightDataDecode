#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
读取 CPL 原始数据。
  --------------------------
 Boeing787, ARINC 767, 
    每个frame的头部是 header，header包含5个内容：
      Sync word (2bytes):  0xEB90 
      Frame length: total size of the frame, up to 2048 bytes(include header and trailer) 16bits
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
      ARINC CHARACTERISTIC 767
   ENHANCED AIRBORNE FLIGHT RECORDER
     Published: November 22, 2006

      ARINC CHARACTERISTIC 767-1
   ENHANCED AIRBORNE FLIGHT RECORDER
     Published: May 29, 2009

   EAFR(Enhanced Airborne Flight Recorder)
   FRED(Flight Recorder Electronic Documentation) 用于描述/定义记录在EAFR中的内容和格式的文档 (ARINC 647A)

   CNS/ATM Frame Format
   Frame 格式
      ----Header---
     2bytes 0xEB90
     2bytes frame length in bytes
     4bytes Time tag, Count of milliseconds since start of recording.
     1bytes Frame Type, Fixed at "10" for Buld Data Frame.
     1bytes Frame ID
      ----Frame data---
     xbytes Frame Data
      ----Trailer--
     2bytes Frame Type+Frame ID
      -------------
    * All numbers are stored in BigEndian order.
    * FrameID:0x01=TIS-B, 0x02=FIS-B, 0x03=ADS-B, 0x04=Datalink
    * FrameLength,Total frame length including header,trailer and data field. Max size is 8kbytes.
    * AFDX message payload padded with "1" for byte alignment.
   -----------------------
    FRAME BASED FLIGHT DATA RECORDING FORMAT
   The parameter are packed into the frame in the order specified in the Parameter Description. The fraame is padded with extra bits to the next byte boundary.The Frame Length field should be used to determine the end of the frame since extra space may be include in the rame for unused parameters or opaque data.

   For EAFR Flight Data recording,
   Frame 格式
      ----Header---
     2bytes 0xEB90
     2bytes frame length in bytes. 14-2048bytes.
     4bytes Time tag, Count of milliseconds since start of recording.
     1bytes Frame Type, Fixed at "0".(Uncompressed Fixed Frame)
     1bytes Frame ID, 1-255 (1,2 are reserved)
      ----Frame data---
     xbytes Frame Data
      ----Trailer--
     1bytes Frame Type, 0x00
     1bytes Frame Frame ID, 1-255
      -------------
    * All numbers are stored in BigEndian order.
    * FrameID:0x01=TIS-B, 0x02=FIS-B, 0x03=ADS-B, 0x04=Datalink
    * FrameLength,Total size of the frame,in bytes,including header,trailer and data field.
    * Frame Type can be combined with Frame ID, resulting in 16 bites for Frame ID.
    * Time would wrap to zero if a recording session lasted 49 days. This is not permitted by this standard.
    * Frames must contain at least one parameter.
   -----------------------
    Standard Documentary Data Frame Format
    Frame ID =1 的 Frame 格式
      ----Header---
     2bytes 0xEB90
     2bytes frame length in bytes. 140
     4bytes Time tag,
     1bytes Frame Type, 0
     1bytes Frame ID,   1
      ----Frame data---
     8char  "647X-XX",Identifies the standart that the Application format.
     32char "905-E2485-00 Rev B"(padding with spaces omitted for clarity),Identifies the standart that the Application format.
     8char  "N123ZZ",Aircraft tail number.
     64char  "Honeywell hardware 967-0212-002 software 998-1111-511"(paddig with spaces omitted for clarity),FDAU make and part number.
     16char  "YYYY/MM/DD-HH:MM",Date and Time from aircraft clock source.HH is 24 hour time referenced to UTC.
      ----Trailer--
     1bytes Frame Type, 0
     1bytes Frame Frame ID, 1
      -------------
    Mark-Time Frames
    Frame ID =2 的 Frame 格式
      ----Header---
     2bytes 0xEB90
     2bytes 32 ,frame length in bytes.
     4bytes Time tag,
     1bytes Frame Type, 0
     1bytes Frame ID,   2
      ----Frame data---
     2bytes (1-65535) Recording Session Number.
     16char  "YYYY/MM/DD-HH:MM",Date and Time from aircraft clock source.HH is 24 hour time referenced to UTC.
     2bytes (1 or 2) EAFR ID.
      ----Trailer--
     1bytes Frame Type, 0
     1bytes Frame Frame ID, 2
      -------------
   The SFDR recording format is base on Frames, which consist of on ordered set of Parameters and an associated Frame Label and Time Stamp. Frames can be recorded at any desired frequency, either periodic or event driven.典型的周期是以2的幂(1hz,2hz,4hz...),但可以使用任意周期,从100hz到1/3600hz(1/hour). During playback, the frames are aligned in time using their time stamps.
   相同周期的参数，放入相同的Frame中。每个单个Frame有自己特定的周期。
   Parameters can be any length(from 1 to 32bits), and they are packed into the frame to efficiently use recording memory space. However, it is typically desirable to pad the frames to the nearest word length so that the allways start on a word boundary.

   example frame
      Frame:
    ____________________________________
   |Frame Header|Paramters|Frame Trailer| 
   |------------------------------------| 
      Frame Header:
    ________________________________________________________
   |Sync Pattern|Frame Length|Time Stamp|Frame Type|Frame ID| 
   |--------------------------------------------------------|
      Parameters:
    _______________________________________________________________
   |1|2|3|4|5|6|7|8|1|2|3|4|5|6|7|8|1|2|3|4|5|6|7|8|1|2|3|4|5|6|7|8| 
   |    Baro Altitude                |   Airspeed        |D|D| Pad | 
   |---------------------------------------------------------------|
 --------------------------------------------------------------
  实际读文件: 每个FrameID相同的Frame的length是相同的。

"""
#import struct
#from datetime import datetime
import zipfile
import psutil   #非必须库
#from io import BytesIO

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
    frame_pos, frame_size=find_SYNC(buf, ttl_len, frame_pos, sync767)
    if frame_pos >= ttl_len -2:
        print('ERR,SYNC1 not found.',flush=True)
        raise(Exception('ERR,SYNC1 not found.'))
    
    #----------验证同步字位置，header内容, trailer内容-----------
    ii=0    #计数
    pm_list=[] #参数列表
    pm_sec=0.0   #参数的时间轴,秒数
    ttl_data_size=0
    while True:
        #----------验证同步字,并返回size--------
        frame_pos2 = frame_pos
        frame_pos, frame_size=find_SYNC(buf, ttl_len, frame_pos, sync767) #同时返回size
        if frame_pos>=ttl_len -2:
            #-----超出文件结尾，退出-----
            break
        if frame_pos > frame_pos2:
            print('==>ERR, miss SYNC at x%X, Refound at x%X'%(frame_pos2, frame_pos))

        #----------frame size-------
        #frame_size=getWord(buf,frame_pos+2) #size

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

        #----------trailer: type & id--------
        frame_tail=getWord(buf,frame_pos+frame_size-2) # type & id
        frame_tail_type= frame_tail >> 8
        frame_tail_id = frame_tail & 0xff
        if frame_id != frame_tail_id or frame_type != frame_tail_type:
            print('==>ERR, type or id in header & trailer is not same.')
        if frame_type != 0:
            print('==>ERR, type is NOT 0.')
        print('Frame id:   %X' % frame_id)

        #----------frame data size--------
        print('Frame data size: %d'% (frame_size,) )

        frame_pos += frame_size
    if frame_pos>=ttl_len -2:
        print('End of file.')

    div4,mod4=divmod(ttl_data_size,4)
    print('Total data size: %d, div4:%d, mod4:%d'% (ttl_data_size, div4, mod4) )

    print('mem:',sysmem())

def find_SYNC(buf, ttl_len, frame_pos, sync767):
    while frame_pos<ttl_len -2:  #寻找frame开始位置
        frame_size=getWord(buf,frame_pos+2) #size
        if getWord(buf,frame_pos) == sync767 and getWord(buf,frame_pos+frame_size) == sync767:
            #当前位置有同步字,加上size之后的位置,也有同步字
            #print('==>Mark,x%X'%(frame_pos,))
            break
        frame_pos +=1
    return frame_pos, frame_size

def getWord(buf,pos):
    '''
    读取两个字节，拼为一个16 bit word。高位在前。bigEndian,High-byte first.
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
    print(u'   命令行工具。')
    print(u' 读取,来源于PC卡的原始数据文件。尝试解码一个参数。')
    print(sys.argv[0]+' [-h|--help]')
    print('   -h, --help     print usage.')
    print('   -f, --file=    "....wgl.zip" filename')
    #print('   -w xxx.dat     写入文件"xxx.dat"')
    print(u'\n               author:南方航空,LLGZ@csair.com')
    print(u' 认为此项目对您有帮助，请发封邮件给我，让我高兴一下.')
    print(u' If you think this project is helpful to you, please send me an email to make me happy.')
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

