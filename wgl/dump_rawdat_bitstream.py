#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
读取 wgl 中 raw.dat 。把12bit的frame展开为16bit，高4bit填0。方便下一步处理。

'''
    1 Frame has 4 subframe
    1 subframe duration 1 sec
    1 sec has 64,128,256,512 or 1024 words (words/sec)
    1 word has 12 bit
    Synchronization word location: 1st word of each subframe
    Synchronization word length:   12,24 or 36 bits
      For standard synchro word:
                           sync1      sync2      sync3      sync4 
      12bits sync word -> 247        5B8        A47        DB8 
      24bits sync word -> 247001     5B8001     A47001     DB8001 
      36bits sync word -> 247000001  5B8000001  A47000001  DB8000001 

   |<------------------------     Frame     -------------------------->| 
   |   subframe 1   |   subframe 2   |   subframe 3   |   subframe 4   | 
   |                |                |                | Duration=1sec  | 
   |* # #  ... # # #|* # #  ... # # #|* # #  ... # # #|* # #  ... # # #| 
    |          |     |                |                |          | 
   synchro     |    synchro          synchro          synchro     | 
    247        |     5B8              A47              DB8        | 
      ________/^\_____________               ____________________/^\_  
     /  Regular Parameter     \      Frame  /     Superframe word    \  
    |12|11|10|9|8|7|6|5|4|3|2|1|        1  |12|11|10|9|8|7|6|5|4|3|2|1| 
        (12 bits)                      ...         .........        
                                       32  |12|11|10|9|8|7|6|5|4|3|2|1| 

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

  bit F: CUT,     Location: First word of the frame.
       set 1 if the frame is not continuous with the previous frame;
       set 0 if the frame is continuous;
       set 0 for the other words of the frame;

  bit E: UNKNOWN, Location: First word of each subframe.
       set 1 if the subframe begins with its synchro word, but is not followed with the next synchro word;
       set 0 otherwise;
       set 0 for the other words of the subframe;

  bit D: BAD,     Location: First word of each subframe.
       set 1 if the subfrae does not begin with its synchro words;
       set 0 otherwise;
       set 0 for the other words of the subframe;

  bit C: PAD,     Location: All words.
       set 1 in the first word of the subframe if the subframe contains at least one extra word;
       set 0 otherwise;
       set 1 for each extra word
  --------------------------------------------  

根据上述的文档的描述。 理论上synchro同步字出现的顺序应该是，sync1,sync2,sync3,sync4, 间隔为 words/sec 的个数。
   author:南方航空,LLGZ@csair.com
  --------------------------
'''

实际读取文件， (bitstream format, words/sec=1024, Synchro Word Length=12bits)
  * 每次读取取单个字节，从此字节的高位移出bit，然后从12bits的word的低位移入bit，每12bits拼装成一个word。
    寻找同步字，出现的顺序没有规律。

  * 每次读取取单个字节，尝试，从此字节的低位移出bit，然后从12bits的word的高位移入bit，每12bits拼装成一个word。
    然后synchro的出现顺序似乎是反的，sync4,sync3,sync2,sync1, 它们之间的间隔为0x1000，是1024的4倍。不知道为什么.
"""
#import struct
#from datetime import datetime
import zipfile
import psutil   #非必须库
from io import BytesIO

def main():
    global FNAME,WFNAME,DUMPDATA

    print('mem:',sysmem())

    try:
        fzip=zipfile.ZipFile(FNAME,'r') #打开zip文件
    except zipfile.BadZipFile as e:
        print('ERR,FailOpenZipFile',e,FNAME,flush=True)
        raise(Exception('ERR,FailOpenZipFile'))
    filename_zip='raw.dat'
    buf=fzip.read(filename_zip)
    fzip.close()

    word_cnt=0   #12bit字计数
    word_cnt2=0  #上一个同步字的位置
    ii=0      #bit位置标记
    word=0    #12bit目标缓存
    mark=-1   #bit起始位置标记
    for bit in getbit(buf):
        ii +=1
        if ii>=12:
            ii=0
            word_cnt +=1
            if word_cnt > 500000:  #测试用，暂时读500k就结束
                break
        #word >>=1  #从高bit移入->低: >>
        word <<=1  #从低bit移入->高: <<
        if bit:
            #word |= 0x800  #从高bit移入->低: 0x800
            word |= 0x001  #从低bit移入->高: 0x1
        word &= 0xfff
        #if (ii==0 or ii==8) and mark<0 and word == 0x247:
        #if mark<0 and word in (0x247,0x5B8,0xA47,0xDB8):
        if mark<0 and word == 0x247:
            mark=ii
            print('==>Mark,%d,x%X'%(ii,word_cnt))
        if ii==mark:
            if word == 0x247:
                print('==>Found sync1.247,%d,x%X,len:x%X'%(ii,word_cnt,word_cnt-word_cnt2))
                word_cnt2=word_cnt
            elif word == 0x5B8:
                print('==>Found sync2.5B8,%d,x%X,len:x%X'%(ii,word_cnt,word_cnt-word_cnt2))
                word_cnt2=word_cnt
            elif word == 0xA47:
                print('==>Found sync3.A47,%d,x%X,len:x%X'%(ii,word_cnt,word_cnt-word_cnt2))
                word_cnt2=word_cnt
            elif word == 0xDB8:
                print('==>Found sync4.DB8,%d,x%X,len:x%X'%(ii,word_cnt,word_cnt-word_cnt2))
                word_cnt2=word_cnt
        if word_cnt-word_cnt2 >0x1000:  #512=0x200,512*4=0x800, 1024=0x400, 1024*4=0x1000
            mark=-1  #重置，重新找 sync1
            pass


    print('mem:',sysmem())


def getbit(buf):
    dat=BytesIO(buf)
    dat.read(3*1024*1024) #跳过3m内容，测试用
    while True:
        bb=dat.read(1)
        if not bb:  # when EOF, return b'', len(bb)==0
            break
        word=ord(bb)
        #chk=0x01  #先低bit->高: 0x1
        chk=0x80  #先高bit->低: 0x80
        for ii in range(8):
            if chk & word:
                yield True
            else:
                yield False
            #chk <<= 1  #先低bit->高: <<
            chk >>= 1  #先高bit->低: >>
    dat.close()
    return 'done'

def showsize(size):
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
    print('   -w xxx.dat     写入文件"xxx.dat"')
    print(u'               author:南方航空,LLGZ@csair.com')
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

