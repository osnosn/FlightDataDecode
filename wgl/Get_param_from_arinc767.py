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
   此文档的样例，可以从 "https://www.aviation-ia.com/support-files/647a-1" 获取。

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
   The parameter are packed into the frame in the order specified in the Parameter Description. The frame is padded with extra bits to the next byte boundary.The Frame Length field should be used to determine the end of the frame since extra space may be include in the rame for unused parameters or opaque data.

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
import config_vec as conf
import read_air as AIR
import read_frd as FRD
import read_par as PAR
#from io import BytesIO

class DATA:
    '用来保存配置参数的类'
    pass

def main():
    global FNAME,WFNAME,DUMPDATA
    global DATAVER

    print('mem0:',sysmem())

    reg=getREG(FNAME)
    if len(DATAVER)<1:
        air=getAIR(reg)
        dataver=air[0]
    else:
        dataver=DATAVER

    print('Registration:',reg,'DataVer:',dataver)
    print()

    frad=getFRAD_config(dataver)

    print()
    for iid in frad:
        if iid.endswith('_bits'):
            continue
        frad_bits=frad[str(iid)+'_bits']
        print('FrameID:{},\t参数个数:{},\t 总bit数:{},\t字节数:{}'.format(iid, len(frad[iid]), frad_bits['ttl_bits'], frad_bits['ttl_bits']/8.0))
        print('           \t dword:{},\t  剩余bits:{},\t 字节数:{}'.format(frad_bits['dword'], frad_bits['dbits'], frad_bits['dword']*4+frad_bits['dbits']/32.0))
        pm_bytes=frad_bits['word']*2
        pm_bytes +=frad_bits['bits']/16.0
        print('           \t   word:{},\t   剩余bits:{},\t  字节数:{}'.format(frad_bits['word'], frad_bits['bits'], pm_bytes))
        #ii=0
        #for row in frad[iid]:
        #    if ii>2: break
        #    ii+=1
        #    print(row)

    print('mem conf end:',sysmem())

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
    frameIDs={}  #记录各个frameid 的datasize
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
            #print('ERR,time 3')
        else:
            MS_str= '%02d'% (MS/10)
        #print('Frame time1: %02d:%02d:%02d.%s'%(HH,MM,SS,MS_str))

        #----------type & id--------
        frame_id=getWord(buf,frame_pos+8) # type & id
        frame_type= frame_id >> 8
        frame_id &= 0xff

        # if ID==1, read it
        if frame_type==0 and frame_id==1 and frame_size==140:
            str2=''  #临时变量
            for num in range(0,8,2):
                word=getWord(buf,frame_pos+10+num)
                str2 += chr(word >> 8)
                str2 += chr(word & 0xff)
            print('Format:',str2)
            str2=''  #临时变量
            for num in range(0,32,2):
                word=getWord(buf,frame_pos+18+num)
                str2 += chr(word >> 8)
                str2 += chr(word & 0xff)
            print('      :',str2)
            str2=''  #临时变量
            for num in range(0,8,2):
                word=getWord(buf,frame_pos+50+num)
                str2 += chr(word >> 8)
                str2 += chr(word & 0xff)
            print('  Tail:',str2)
            str2=''  #临时变量
            for num in range(0,64,2):
                word=getWord(buf,frame_pos+58+num)
                str2 += chr(word >> 8)
                str2 += chr(word & 0xff)
            print('  FDAU:',str2)
            str2=''  #临时变量
            for num in range(0,16,2):
                word=getWord(buf,frame_pos+122+num)
                str2 += chr(word >> 8)
                str2 += chr(word & 0xff)
            print('UTC Time:',str2)

        #----------trailer: type & id--------
        frame_tail=getWord(buf,frame_pos+frame_size-2) # type & id
        frame_tail_type= frame_tail >> 8
        frame_tail_id = frame_tail & 0xff
        if frame_id != frame_tail_id or frame_type != frame_tail_type:
            print('==>ERR, type or id in header & trailer is not same. Type:%d != %d or ID:%d != %d'% (frame_type, frame_tail_type, frame_id, frame_tail_id ))
        if frame_type != 0:
            print('==>ERR, type is NOT 0.')
        #print('Frame id:   %X' % frame_id)

        #----------frame data size--------
        #print('Frame data size: %d'% (frame_size,) )

        #------记录各个frame id 的 frame_size ----
        if frame_id not in frameIDs:
            frameIDs[frame_id]=frame_size
        else:
            if frameIDs[frame_id] != frame_size:
                print('frame id %d size NOT same.%d != %d' % (frame_id,frameIDs[frame_id], frame_size))

        frame_pos += frame_size
    if frame_pos>=ttl_len -2:
        print('End of file.')

    #div4,mod4=divmod(ttl_data_size,4)
    #print('Total data size: %d, div4:%d, mod4:%d'% (ttl_data_size, div4, mod4) )

    #------打印各个frame id 的 frame_size ----
    print('  ','Frame','Data',sep='\t')
    print('ID','Size','Size(Byte)',sep='\t')
    for kk in frameIDs:
        print(kk,frameIDs[kk],frameIDs[kk]-10,sep='\t')

    print('mem:',sysmem())

