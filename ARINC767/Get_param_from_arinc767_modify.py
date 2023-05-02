#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
读取 CPL 原始数据。
支持修改原始数据中的内容，用于脱敏处理
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
import struct
import zipfile
import gzip
import config_vec as conf
import read_air as AIR
import read_frd as FRD
import read_par as PAR

class ARINC767():
    '''
    从 ARINC 767 格式文件中，获取参数
    支持修改原始数据中的内容，用于脱敏处理
    '''
    def __init__(self,fname):
        '''
        用来保存配置参数的实例变量
        '''
        self.write_raw_dat=None
        self.air=None
        self.frd=None
        self.frd_dataver=-1
        self.par=None
        self.qar=None
        self.qar_filename=''
        if len(fname)>0:
            self.qar_file(fname)
    def close(self):
        '清除,保留的所有配置和数据'
        self.air=None
        self.frd=None
        self.frd_dataver=-1
        self.par=None
        self.qar=None
        self.qar_filename=''
    def dataVer(self):
        '''
        获取当前文件的 DataVer
        '''
        return self.frd_dataver
    def qar_file(self,qar_filename):
        #----------打开zip压缩文件-----------
        if self.qar is None or self.qar_filename != qar_filename:
            try:
                fzip=zipfile.ZipFile(qar_filename,'r') #打开zip文件
            except zipfile.BadZipFile as e:
                print('==>ERR,FailOpenZipFile',e,qar_filename,flush=True)
                raise(Exception('ERR,FailOpenZipFile,%s'%qar_filename))
            filename_zip=fzip.namelist()
            cpl_map=list(map(lambda x: x.find('CPL')>=0 ,filename_zip))
            if cpl_map.count(True)>0:
                cpl_idx=cpl_map.index(True) #获取索引
                self.qar=fzip.read(filename_zip[cpl_idx]) #读取 CPL文件 的内容,放入内存
                self.qar=bytearray(self.qar)  #可以被修改
                self.write_raw_dat=filename_zip[cpl_idx]
            else:
                print('ERR, arinc767 raw file NOT found')
            fzip.close()
            self.qar_filename=qar_filename
        self.readFRD()
        self.readPAR()


    def find_SYNC(self, buf, ttl_len, frame_pos, sync767):
        '''
        判断 frame_pos 位置，是否满足同步字特征。如果不满足, 继续寻找下一个起始位置
        '''
        frame_size=0
        while frame_pos<ttl_len -2:  #寻找frame开始位置
            frame_size=self.getWord(buf,frame_pos+2) #size,判断要使用，只能先取size
            if self.getWord(buf,frame_pos) == sync767 and \
                    (frame_pos+frame_size>=ttl_len or self.getWord(buf,frame_pos+frame_size) == sync767 ):
                #当前位置有同步字,加上size之后的位置,也有同步字,或者是文件结尾
                ## 应该判断trailer的 type&id 吻合，说明当前frame完整,即可返回。
                #print('==>Mark,x%X'%(frame_pos,))
                break
            frame_pos +=1
        return frame_pos, frame_size

    def data_file_info(self, DUMPDATA=False):
        '''
        根据配置，扫描原始文件，验证格式
           author:南方航空,LLGZ@csair.com
        '''
        frd=self.readFRD()
        if frd is None:
            print('Empty dataVer.',flush=True)
            return
        frad=self.getFRD()

        print('-----根据配置文件的内容，用整体计算，或用DWORD计算,多出的bit和字节数量------')
        print('FrameID, 参数个数, 需要的总bit数, 需要的字节数  |  所需dword + 多出bits, 所需字节数,')
        for iid in frad:
            if iid.endswith('_bits'):
                continue
            frad_bits=frad[str(iid)+'_bits']
            print('{:>7}, {:8}, {:13}, {:12}  | '.format(iid, len(frad[iid]), frad_bits['ttl_bits'], frad_bits['ttl_bits']/8.0),end=' ')
            print('{:9} + {:<8}, {:10}'.format(frad_bits['dword'], frad_bits['dbits'], frad_bits['dword']*4+frad_bits['dbits']/32.0),end=' ')
            print(flush=True)

        #----------zip压缩文件内容-----------
        buf=self.qar
        if buf is None:
            print('ERR, arinc767 raw file NOT found')
            return []

        sync767=0xEB90  #同步字
        ttl_len=len(buf)

        #----------寻找起始位置-----------
        frame_pos=0  #frame开始位置,字节指针
        frame_pos, frame_size=self.find_SYNC(buf, ttl_len, frame_pos, sync767)
        if frame_pos >= ttl_len -2:
            print('ERR,SYNC1 not found.',flush=True)
            raise(Exception('ERR,SYNC1 not found.'))
        elif frame_pos>0:
            print('ERR,SYNC1 not at begin.',flush=True)

        #----------验证同步字位置，header内容, trailer内容-----------
        frameIDs={}  #记录各个frameid 的datasize
        ii=0    #计数
        #ttl_data_size=0  #没有使用
        while True:
            #----------验证同步字,并返回size--------
            frame_pos2 = frame_pos  #保存上一次的位置
            frame_pos, frame_size=self.find_SYNC(buf, ttl_len, frame_pos, sync767) #同时返回size
            if frame_pos>=ttl_len -2:
                #-----超出文件结尾，退出-----
                break
            if frame_pos > frame_pos2:
                print('==>ERR, miss SYNC at x%X, Refound at x%X'%(frame_pos2, frame_pos))

            #----------frame size-------
            #这里不需要了。sync已经读取size了。
            #frame_size=self.getWord(buf,frame_pos+2) #size

            #----------timestamp--------
            tm=self.getWord(buf,frame_pos+4) #timestamp
            tm=(tm <<16) | self.getWord(buf,frame_pos+6) #timestamp
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
            frame_id=self.getWord(buf,frame_pos+8) # type & id
            frame_type= frame_id >> 8
            frame_id &= 0xff

            # if ID==1, read it
            if frame_type==0 and frame_id==1 and frame_size==140:
                print('-------file header--------')
                str2=''  #临时变量
                for num in range(0,8,2):
                    word=self.getWord(buf,frame_pos+10+num)
                    str2 += chr(word >> 8)
                    str2 += chr(word & 0xff)
                print('    Format:    ',str2)
                str2=''  #临时变量
                for num in range(0,32,2):
                    word=self.getWord(buf,frame_pos+18+num)
                    str2 += chr(word >> 8)
                    str2 += chr(word & 0xff)
                print('          :    ',str2)
                str2=''  #临时变量
                for num in range(0,8,2):
                    word=self.getWord(buf,frame_pos+50+num)
                    str2 += chr(word >> 8)
                    str2 += chr(word & 0xff)
                print('      Tail:    ',str2, '               \x1b[45m<===\x1b[0m')
                str2=''  #临时变量
                for num in range(0,64,2):
                    word=self.getWord(buf,frame_pos+58+num)
                    str2 += chr(word >> 8)
                    str2 += chr(word & 0xff)
                print('      FDAU:    ',str2)
                str2=''  #临时变量
                for num in range(0,16,2):
                    word=self.getWord(buf,frame_pos+122+num)
                    str2 += chr(word >> 8)
                    str2 += chr(word & 0xff)
                print('  UTC Time:    ',str2, '       \x1b[45m<===\x1b[0m')
                print(flush=True)

            #----------trailer: type & id, 验证trailer是否正确--------
            frame_tail=self.getWord(buf,frame_pos+frame_size-2) # type & id
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
                rate_str=''
                # 查找frame_id 对应的rate说明
                for one_frd in frd['2']:
                    if str(frame_id) == one_frd[0]:
                        rate_str=one_frd[1]
                one_frame={'size':frame_size, 'time': ['%02d:%02d:%02d.%s'%(HH,MM,SS,MS_str), ], 'rate':rate_str }
                frameIDs[frame_id]=one_frame
            else:
                if frameIDs[frame_id]['size'] != frame_size:
                    print('frame id %d size NOT same.%d != %d' % (frame_id,frameIDs[frame_id], frame_size))
                frameIDs[frame_id]['time'].append('%02d:%02d:%02d.%s'%(HH,MM,SS,MS_str) )

            frame_pos += frame_size
        print('-----End of file. File scan finished.----')

        #------打印各个frame id 的 frame_size ----
        print('          (Bytes)    (Bytes)   ')
        print('FrameID, FrameSize, DataSize, FrameCount,   ParamRate')
        for kk in frameIDs:
            # datasize = framesize - header(10bytes) - trailer(2bytes)
            f_count=len(frameIDs[kk]['time'])
            print('{:7}, {:9}, {:8}, {:10},  {:<18}'.format(kk,frameIDs[kk]['size'],frameIDs[kk]['size']-12,f_count,frameIDs[kk]['rate']) )
        if DUMPDATA:
            print('------ DumpData -----')
            time_tmp=[]
            ii=0
            for kk in frameIDs:
                if kk==1: continue  #跳过frame_id=1
                time_cnt=len(frameIDs[kk]['time'])
                time_tmp.append({'key':kk, 'len':time_cnt, 'time':[]})
                if time_cnt>5:
                    for jj in range(0,3):
                        time_tmp[ii]['time'].append(frameIDs[kk]['time'][jj])
                    time_tmp[ii]['time'].append('...')
                    for jj in range(time_cnt-3,time_cnt):
                        time_tmp[ii]['time'].append(frameIDs[kk]['time'][jj])
                else:
                    for jj in range(0,time_cnt):
                        time_tmp[ii]['time'].append(frameIDs[kk]['time'][jj])
                ii+=1
            print('{:>8} '.format('FrameID:'), end=' ')
            for kk in time_tmp:
                print('{:^11} '.format(kk['key']), end=' ')
            print()
            for ii in range(len(time_tmp[1]['time'])):
                print('{:>8} '.format('time:  '), end=' ')
                for jj in range(len(time_tmp)):
                    if time_tmp[jj]['len']>ii:
                        print('{:>11} '.format(time_tmp[jj]['time'][ii]), end=' ')
                    else:
                        print('{:>11} '.format(' '), end=' ')
                print()

    def get_param(self, param):
        '''
        解码一个参数
           author:南方航空,LLGZ@csair.com
        '''
        if len(param)<1:
            print('Empty parameter Name!')
            return []

        frd=self.readFRD()
        param_conf=self.getFRD(param)

        if len(param_conf)<1:
            print('Parameter "%s" not found!'% param)
            return []
        #print(param_conf)

        #----------zip压缩文件内容-----------
        buf=self.qar
        if buf is None:
            print('ERR, arinc767 raw file NOT found')
            return []

        sync767=0xEB90  #同步字
        ttl_len=len(buf)

        #----------寻找起始位置-----------
        frame_pos=0  #frame开始位置,字节指针
        frame_pos, frame_size=self.find_SYNC(buf, ttl_len, frame_pos, sync767)
        if frame_pos >= ttl_len -2:
            print('ERR,SYNC1 not found.',flush=True)
            raise(Exception('ERR,SYNC1 not found.'))
        elif frame_pos>0:
            print('ERR,SYNC1 not at begin.',flush=True)

        #----------验证同步字位置，header内容, trailer内容-----------
        param_val=[]
        ii=0    #计数
        while True:
            #----------验证同步字,并返回size--------
            frame_pos2 = frame_pos  #保存上一次的位置
            frame_pos, frame_size=self.find_SYNC(buf, ttl_len, frame_pos, sync767) #同时返回size
            if frame_pos>=ttl_len -2:
                #-----超出文件结尾，退出-----
                break
            if frame_pos > frame_pos2:
                print('==>ERR, miss SYNC at x%X, Refound at x%X'%(frame_pos2, frame_pos))

            #----------timestamp--------
            tm=self.getWord(buf,frame_pos+4) #timestamp
            tm=(tm <<16) | self.getWord(buf,frame_pos+6) #timestamp
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
            frame_id=self.getWord(buf,frame_pos+8) # type & id
            frame_type= frame_id >> 8
            frame_id &= 0xff

            if not (frame_type==0 and frame_id == param_conf['frameID']):
                frame_pos += frame_size
                continue

            #----------trailer: type & id, 验证trailer是否正确--------
            frame_tail=self.getWord(buf,frame_pos+frame_size-2) # type & id
            frame_tail_type= frame_tail >> 8
            frame_tail_id = frame_tail & 0xff
            if frame_id != frame_tail_id or frame_type != frame_tail_type:
                print('==>ERR, type or id in header & trailer is not same. Type:%d != %d or ID:%d != %d'% (frame_type, frame_tail_type, frame_id, frame_tail_id ))
            if frame_type != 0:
                print('==>ERR, type is NOT 0.')
            #print('Frame id:   %X' % frame_id)

            #------获取参数的值 ----
            pos_dword,bits_mod=divmod(param_conf['start_bit'], 32)
            dword=self.getDWord(buf, frame_pos + 10 + pos_dword * 4)
            bits= (1 << param_conf['pm_blen']) -1
            move=32-bits_mod - param_conf['pm_blen']
            if move <0:
                bits3 = bits << (32 + move)
                bits2 = bits3 >> 32  #取 64->32 位
                bits3 &= 0xffffffff  #取 32-> 1 位
                valueraw=(dword & bits2)
                valueraw <<=  (move * -1)
                dword=self.getDWord(buf, frame_pos + 10 + (pos_dword * 4) +4)  #取下一个 dword
                valueraw |= ((dword & bits3) >> (32 + move))
            else:
                bits <<= move
                valueraw=dword & bits
                valueraw >>=  move
            value =self.arinc429_decode(valueraw ,param_conf )

            #------------super根据需要修改的字段，手工修改此段代码------------
            #---需修改 ARINC767 文件的 Header 中的 机号,时间.-----
            print(type(value),value,hex(valueraw),valueraw.to_bytes(4,'big'))
            if value=='X':
            #if value==b'\x00\x00\x002':
            #if valueraw==b'\x00\x00\x00\x05':
            #if valueraw==0x05:
                new_value=b'\x00\x00\x00Y'
                valueraw=int.from_bytes(new_value,byteorder='big',signed=False)
                print(value,'change to:',new_value, hex(valueraw))
                bits= (1 << param_conf['pm_blen']) -1
                move=32-bits_mod - param_conf['pm_blen']
                if move <0:
                    bits3 = bits << (32 + move)
                    bits2 = bits3 >> 32  #取 64->32 位
                    bits3 &= 0xffffffff  #取 32-> 1 位
                    dword3 = valueraw << (32 + move)
                    dword2 = dword3 >> 32  #取 64->32 位
                    dword3 &= 0xffffffff  #取 32-> 1 位
                    self.setDWord(frame_pos + 10 + pos_dword * 4, dword2, bits2)
                    self.setDWord(frame_pos + 10 +(pos_dword * 4) +4, dword3, bits3)  #set下一个 dword
                else:
                    bits <<= move
                    valueraw <<= move
                    self.setDWord(frame_pos + 10 + pos_dword * 4, valueraw, bits)
            #------------super根据需要修改的字段，手工修改此段代码------------

            param_val.append( {'time':'%02d:%02d:%02d.%s'%(HH,MM,SS,MS_str), 'val':value } )

            frame_pos += frame_size
        #print('-----End of file. File scan finished.----')

        #----------改写raw.dat-----------
        if self.write_raw_dat is not None:
            wfp=open(self.write_raw_dat,'wb')
            wfp.write(self.qar)
            wfp.close()

        return param_val


    def getDWord(self, buf,pos):
        '''
        读取两个WORD，拼为一个32 bit dword。高位在前。bigEndian,High-byte first.
           author:南方航空,LLGZ@csair.com
        '''
        return (self.getWord(buf, pos) << 16) | self.getWord(buf, pos+2)

    def getWord(self, buf,pos):
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
    def setDWord(self, pos, word, mask):
        mask2=mask >> 16
        word2=word >> 16
        self.setWord(pos, word2, mask2)
        mask2=mask & 0xffff
        word2=word & 0xffff
        self.setWord(pos+2, word2, mask2)
    def setWord(self, pos, word, mask, word_len=1):
        '''
        写入两个字节，取16bit为一个word。高位在前。bigEndian,High-byte first.
           author:南方航空,LLGZ@csair.com
        '''
        buf=self.qar
        #print(type(buf), type(buf[pos]), type(buf[pos+1])) #bytes, int, int

        ttl=len(buf)  #读数据的时候,开始位置加上subframe和word的偏移，可能会超限
        if word_len==1:
            if pos+1 >= ttl:
                return  #超限不修改
            else:
                byte=bytearray(b'0')
                byte[0]=(~mask >> 8 ) & 0xFF
                buf[pos] &= byte[0]             #清除对应bit
                buf[pos] |= (word >> 8 )& 0xFF  #写入值
                byte[0]= ~mask & 0xFF
                buf[pos +1] &= byte[0]          #清除对应bit
                buf[pos +1] |= word & 0xFF      #写入值
                #return ((buf[pos] << 8 ) | buf[pos +1] )

    def readPAR(self):
        '读 frd 配置'
        dataver=self.dataVer()
        if dataver<0:
            dataver=self.getAIR()[0]
        if not hasattr(self,'par') or self.par is None:
            self.par=PAR.read_parameter_file(dataver)
    def getPAR(self, param):
        '''
        获取参数在arinc429的32bit word中的位置配置
        挑出有用的,整理一下,返回
           author:南方航空,LLGZ@csair.com
        '''
        self.readPAR()
        if self.par is None or len(self.par)<1:
            return {}
        #param=param.upper()  #不能改大写. 有几个参数是"大小写字母混合"的。
        buf_map=list(map(lambda x: param==x[0] ,self.par))
        idx4=buf_map.count(True)
        if idx4<1 or idx4>1:
            print('=>ERR, (par)"%s" not found OR error.'%(param) )
            return {}
        idx4=buf_map.index(True) #获取索引
        pm_find=self.par[idx4]
        if True:
            tmp_part=[]
            if isinstance(pm_find[36], list):
                #如果有多个部分的bits的配置, 组合一下
                for ii in range(len(pm_find[36])):
                    tmp_part.append({
                            'id'  :int(pm_find[36][ii]),  #Digit ,顺序标记
                            'pos' :int(pm_find[37][ii]),  #MSB   ,开始位置
                            'blen':int(pm_find[38][ii]),  #bitLen,DataBits,数据长度
                            })
            return {
                    'ssm'    :int(pm_find[5]) if len(pm_find[5])>0 else -1,   #SSM Rule , (0-15)0,4 
                    'signBit':int(pm_find[6]) if len(pm_find[6])>0 else -1,   #bitLen,SignBit  ,符号位位置
                    'pos'   :int(pm_find[7]) if len(pm_find[7])>0 else -1,   #MSB  ,开始位置
                    'blen'  :int(pm_find[8]) if len(pm_find[8])>0 else -1,   #bitLen,DataBits ,数据部分的总长度
                    'part'    :tmp_part,
                    'type'    :pm_find[2],    #Type(BCD,CHARACTER)
                    'format'  :pm_find[17],    #Display Format Mode (DECIMAL,ASCII)
                    'Resol'   :pm_find[12],    #Computation:Value=Constant Value or Resol=Coef A(Resolution) or ()
                    'A'       :pm_find[29] if pm_find[29] is not None else '',    #Coef A(Res)
                    'B'       :pm_find[30] if pm_find[30] is not None else '',    #Coef b
                    'format'  :pm_find[25],    #Internal Format (Float ,Unsigned or Signed)
                    }

    def getFRD(self, paramName=''):
        '''
        获取参数在arinc767的32bit word中的位置配置
        挑出有用的,整理一下,返回
           author:南方航空,LLGZ@csair.com
        '''
        frd=self.readFRD()
        if frd is None:
            print('Empty dataVer.',flush=True)
            return {}

        if len(paramName)>0:
            # ------在FRED中,找出 参数的 frame_id 和 order -------
            buf_map=list(map(lambda x: paramName==x[1] ,frd['4'])) #在['4']中查找匹配, x[1]:Parameter Name
            idx4=buf_map.count(True)
            if idx4<1 or idx4>1:
                print('=>ERR, not find "%s" in frd_4 OR error.'%(paramName) )
                return {}
            idx4=buf_map.index(True) #获取索引
            pm_long_name=frd['4'][idx4][0]

            buf_map=list(map(lambda x: pm_long_name == x[2] ,frd['3'])) #在['3']中,查找匹配, x[2]:Parameter long name
            idx3=buf_map.count(True)
            if idx3<1 or idx3>1:
                print('=>ERR, not find "%s" in frd_3 OR error.'%(pm_long_name) )
                return {}
            idx3=buf_map.index(True) #获取索引
            param_frame_id=frd['3'][idx3][0]
            param_order=frd['3'][idx3][1]
            param_conf={}
            #print('param_frame_id:{}, param_order:{}'.format(param_frame_id, param_order) )


        conf={}
        ii=0   #测试用，可以删除
        for row in frd['2']:  #参数的rate,Nr
            #if ii>5: break
            ii+=1
            if row[0].startswith('Frame'): #跳过第一行,标题行 
                continue
            frame_id=row[0]
            if len(paramName)>0:
                #获取单个参数，只读取对应的 frame_id
                if frame_id != param_frame_id: continue
            #print('====== %s ========' % frame_id)

            #初始化参数变量
            if frame_id not in conf:
                conf[frame_id]=[]
            if str(frame_id)+'_bits' not in conf:
                conf[str(frame_id)+'_bits']={
                        'dword':0,
                        'dbits':0,
                        'ttl_bits':0,
                        }

            jj=0   #测试用，可以删除
            for pm_id in range(1,int(row[4])+1):  #row[4]:Parameter Nr for this frame id
                #if jj>12: break
                jj+=1

                # ------在FRED中按顺序(order)，提取参数名-------
                buf_map=list(map(lambda x: frame_id == x[0] and pm_id==int(x[1]) ,frd['3'])) #在['3']中,查找匹配, x[0]:Frame Id, x[1]:Parameter order
                idx3=buf_map.count(True)
                if idx3<1 or idx3>1:
                    print('=>ERR, find (frame_id:%s,order:%s) in frd_3 != 1.'%(frame_id, pm_id) )
                idx3=buf_map.index(True) #获取索引

                #if len(frd['3'][idx3][3])>0:  #Parameter Mnemonic 有内容，就打印一下。(通常都是无内容的)
                #    print('=>INFO, Fid:%d, order:%d, Mnemonic:%s'%(frame_id, pm_id, frd['3'][idx3][3]))
                pm_long_name=frd['3'][idx3][2]

                buf_map=list(map(lambda x: pm_long_name==x[0] ,frd['4'])) #在['4']中查找匹配, x[0]:Parameter Long Name
                idx4=buf_map.count(True)
                if idx4<1 or idx4>1:
                    print('=>ERR, find (pm_long_name:%s) in frd_4 != 1.'%(pm_long_name) )
                idx4=buf_map.index(True) #获取索引
                pm_name=frd['4'][idx4][1]
                #print(pm_id, idx3,idx4, frd['3'][idx3], frd['4'][idx4])

                # ------根据参数名, 去par中获取参数的配置-------
                par=self.getPAR(pm_name)
                #print(par)
                if len(par)<1:
                    #print('=>ERR,par NOT found.',pm_id, idx3,idx4, frd['3'][idx3], frd['4'][idx4])
                    print('=>ERR,par NOT found.', 'pm_long_name:',pm_long_name, ' pm_name:',pm_name )
                    #print('         ', 'FRD3:',frd['3'][idx3], 'FRD4:',frd['4'][idx4])
                    continue

                conf_one={  #临时变量
                        'seq':pm_id,
                        'longName':pm_long_name,
                        'name':pm_name,
                        'start_bit': conf[str(frame_id)+'_bits']['ttl_bits'],
                        }

                pm_bits=0
                if par['signBit']>0:
                    pm_bits +=1
                    #print('==>INFO, signBit',par['signBit'],frd['4'][idx4])  #有挺多参数,有符号位
                if par['blen']>0:
                    pm_bits +=par['blen']

                conf_one['pm_blen']=pm_bits
                conf[str(frame_id)+'_bits']['ttl_bits'] +=pm_bits

                if par['pos'] != par['blen']:  #看看,参数是不是从bit1开始的, 可删
                    print('==>INFO, param POS != BLEN')
                conf_one.update(par)
                conf[frame_id].append(conf_one)

                if len(paramName)<1:
                    #按填满一个 dword 计算
                    if conf[str(frame_id)+'_bits']['dbits'] + pm_bits >32:
                        #如果这个参数会超出DWORD，应该补pad，然后把这个参数写入下一个DWORD
                        conf[str(frame_id)+'_bits']['dbits'] = pm_bits
                        conf[str(frame_id)+'_bits']['dword'] +=1
                    else:
                        conf[str(frame_id)+'_bits']['dbits'] += pm_bits

                else: #if len(paramName)>0:
                    if pm_id == int(param_order):
                        conf_one['frameID']=int(frame_id)  #额外加一个内容frameID
                        param_conf=conf_one
                        return conf_one   #找到参数的配置,就直接return,也可以
                        #break   #找到参数的配置,就中断,也可以


        if len(paramName)>0:
            return param_conf
        else:
            return conf

    def paramlist(self):
        '''
        获取所有的记录参数名称，按 frame_id 分类
           author:南方航空,LLGZ@csair.com
        '''
        frd=self.readFRD()
        param_list={}
        if frd is None:
            print('Empty dataVer.',flush=True)
            return param_list
        ii=0
        for row in frd['2']:  #参数的rate,Nr
            #if ii>5: break
            ii+=1
            if row[0].startswith('Frame'): #跳过第一行,标题行 
                continue
            frame_id=row[0]
            if frame_id not in param_list:
                param_list[frame_id]={'info':row[1], 'pm':[]}

            jj=0
            for pm_id in range(1,int(row[4])+1):  #row[4]:Parameter Nr for this frame id
                jj+=1

                # ------在FRED中按顺序order，提取参数名-------
                buf_map=list(map(lambda x: frame_id == x[0] and pm_id==int(x[1]) ,frd['3'])) #在['3']中,查找匹配, x[0]:Frame Id, x[1]:Parameter order
                idx3=buf_map.index(True) #获取索引

                pm_long_name=frd['3'][idx3][2]

                buf_map=list(map(lambda x: pm_long_name==x[0] ,frd['4'])) #在['4']中查找匹配, x[0]:Parameter Long Name
                idx4=buf_map.index(True) #获取索引
                pm_name=frd['4'][idx4][1]

                param_list[frame_id]['pm'].append(pm_name)

        return param_list

    def readFRD(self):
        '读 frd 配置'
        dataver=self.getAIR()[0]
        if isinstance(dataver,(str,float)):
            dataver=int(dataver)
        if self.frd is None or self.frd_dataver != dataver: #有了就不重复读
            self.frd=FRD.read_parameter_file(dataver)
            self.frd_dataver = dataver
        return self.frd

    def getAIR(self):
        '''
        获取机尾号对应解码库的配置。
        挑出有用的,整理一下,返回
           author:南方航空,LLGZ@csair.com
        '''
        reg=self.getREG().upper()
        self.readAIR()
        idx=0
        for row in self.air: #找机尾号
            if row[0]==reg: break
            idx +=1
        if idx<len(self.air):  #找到记录
            return [self.air[idx][12], #dataver
                    self.air[idx][13], #dataver2
                    self.air[idx][16], #recorderType
                    self.air[idx][17]] #recorderType2
        else:
            return [0,0,'','']  #没找到
    def readAIR(self):
        '读 air 配置'
        if self.air is None:
            self.air=AIR.air(conf.aircraft)


    def getREG(self):
        '''
        从zip文件名中，找出机尾号
           author:南方航空,LLGZ@csair.com
        '''
        basename=os.path.basename(self.qar_filename)
        reg=basename.strip().split('_',1)
        if len(reg[0])>6: #787的文件名没有用 _ 分隔
            return reg[0][:6]
        elif len(reg[0])>0:
            return reg[0]
        else:
            return ''

    def arinc429_decode(self, word,conf):
        '''
        par可能有的 Type: 'CONSTANT' 'DISCRETE' 'PACKED BITS' 'BNR LINEAR (A*X)' 'COMPUTED ON GROUND' 'CHARACTER' 'BCD' 'BNR SEGMENTS (A*X+B)' 'UTC'
        par实际有的 Type(717): 'BNR LINEAR (A*X)' 'BNR SEGMENTS (A*X+B)' 'CHARACTER' 'BCD' 'UTC' 'PACKED BITS' 'DISCRETE'
        par实际有的 Type(767): 'BNR LINEAR (A*X)' 'CHARACTER' 'BCD' 'PACKED BITS' 'DISCRETE' 'COMPUTED ON BOARD'
            author:南方航空,LLGZ@csair.com  
        '''
        if conf['type'].find('BNR')==0 or \
                conf['type'].find('PACKED BITS')==0:
            return self.arinc429_BNR_decode(word ,conf)
        elif conf['type'].find('BCD')==0 or \
                conf['type'].find('CHARACTER')==0:
            return self.arinc429_BCD_decode(word ,conf)
        elif conf['type'].find('UTC')==0:
            val=self.arinc429_BNR_decode(word ,conf)
            ss= val & 0x3f         #6bits
            mm= (val >>6) & 0x3f   #6bits
            hh= (val >>12) & 0x1f  #5bits
            return '%02d:%02d:%02d' % (hh,mm,ss)
        else:
            return self.arinc429_BNR_decode(word ,conf)

    def arinc429_BCD_decode(self, word,conf):
        '''
        从 ARINC429格式中取出 值
            conf=[{ 'ssm'    :tmp2.iat[0,5],   #SSM Rule (0-15)0,4 
                    'signBit':tmp2.iat[0,6],   #bitLen,SignBit
                    'pos'   :tmp2.iat[0,7],   #MSB
                    'blen'  :tmp2.iat[0,8],   #bitLen,DataBits
                    'part': [{
                        'id'     :tmp2.iat[0,36],  #Digit
                        'pos'    :tmp2.iat[0,37],  #MSB
                        'blen'   :tmp2.iat[0,38],  #bitLen,DataBits
                    'type'    :tmp2.iat[0,2],     #Type(BCD,CHARACTER)
                    'format'  :tmp2.iat[0,17],    #Display Format Mode (DECIMAL,ASCII)
                    'Resol'   :tmp2.iat[0,12],    #Computation:Value=Constant Value or Resol=Coef A(Resolution) or ()
                    'format'  :tmp2.iat[0,25],    #Internal Format (Float ,Unsigned or Signed)
                        }]
        author:南方航空,LLGZ@csair.com
        '''
        if conf['type']=='CHARACTER':
            if len(conf['part'])>0:
                #有分步配置
                value = ''
                for vv in conf['part']:
                    #根据blen，获取掩码值
                    bits= (1 << vv['blen']) -1
                    #把值移到最右(移动到bit0)，并获取值
                    tmp = ( word >> (vv['pos'] - vv['blen']) ) & bits
                    value +=  chr(tmp)
            else:
                #根据blen，获取掩码值
                bits= (1 << conf['blen']) -1
                #把值移到最右(移动到bit0)，并获取值
                value = ( word >> (conf['pos'] - conf['blen']) ) & bits
                value =  chr(value)
            return value
        else:  #BCD
            #符号位
            sign=1
            if conf['signBit']>0:
                bits=1
                bits <<= conf['signBit']-1  #bit位编号从1开始,所以-1
                if word & bits:
                    sign=-1

            if len(conf['part'])>0:
                #有分步配置
                value = 0
                for vv in conf['part']:
                    #根据blen，获取掩码值
                    bits= (1 << vv['blen']) -1
                    #把值移到最右(移动到bit0)，并获取值
                    tmp = ( word >> (vv['pos'] - vv['blen']) ) & bits
                    value = value * 10 + tmp
            else:
                #根据blen，获取掩码值
                bits= (1 << conf['blen']) -1
                #把值移到最右(移动到bit0)，并获取值
                value = ( word >> (conf['pos'] - conf['blen']) ) & bits
            return value * sign

    def arinc429_BNR_decode(self, word,conf):
        '''
        从 ARINC429格式中取出 值
            conf=[{ 'ssm'    :tmp2.iat[0,5],   #SSM Rule (0-15)0,4 
                    'signBit':tmp2.iat[0,6],   #bitLen,SignBit
                    'pos'   :tmp2.iat[0,7],   #MSB
                    'blen'  :tmp2.iat[0,8],   #bitLen,DataBits
                    'part': [{
                        'id'     :tmp2.iat[0,36],  #Digit
                        'pos'    :tmp2.iat[0,37],  #MSB
                        'blen'   :tmp2.iat[0,38],  #bitLen,DataBits
                    'type'    :tmp2.iat[0,2],     #Type(BCD,CHARACTER)
                    'format'  :tmp2.iat[0,17],    #Display Format Mode (DECIMAL,ASCII)
                    'Resol'   :tmp2.iat[0,12],    #Computation:Value=Constant Value or Resol=Coef A(Resolution) or ()
                    'format'  :tmp2.iat[0,25],    #Internal Format (Float ,Unsigned or Signed)
                        }]
        author:南方航空,LLGZ@csair.com
        '''
        #根据blen，获取掩码值
        bits= (1 << conf['blen']) -1
        #把值移到最右(移动到bit0)，并获取值
        value = ( word >> (conf['pos'] - conf['blen']) ) & bits

        #符号位
        if conf['signBit']>0:
            bits = 1 << (conf['signBit']-1)  #bit位编号从1开始,所以-1
            if word & bits:
                value -= 1 << conf['blen']
        #Resolution
        if conf['type'].find('BNR LINEAR (A*X)')==0:
            if conf['Resol'].find('Resol=')==0:
                value *= float(conf['Resol'][6:])
        elif conf['type'].find('BNR SEGMENTS (A*X+B)')==0:
            if len(conf['A'])>0:
                value *= float(conf['A'])
            if len(conf['B'])>0:
                value += float(conf['B'])
        elif conf['type'].find('COMPUTED ON BOARD')==0:
            if conf['format']=='Float':
                value = struct.unpack('f',struct.pack('I',value))[0] #转4字节，再转float。I=4字节无符号整数, L=8字节无符号整数
        else:
            #----已知 PACKED BITS, UTC, DISCRETE, 就应该按 BNR 处理---
            #其他不能识别的类型，默认按BNR处理
            #在此，无需给出错误提示
            pass
        return value 

