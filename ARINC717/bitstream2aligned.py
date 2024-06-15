#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
读取 bitstream 格式的 raw.dat 。把12bit的frame展开为16bit，高4bit填0。方便下一步处理。
本程序丢弃了所有不完整的Frame，并没有判断丢帧，也没有补帧。

'''
    1 Frame has 4 subframe
    1 subframe duration 1 sec
    1 sec has 64,128,256,512 or 1024 words (words/sec)
    1 word has 12 bit
    Synchronization word location: 1st word of each subframe
      For standard synchro word:
                           sync1      sync2      sync3      sync4 
      12bits sync word -> 247        5B8        A47        DB8 

  ---------BITSTREAM FILE FORMAT---------- 
      bit:  F E D C B A 9 8 7 6 5 4 3 2 1 0  
    byte1  :x:x:x:x:x:x:x:x:x:x:x|S:Y:N:C:H: 
    byte2  :R:O: :1:-:-:>|W:O:R:D: :1:-:-:-: 
    byte3  :-:-:>|W:O:R:D: :2:-:-:-:-:-:>|W: 
    byte4  :O:R:D: :3:-:-:-:-:-:>|W:O:R:D: : 
    byte5  :4:-:-:-:-:-:>|W:O:R:D: :5:-:-:-: 
    byte6  :-:-:>| : : : : : : : : : : : : : 
     ...              ... ...  
  ----------------------------------------  
   At Little-Endian system, 在小端格式的系统中.
   Bitstream file format 应该是这样的. osnosn@126.com
      bit:  F E D C B A 9 8 7 6 5 4 3 2 1 0  
    byte1  :R:O: :1:-:-:>|x:x:x:x:x:x:x:x:x:
    byte2  :O:R:D: :1:-:-:-:-:-:>|S:Y:N:C:H:  
    byte3  :-:-:>|W:O:R:D: :2:-:-:-:-:-:>|W: 
    byte4  :4:-:-:-:-:-:>|W:O:R:D: :3:-:-:-: 
    byte5  :O:R:D: :5:-:-:-:-:-:>|W:O:R:D: : 
    byte6  : : : |W:O:R:D: :6:-:-:-:-:-:>|W: 
     ...              ... ...  
  ----------------------------------------  

  ----------ALIGNED BIT FILE FORMAT-----------  
  bit: F E D C|B A 9 8 7 6 5 4 3 2 1 0 
    
      |X X X X|      ... ...          |low address
      |X X X X|      ... ...          | 
      |-------|-----------------------| -- 
      |X X X X|SYNCHRONIZATION WORD 1 | | 
      |X X X X|        DATA           | 
      |X X X X|        DATA           |subframe1 
      |X X X X|      ... ...          | | 
      |-------|-----------------------| --  
      |X X X X|SYNCHRONIZATION WORD 2 | | 
      |X X X X|        DATA           | 
      |X X X X|        DATA           |subframe2 
      |X X X X|      ... ...          | | 
      |-------|-----------------------| --  
      |X X X X|SYNCHRONIZATION WORD 3 | | 
      |X X X X|        DATA           | 
      |X X X X|        DATA           |subframe3 
      |X X X X|      ... ...          | | 
      |-------|-----------------------| --  
      |X X X X|SYNCHRONIZATION WORD 4 | 
      |X X X X|      ... ...          | 
      |X X X X|      ... ...          |high address
  --------------------------------------------  

根据上述的文档的描述。 理论上synchro同步字出现的顺序应该是，sync1,sync2,sync3,sync4, 间隔为 words/sec 的个数。
    author: osnosn@126.com
    2024-06
  --------------------------
'''