def find_SYNC(buf, ttl_len, frame_pos, sync767):
    frame_size=0
    while frame_pos<ttl_len -2:  #寻找frame开始位置
        frame_size=getWord(buf,frame_pos+2) #size
        if getWord(buf,frame_pos) == sync767 and \
                (frame_pos+frame_size>=ttl_len or getWord(buf,frame_pos+frame_size) == sync767 ):
            #当前位置有同步字,加上size之后的位置,也有同步字,或者是文件结尾
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
        print('Read out of range at %X/%X'%(pos,ttl))
        #raise(Exception)
        return 0
    else:
        return ((buf[pos] << 8 ) | buf[pos +1] )

def getPAR(dataver,param):
    '''
    获取参数在arinc429的32bit word中的位置配置
    挑出有用的,整理一下,返回
       author:南方航空,LLGZ@csair.com
    '''
    global DATA
    if not hasattr(DATA,'par') or DATA.par is None:
        DATA.par=PAR.read_parameter_file(dataver)
    if DATA.par is None or len(DATA.par.index)<1:
        return {}
    param=param.upper()  #改大写
    tmp=DATA.par
    tmp2=tmp[ tmp.iloc[:,0]==param ].copy(deep=True) #dataframe ,找到对应参数的记录行
    #pd.set_option('display.max_columns',78)
    #pd.set_option('display.width',156)
    #print('=>',type(tmp2))
    #print(tmp2)
    if len(tmp2.index)<1:
        return {}
    else:
        tmp_part=[]
        if isinstance(tmp2.iat[0,36], list):
            #如果有多个部分的bits的配置, 组合一下
            for ii in range(len(tmp2.iat[0,36])):
                tmp_part.append({
                        'id'  :int(tmp2.iat[0,36][ii]),  #Digit ,顺序标记
                        'pos' :int(tmp2.iat[0,37][ii]),  #MSB   ,开始位置
                        'blen':int(tmp2.iat[0,38][ii]),  #bitLen,DataBits,数据长度
                        })
        return {
                'ssm'    :int(tmp2.iat[0,5]) if len(tmp2.iat[0,5])>0 else -1,   #SSM Rule , (0-15)0,4 
                'signBit':int(tmp2.iat[0,6]) if len(tmp2.iat[0,6])>0 else -1,   #bitLen,SignBit  ,符号位位置
                'pos'   :int(tmp2.iat[0,7]) if len(tmp2.iat[0,7])>0 else -1,   #MSB  ,开始位置
                'blen'  :int(tmp2.iat[0,8]) if len(tmp2.iat[0,8])>0 else -1,   #bitLen,DataBits ,数据部分的总长度
                'part'    :tmp_part,
                'type'    :tmp2.iat[0,2],    #Type(BCD,CHARACTER)
                'format'  :tmp2.iat[0,17],    #Display Format Mode (DECIMAL,ASCII)
                'Resol'   :tmp2.iat[0,12],    #Computation:Value=Constant Value or Resol=Coef A(Resolution) or ()
                'A'       :tmp2.iat[0,29] if tmp2.iat[0,29] is not None else '',    #Coef A(Res)
                'B'       :tmp2.iat[0,30] if tmp2.iat[0,30] is not None else '',    #Coef b
                'format'  :tmp2.iat[0,25],    #Internal Format (Float ,Unsigned or Signed)
                }