import os,sys
def usage():
    print()
    print(u' 读取 arinc767中原始数据,根据参数编码规则,解码一个参数。')
    print(u'Usage:')

    print('   import Get_param_from_arinc767 as A767')
    print('   qar_file="B-1234xxxxxxxxx.zip"')
    print('   myQAR=A767.ARINC767(qar_file)               #创建实例,并打开一个文件')
    print('   parameter_list=myQAR.paramlist()     #列出所有的参数的名称')
    print('   frd=myQAR.getFRD()                   #获取frd配置')
    print('   pm_config=myQAR.getFRD("VRTG")       #获取参数的frd配置')
    print('   par=myQAR.getPAR("VRTG")      #获取参数的par配置')
    print('   dataver=myQAR.dataVer()       #已打开文件的dataVer')
    print('   myQAR.get_param("VRTG")       #解码一个参数')
    print('   myQAR.myQAR.data_file_info()  #扫描确定文件格式是否正确')
    print('   myQAR.close()                 #关闭')
    print('   myQAR.qar_file(qar_file)      #重新打开一个文件')
    print(u'\n               author:南方航空,LLGZ@csair.com')
    print(u' 认为此项目对您有帮助，请发封邮件给我，让我高兴一下.')
    print(u' If you think this project is helpful to you, please send me an email to make me happy.')
    print()
    return

if __name__=='__main__':
    usage()
    exit()