"""
import struct
#from datetime import datetime
import zipfile
#import psutil   #非必须库
from io import BytesIO

def main():
    '''
    '''
    global FNAME,WFNAME,DUMPDATA
    global WORDSEC

    BS=BITSTREAM(FNAME)

    print()
    bitcnt=0     #bit计数
    FFF_cnt=0    # 连续的 0xFFF 计数, 12bit word 计数
    bit_cnt2=0  # 上一个同步字的位置, bit 计数
    while bitcnt < BS.rawlen * 8:
        word = BS.getword(bitcnt)
        if word is None:
            break  #文件结束
        if word == 0xfff:
            FFF_cnt +=1
        else:
            if FFF_cnt > 60:
                print('---> Found {0:d} consecutive "0xFFF" synchronization words and an additional {1} "bit 1".'.format(FFF_cnt//12,FFF_cnt%12) ,flush=True)
                FFF_cnt  =0
        if word == 0x247:
            print('==>Found sync1   , At 0x{0:X} bytes+{1:1d}bit, 0x{2:<5X} word+{3:02d}bit, Frame len:0x{4:<3X}({4})'.format(
                bitcnt//8,bitcnt%8,bitcnt//12,bitcnt%12,(bitcnt-bit_cnt2)//12),flush=True)
            bit_cnt2=bitcnt

            word2 = BS.getword(bitcnt+WORDSEC*1*12)
            if word2 is None: break
            elif word2 == 0x5B8:
                print('==>Found sync 2  , At next 0x{0:3X}({0})'.format(WORDSEC),flush=True)
                #print('==>Found sync2.5B8,at x%X word(12bit)+%dbit,len:x%X'%(word_cnt,ii,word_cnt-word_cnt2))
            else:
                print('====>Missing  sync2,  At next 0x{0:3X}({0})'.format(WORDSEC),flush=True)
                bitcnt+=1
                continue

            word2 = BS.getword(bitcnt+WORDSEC*2*12)
            if word2 is None: break
            elif word2 == 0xA47:
                print('==>Found sync  3 , At next 0x{0:X}({0})'.format(WORDSEC),flush=True)
                #print('==>Found sync3.A47,at x%X word(12bit)+%dbit,len:x%X'%(word_cnt,ii,word_cnt-word_cnt2))
            else:
                print('==>Missing sync 3, At next 0x{0:3X}({0})'.format(WORDSEC),flush=True)
                bitcnt+=1
                continue

            word2 = BS.getword(bitcnt+WORDSEC*3*12)
            if word2 is None: break
            elif word2 == 0xDB8:
                print('==>Found sync   4, At next 0x{0:X}({0})'.format(WORDSEC),flush=True)
                #print('==>Found sync4.DB8,at x%X word(12bit)+%dbit,len:x%X'%(word_cnt,ii,word_cnt-word_cnt2))
            else:
                print('==>Missing sync  4, At next 0x{0:3X}({0})'.format(WORDSEC),flush=True)
                bitcnt+=1
                continue
            BS.convert12_16(bitcnt,WORDSEC*4)
            bitcnt +=WORDSEC*4*12
            continue
        bitcnt+=1

    BS.write_file(WFNAME)
    print('   Note: word=12bit, byte=8bit, Frame=4subFrame, 1 second=1 subFrame. ',flush=True)
    print()

class BITSTREAM():
    def __init__(self,fname=''):
        self.raw=None
        self.rawlen=0
        self.raw_filename=''
        self.aligned=bytearray()
        if len(fname)>0:
            self.raw_file(fname)

    def raw_file(self,raw_filename):
        #----------读取raw.dat文件-----------
        if self.raw is None or self.raw_filename != raw_filename:
            with open(FNAME,'rb') as fp:
                self.raw=fp.read()
            '''
            try:
                fzip=zipfile.ZipFile(FNAME,'r') #打开zip文件
            except zipfile.BadZipFile as e:
                print('ERR,FailOpenZipFile',e,FNAME,flush=True)
                raise(Exception('ERR,FailOpenZipFile'))
            #filename_zip='raw.dat'
            #buf=fzip.read(filename_zip)
            names=fzip.namelist()
            self.raw=fzip.read(names[0]) #读取第一个文件内容,放入内存
            fzip.close()
            '''
        
            self.rawlen=len(self.raw)
            self.raw_filename=raw_filename
            self.aligned=bytearray()
        
    def getword(self, bitcnt=0):
        '''
          从文件头开始 第0bit，取第bitcnt的bit位
           bitcnt 除以 8,余数 从低位->高位: 0->7bit
           取出的bit,从高位移入,连续移动12次
        '''
        word=0
        for ii in range(0,12):
            word >>=1
            bit=self.getbit(bitcnt+ii)
            if bit == -1:
                return None   #文件结束
            elif bit == 1:
                word |= 0x800
        return word
            
    def getbit(self, bitcnt=0):
        '''
          从文件头开始 第0bit，取第bitcnt的bit位
           bitcnt 除以 8,余数 从低位->高位: 0->7bit
        '''
        bytecnt=bitcnt // 8
        if bytecnt >= self.rawlen:
            return -1   #文件结束
        bytebit=bitcnt % 8
        mask=(1<<bytebit)
        buf=self.raw[bytecnt]
        if buf & mask:
            return 1
        else:
            return 0
    def convert12_16(self, bitcnt=0,wordlen=0):
        for ii in range(0,wordlen*12,12):
            word=self.getword(bitcnt+ii)
            if word is None:
                return
            self.aligned.extend(struct.pack('<H',word))  #H:unsigned short int,u16
        return
    def write_file(self,filename=''):
        if len(self.aligned)<10:
            print(' Empty Aligned data to write.')
            return
        elif filename is None or len(filename)<2:
            print(' Empty filename to write.')
            return
        else:
            with open(filename,'wb') as fp:
                fp.write(self.aligned)
            print(' Aligned data write into "{}".'.format(filename))

import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'   命令行工具。')
    print(u'   读取 bitstream 格式的 raw.dat 。把12bit的frame展开为16bit，高4bit填0。方便下一步处理。')
    print(u'   本程序丢弃了所有不完整的Frame，没有判断丢帧，也没有补帧。')
    print(sys.argv[0]+' [-h|--help]')
    print('   -h, --help               print usage.')
    print('   -f, --file=bitstm.dat    读取 "bitstream.dat"')
    print('   -s, --wordsec=512        word per second "512", 1 second=1 subFrame.')
    print('   -w aligned.dat           写入文件"aligned.dat"')
    print(u'\n        author: osnosn@126.com   2024-06')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hw:s:df:',['help','file=','wordsec=',])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    WORDSEC=0
    WFNAME=None
    DUMPDATA=False
    if len(args)>0:  #命令行剩余参数
        FNAME=args[0]  #只取第一个
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-f','--file'):
            FNAME=value
        elif op in('-s','--wordsec'):
            WORDSEC=int(value)
        elif op in('-w',):
            WFNAME=value
        elif op in('-d',):
            DUMPDATA=True
    if FNAME is None:
        usage()
        exit()
    if os.path.isfile(FNAME)==False:
        usage()
        print(' ERROR, "{}" Not a file.'.format(FNAME,))
        print()
        exit()
    if WORDSEC < 128:
        usage()
        print(' ERROR, Missing WordPerSecond "-s 256"')
        print()
        exit()

    main()