def getFRAD_config(dataVer):
    if hasattr(DATA,'frad') and DATA.frad is not None:
        return DATA.frad

    frd=getFRD(dataVer)
    '''
    #打印内容
    print(frd.keys())
    for row in frd['2']:
        print(row)
    ii=0
    for row in frd['3']:
        ii+=1
        if ii>3:break
        print(row)
    ii=0
    for row in frd['4']:
        ii+=1
        if ii>3:break
        print(row)
    '''

    conf={}
    ii=0
    for row in frd['2']:
        #if ii>1: break
        ii+=1
        if row[0].startswith('Frame'): #跳过第一行,标题行 
            continue
        frame_id=row[0]
        #print('====== %s ========' % frame_id)

        if frame_id not in conf:
            conf[frame_id]=[]
        if str(frame_id)+'_bits' not in conf:
            conf[str(frame_id)+'_bits']={
                    'dword':0,
                    'dbits':0,
                    'word':0,
                    'bits':0,
                    'ttl_bits':0,
                    }

        jj=0
        for pm_id in range(1,int(row[4])+1):
            #if jj>12: break
            jj+=1

            buf_map=list(map(lambda x: frame_id == x[0] and pm_id==int(x[1]) ,frd['3'])) #查找匹配
            if buf_map.count(True)>1:
                print('=>ERR, find frd_3 >1.')
            idx3=buf_map.index(True) #获取索引
            pm_long_name=frd['3'][idx3][2]

            buf_map=list(map(lambda x: pm_long_name==x[0] ,frd['4'])) #查找匹配
            if buf_map.count(True)>1:
                print('=>ERR, find frd_3 >1.')
            idx4=buf_map.index(True) #获取索引
            pm_name=frd['4'][idx3][1]
            #print(pm_id, idx3,idx4, frd['3'][idx3], frd['4'][idx4])

            par=getPAR(dataVer,pm_name)
            #print(par)
            if len(par)<1:
                #print('=>ERR,par NOT found.',pm_id, idx3,idx4, frd['3'][idx3], frd['4'][idx4])
                print('=>ERR,par NOT found.', frd['3'][idx3], frd['4'][idx4])
                continue

            pm_bits=0
            if par['signBit']>0:
                pm_bits +=1
                #print('==>INFO, signBit',par['signBit'],frd['4'][idx4])  #有挺多参数,有符号位
            if par['blen']>0:
                pm_bits +=par['blen']

            conf[str(frame_id)+'_bits']['ttl_bits'] +=pm_bits

            #按填满一个 dword 计算
            if conf[str(frame_id)+'_bits']['dbits'] + pm_bits >32:
                conf[str(frame_id)+'_bits']['dbits'] = pm_bits
                conf[str(frame_id)+'_bits']['dword'] +=1
            else:
                conf[str(frame_id)+'_bits']['dbits'] += pm_bits

            #按填满一个 word 计算
            if conf[str(frame_id)+'_bits']['bits'] + pm_bits >16:
                conf[str(frame_id)+'_bits']['bits'] = pm_bits
                conf[str(frame_id)+'_bits']['word'] +=1
            else:
                conf[str(frame_id)+'_bits']['bits'] += pm_bits

            if conf[str(frame_id)+'_bits']['bits'] >16:
                conf[str(frame_id)+'_bits']['bits'] -= 16
                conf[str(frame_id)+'_bits']['word'] +=1

            if par['pos'] != par['blen']:
                print('==>INFO, param POS != BLEN')

            conf_one={  #临时变量
                    'seq':pm_id,
                    'longName':pm_long_name,
                    'name':pm_name,
                    }
            conf_one.update(par)
            conf[frame_id].append(conf_one)


    DATA.par=None  #没用了
    DATA.frd=None  #没用了
    DATA.frad=conf
    return conf

def getFRD(dataver):
    '''
    获取参数在arinc767的32bit word中的位置配置
    挑出有用的,整理一下,返回
       author:南方航空,LLGZ@csair.com
    '''
    global PARAMLIST
    global DATA

    if not hasattr(DATA,'frd') or DATA.frd is None:
        DATA.frd=FRD.read_parameter_file(dataver)
    if DATA.frd is None:
        return {}

    #if PARAMLIST:
    return DATA.frd

    ret2=[]  #for regular
    ret3=[]  #for superframe
    ret4=[]  #for superframe pm
    if len(param)>0:
        param=param.upper() #改大写
        #---find regular parameter----
        tmp=DATA.frd['2']
        tmp=tmp[ tmp.iloc[:,0]==param].copy()  #dataframe
        #print(tmp)
        if len(tmp.index)>0:  #找到记录
            for ii in range( len(tmp.index)):
                tmp2=[
                    tmp.iat[ii,1],   #part(1,2,3),会有多组记录,对应返回多个32bit word(完成)
                    tmp.iat[ii,2],   #recordRate
                    tmp.iat[ii,3],   #subframe
                    tmp.iat[ii,4],   #word
                    tmp.iat[ii,5],   #bitOut
                    tmp.iat[ii,6],   #bitLen
                    tmp.iat[ii,7],   #bitIn
                    tmp.iat[ii,12],  #Occurence No
                    tmp.iat[ii,8],   #Imposed,Computed
                    ]
                ret2.append(tmp2)
        #---find superframe parameter----
        tmp=DATA.frd['4']
        tmp=tmp[ tmp.iloc[:,0]==param].copy()  #dataframe
        #print(tmp)
        if len(tmp.index)>0:  #找到记录
            superframeNo=tmp.iat[0,3]
            for ii in range( len(tmp.index)):
                tmp2=[
                    tmp.iat[ii,1],   #part(1,2,3),会有多组记录,对应返回多个32bit word(完成)
                    tmp.iat[ii,2],   #period
                    tmp.iat[ii,3],   #superframe no
                    tmp.iat[ii,4],   #Frame
                    tmp.iat[ii,5],   #bitOut
                    tmp.iat[ii,6],   #bitLen
                    tmp.iat[ii,7],   #bitIn
                    tmp.iat[ii,10],  #resolution
                    ]
                ret4.append(tmp2)
            tmp=DATA.frd['3']
            tmp=tmp[ tmp.iloc[:,0]==superframeNo].copy()  #dataframe
            for ii in range( len(tmp.index)):
                tmp2=[
                    tmp.iat[ii,0],   #superframe no
                    tmp.iat[ii,1],   #subframe
                    tmp.iat[ii,2],   #word
                    tmp.iat[ii,3],   #bitOut
                    tmp.iat[ii,4],   #bitLen
                    tmp.iat[ii,5],   #superframe couter 1/2
                    ]
                ret3.append(tmp2)


    return { '1':
            [
                DATA.frd['1'].iat[1,1],  #Word/Sec
                DATA.frd['1'].iat[1,2],  #sync length
                DATA.frd['1'].iat[1,3],  #sync1
                DATA.frd['1'].iat[1,4],  #sync2
                DATA.frd['1'].iat[1,5],  #sync3
                DATA.frd['1'].iat[1,6],  #sync4
                DATA.frd['1'].iat[1,7],  #subframe, [superframe counter]
                DATA.frd['1'].iat[1,8],  #word
                DATA.frd['1'].iat[1,9],  #bitOut
                DATA.frd['1'].iat[1,10], #bitLen
                DATA.frd['1'].iat[1,11], #Value in 1st frame (0/1)
                ],
             '2':ret2,
             '3':ret3,
             '4':ret4,
            }

def getAIR(reg):
    '''
    获取机尾号对应解码库的配置。
    挑出有用的,整理一下,返回
       author:南方航空,LLGZ@csair.com
    '''
    reg=reg.upper()
    df_flt=AIR.csv(conf.aircraft)
    tmp=df_flt[ df_flt.iloc[:,0]==reg].copy()  #dataframe
    if len(tmp.index)>0:  #找到记录
        return [tmp.iat[0,12],   #dataver
                tmp.iat[0,13],   #dataver
                tmp.iat[0,16],   #recorderType
                tmp.iat[0,16]]   #recorderType
    else:
        return [0,0,0,0]

def getREG(fname):
    '''
    从zip文件名中，找出机尾号
       author:南方航空,LLGZ@csair.com
    '''
    basename=os.path.basename(fname)
    tmp=basename.strip().split('_',1)
    if len(tmp[0])>6: #787的文件名没有用 _ 分隔
        return tmp[0][:6]
    elif len(tmp[0])>0:
        return tmp[0]
    else:
        return ''

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
    print('   -h, --help                print usage.')
    print('   -v, --ver 787151          指定DataVer')
    print('   -f, --file="....wgl.zip"     filename')
    #print('   -w xxx.dat               写入文件"xxx.dat"')
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
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hv:w:df:',['help','file=','ver=',])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    WFNAME=None
    DUMPDATA=False
    DATAVER=''
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-f','--file'):
            FNAME=value
        elif op in('-v','--ver'):
            DATAVER=value
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

