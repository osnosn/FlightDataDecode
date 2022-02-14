#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
读取 wgl 中 raw.dat 。
读解码一个参数。')
仅支持 ARINC 573/717 PCM 格式
------
https://github.com/aeroneous/PyARINC429   #py3.5
https://github.com/KindVador/A429Library  #C++

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
   * 每次读取取单个字节，定位sync1, 同步字出现顺序是 1, 2, 3, 4, 间隔为 0x400.
     文件应该是被处理，补齐。中间没有frame缺失。

 程序将按照 aligned bit format 格式读取。
"""
#import struct
#from datetime import datetime
import zipfile
import psutil         #非必需库
#from io import BytesIO
#pandas不是必需的库。获取参数返回的是dist的list表。并没有用到pandas。
import pandas as pd   #非必需库
import config_vec as conf
import read_air as AIR
import read_fra as FRA
import read_par as PAR
#from decimal import Decimal
#import arinc429  #没有使用# https://github.com/aeroneous/PyARINC429   #py3.5

class DATA:
    '用来保存配置参数的类'
    pass

def main():
    global FNAME,WFNAME,DUMPDATA
    global PARAM,PARAMLIST

    #print('mem:',sysmem())

    reg=getREG(FNAME)
    air=getAIR(reg)

    if PARAMLIST:
        #-----------列出记录中的所有参数名称--------------
        fra=getFRA(air[0],'ALT_STD')
        if len(fra)<1:
            print('Empty dataVer.')
            return
        #---regular parameter
        ii=0
        for vv in fra['2'].iloc[:,0].tolist():
            print(vv, end=',\t')
            if ii % 9 ==0:
                print()
            ii+=1
        print()
        #---superframe parameter
        ii=0
        for vv in fra['4'].iloc[:,0].tolist():
            print(vv, end=',\t')
            if ii % 9 ==0:
                print()
            ii+=1
        print()
        print('mem:',sysmem())
        return

    if PARAM is None:
        #-----------打印参数的配置内容-----------------
        for vv in ('ALT_STD','AC_TAIL7'):
            fra=getFRA(air[0],vv)
            if len(fra)<1:
                print('Empty dataVer.')
                continue
            print('parameter:',vv)
            print('Word/SEC:{0[0]}, synchro len:{0[1]} bit, sync1:{0[2]}, sync2:{0[3]}s, sync3:{0[4]}, sync4:{0[5]}, '.format(fra['1']))
            print('   superframe counter:subframe:{0[6]:<5}, word:{0[7]:<5}, bitOut:{0[8]:<5}, bitLen:{0[9]:<5}, value in 1st frame:{0[10]:<5}, '.format(fra['1']) )
            for vv in fra['2']:
                print('Part:{0[0]:<5}, recordRate:{0[1]:<5}, subframe:{0[2]:<5}, word:{0[3]:<5}, bitOut:{0[4]:<5}, bitLen:{0[5]:<5}, bitIn:{0[6]:<5}, type:{0[7]:<5}, '.format(vv) )
            print()
        print('dataVer:',air[0],air[1])
    else:
        #-----------获取一个参数--------------------
        fra =getFRA(air[0],PARAM)
        par =getPAR(air[0],PARAM)
        if len(fra)<1:
            print('Empty dataVer.')
            return
        if len(fra['2'])<1 and len(fra['4'])<1:
            print('Parameter not found.')
            return
        #print(PARAM,'(fra):',fra)
        #print(PARAM,'(par):',par)
        #print()

        print('PARAM:',PARAM)
        if len(fra['2'])>0:
            pm_list=get_param(fra,par) #获取一个参数,regular
        else:
            pm_list=get_super(fra,par) #获取一个参数,superframe
        #print(pm_list)
        print('Result[0]:',pm_list[0]) #打印第一组值
        print('DataVer:',air[0])

        df_pm=pd.DataFrame(pm_list)

        #-----------参数写入csv文件--------------------
        if WFNAME is not None and len(WFNAME)>0:
            print('Write into file "%s".' % WFNAME)
            #df_pm.to_csv(WFNAME,index=False)
            df_pm.to_csv(WFNAME,sep='\t',index=False)
            return

        pd.set_option('display.min_row',200)
        print( df_pm['v'][1000:].tolist() )

    print('mem:',sysmem())
    return

def get_super(fra,par):
    '''
    获取 superframe 参数，返回 ARINC 429 format
  -------------------------------------
  bit:|32|31|30|29|28|27|26|25|24|23|22|21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|3|2|1| 
      |  | SSM |                            DATA field                  | SDI|     label     | 
     _/  \     | MSB -->                                        <-- LSB |    |               | 
    /     \    
   |parity |   
  -------------------------------------  
    author:南方航空,LLGZ@csair.com  
    '''
    global FNAME,WFNAME,DUMPDATA

    #初始化变量
    word_sec=int(fra['1'][0])
    sync_word_len=int(fra['1'][1])//12  #整除, 同步字的字数(长度)
    sync1=int(fra['1'][2],16)  #同步字1
    sync2=int(fra['1'][3],16)
    sync3=int(fra['1'][4],16)
    sync4=int(fra['1'][5],16)
    superframe_counter_set=[{
            #counter1
            'part':1,
            'rate':1,
            'sub' :int(fra['1'][6]),
            'word':int(fra['1'][7]),
            'bout':int(fra['1'][8]),
            'blen':int(fra['1'][9]),
            'v_first':int(fra['1'][10]),
            'bin' :12,
            'occur': -1,
            },
            #counter2  没有从配置文件读入(todo)
            #{'part':1,}
            ]
    if sync_word_len>1: #如果同步字 > 1 word
        sync1=(sync1 << (12 * (sync_word_len-1))) +1  #生成长的同步字
        sync2=(sync2 << (12 * (sync_word_len-1))) +1
        sync3=(sync3 << (12 * (sync_word_len-1))) +1
        sync4=(sync4 << (12 * (sync_word_len-1))) +1

    #----------准备参数的配置-----------
    super_set=[]
    for vv in fra['3']: #全部内容变为 int
        p_set={  #临时变量
            'frameNo':int(vv[0]),
            'sub' :int(vv[1]),
            'word':int(vv[2]),
            'bout':int(vv[3]),
            'blen':int(vv[4]),
            'counterNo' :int(vv[5]),
            }
        super_set.append(p_set)
    super_set=super_set[0] #只取了第一项,通常一个super参数只会对应一个frameNo

    #----------准备参数的配置,把一个period作为一个大frame处理-----------
    superpm_set=[]
    p_set=[]  #临时变量
    last_part=0
    for vv in fra['4']: #全部内容变为 int
        vv[0]=int(vv[0]) #part
        if vv[0]<=last_part:
            #part=1,2,3 根据part分组
            superpm_set.append(p_set)
            p_set=[]
        last_part=vv[0]
        #frameNo=vv[2]   #应该由frameNo取找super_set中对应的配置,这里简单化了。
        p_set.append({
            'part':vv[0],
            'rate': 1,
            'sub' :super_set['sub'],
            'word':super_set['word'] + (int(vv[3])-1) * word_sec * 4, #subframe + (Frame-1) * word_sec *4
            'bout':int(vv[4]),  #以下两项bout,blen,应该用super_set中的设置,获取数据后,再用这里的配置取出最终bits。
            'blen':int(vv[5]),  #但是因为super_set中的内容都是12,12。所以这里就直接用了最终配置。
            'bin' :int(vv[6]),
            'occur' : -1,
            'resol': float(vv[7]), #resolution
            'period':int(vv[1]),
            })
    if len(p_set)>0: #最后一组
        superpm_set.append(p_set)

    #----------打印参数-----------
    print('Frame定义: Word/SEC:%d, syncLen(word):%d, sync1234: %X,%X,%X,%X'%(word_sec,sync_word_len,sync1,sync2,sync3,sync4) )
    print('   SuperFrame Counter:',superframe_counter_set)
    print()
    print('super_set: ',super_set )
    print('superpm: len:%d'%( len(superpm_set)) )
    for vv in superpm_set:
        print(vv)
    print('param(par):',par)
    print()

    #----------Data Type Warning-----------
    if par['type'].find('BCD')!=0 and \
            par['type'].find('BNR LINEAR (A*X)')!=0 and \
            par['type'].find('BNR SEGMENTS (A*X+B)')!=0 and \
            par['type'].find('CHARACTER')!=0 and \
            par['type'].find('DISCRETE')!=0 and \
            par['type'].find('PACKED BITS')!=0 and \
            par['type'].find('UTC')!=0 :
        print('!!!Warning!!! Data Type "%s" Decoding maybe NOT correct.\n' % (par['type']) )

    #----------打开zip压缩文件-----------
    try:
        fzip=zipfile.ZipFile(FNAME,'r') #打开zip文件
    except zipfile.BadZipFile as e:
        print('==>ERR,FailOpenZipFile',e,FNAME,flush=True)
        raise(Exception('ERR,FailOpenZipFile,%s'%FNAME))
    filename_zip='raw.dat'
    buf=fzip.read(filename_zip)
    fzip.close()

    #----------寻找起始位置-----------
    ttl_len=len(buf)
    frame_pos=0  #frame开始位置,字节指针
    frame_pos=find_SYNC1(buf, ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4) )
    if frame_pos > 0:
        print('!!!Warning!!! First SYNC at x%X, not beginning of DATA.'%(frame_pos),flush=True)
    if frame_pos >= ttl_len - sync_word_len *2:
        #整个文件都没找到同步字
        print('==>ERR, SYNC not found at end of DATA.',flush=True)
        raise(Exception('ERR,SYNC not found at end of DATA.'))

    period=superpm_set[0][0]['period']   #简单的从第一组的第一条记录中获取period

    #----------计算counter_mask-----------
    #有的库 counter 是递增 1, N个period一循环。 有的是递增 256,一个period一循环。
    #根据前后两个Frame中的counter值，确定mask。
    frame_counter  = get_arinc429(buf, frame_pos, superframe_counter_set, word_sec )
    frame_counter -= get_arinc429(buf, frame_pos + word_sec * 4 * 2, superframe_counter_set, word_sec )
    if abs(frame_counter) ==1:
        count_mask = ( 1 << int(pow(period, 0.5)) ) -1  #平方根sqrt: pow(x, 0.5) or (x ** 0.5)
        #count_mask= 0xf
    else:
        count_mask= 0
    print('counter sep:',frame_counter,period,bin(count_mask) )
    
    #----------寻找SuperFrame起始位置-----------
    val_first=super_set['counterNo'] #superframe counter 1/2
    if val_first==2: val_first=1  #counter2 没从配置中读入(todo)
    val_first=superframe_counter_set[val_first-1]['v_first']
    pm_sec=0.0   #参数的时间轴,秒数
    frame_pos,sec_add=find_FIRST_super(buf, ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4), val_first, superframe_counter_set, period, count_mask )
    pm_sec += sec_add  #加上时间增量

    #----------读参数-----------
    ii=0    #计数
    pm_list=[] #参数列表
    while True:
        # 有几个dataVer的数据,不是从文件头开始,只匹配sync1会找错。且不排除中间会错/乱。
        #所以每次都要确认first frame的位置。 实际测试,发现有同步字错误,但frame间隔正确。
        frame_pos2=frame_pos   #保存旧位置
        frame_pos,sec_add=find_FIRST_super(buf, ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4), val_first, superframe_counter_set, period, count_mask )
        pm_sec += sec_add  #加上时间增量
        if frame_pos>=ttl_len -2:
            #-----超出文件结尾，退出-----
            break

        for pm_set in superpm_set:
            #获取anrinc429,第一步应该用super_set中的bout,blen设置,获取数据后,再用superpm_set中的配置取出最终bits。
            #但是因为super_set中的内容都是12,12。所以这里就直接用了最终配置。
            value=get_arinc429(buf, frame_pos, pm_set, word_sec )  #ARINC 429 format
            value =arinc429_decode(value ,par )
            # superpm_set 中有个 resolution 似乎是无用的。AGS配置中,说是自动计算的,不让改。
            # 试着乘上去，数据就不对了。
            #if pm_set[0]['resol'] != 0.0 and pm_set[0]['resol'] != 1.0: 
            #    value *= pm_set[0]['resol']

            pm_list.append({'t':round(pm_sec,10),'v':value})
            #pm_list.append({'t':round(pm_sec,10),'v':bin(value)})
            #pm_list.append({'t':round(pm_sec,10),'v':value,'c':frame_counter})

        pm_sec += 4.0 * period  #一个frame是4秒
        frame_pos += word_sec * 4 * 2 * period   # 4subframe, 2bytes,直接跳过一个period,哪怕中间有frame错误/缺失，都不管了。
    return pm_list

def find_FIRST_super(buf, ttl_len, frame_pos, word_sec, sync_word_len, sync, val_first, superframe_counter_set, period, count_mask ):
    '''
    判断 first frame 的位置，如果不是，则向后推 1 frame再找。
    根据 superframe_counter 的内容，找到conter的值为 first value 的frame位置
       author:南方航空,LLGZ@csair.com  
    '''
    pm_sec=0.0   #参数的时间轴,秒数
    while True:
        frame_pos2=frame_pos   #保存旧位置
        frame_pos=find_SYNC1(buf, ttl_len, frame_pos, word_sec, sync_word_len, sync )  #判断同步字，或继续寻找新位置
        if frame_pos>=ttl_len -2:
            #-----超出文件结尾，退出-----
            break
        if frame_pos>frame_pos2:
            print('==>ERR, SYNC loss at x%X，refound at x%X' % (frame_pos2, frame_pos) )
            pm_sec +=4  #如果失去同步,重新同步后,时间加4秒。(这里应该根据跳过的距离确定时间增量,这里就简单粗暴了)

        frame_counter=get_arinc429(buf, frame_pos, superframe_counter_set, word_sec )
        if count_mask > 0:
            frame_counter &= count_mask
        if frame_counter==val_first:
            #print('Found first superframe at x%X, cnter:%d' % (frame_pos, frame_counter) )
            break
        else:
            print('NotFound first superframe at x%X, cnter:%d' % (frame_pos, frame_counter) )
            pm_sec += 4.0   #一个frame是4秒
            frame_pos += word_sec * 4 * 2   # 4subframe, 2bytes

    return frame_pos, pm_sec  #返回位置, 时间增量

def get_param(fra,par):
    '''
    获取 regular 参数，返回 ARINC 429 format
  -------------------------------------
  bit:|32|31|30|29|28|27|26|25|24|23|22|21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|3|2|1| 
      |  | SSM |                            DATA field                  | SDI|     label     | 
     _/  \     | MSB -->                                        <-- LSB |    |               | 
    /     \    
   |parity |   
  -------------------------------------  
    author:南方航空,LLGZ@csair.com  
    '''
    global FNAME,WFNAME,DUMPDATA

    #初始化变量
    word_sec=int(fra['1'][0])
    sync_word_len=int(fra['1'][1])//12  #整除, 同步字的字数(长度)
    sync1=int(fra['1'][2],16)  #同步字1
    sync2=int(fra['1'][3],16)
    sync3=int(fra['1'][4],16)
    sync4=int(fra['1'][5],16)
    superframe_counter_set=[{
            'part':1,
            'rate':1,
            'sub' :int(fra['1'][6]),
            'word':int(fra['1'][7]),
            'bout':int(fra['1'][8]),
            'blen':int(fra['1'][9]),
            'v_first':int(fra['1'][10]),
            'bin' :12,
            'occur': -1,
            }]
    if sync_word_len>1: #如果同步字 > 1 word
        sync1=(sync1 << (12 * (sync_word_len-1))) +1  #生成长的同步字
        sync2=(sync2 << (12 * (sync_word_len-1))) +1
        sync3=(sync3 << (12 * (sync_word_len-1))) +1
        sync4=(sync4 << (12 * (sync_word_len-1))) +1

    param_set=getDataFrameSet(fra['2'],word_sec)  #整理参数位置记录的配置

    #----------打印参数-----------
    print('Frame定义: Word/SEC:%d, syncLen(word):%d, sync1234: %X,%X,%X,%X'%(word_sec,sync_word_len,sync1,sync2,sync3,sync4) )
    print('   SuperFrame Counter:',superframe_counter_set)
    print()
    print('param(fra): len:%d'%( len(param_set)) )
    for vv in param_set:
        print(vv)
    print('param(par):',par)
    print()

    #----------Data Type Warning-----------
    if par['type'].find('BCD')!=0 and \
            par['type'].find('BNR LINEAR (A*X)')!=0 and \
            par['type'].find('BNR SEGMENTS (A*X+B)')!=0 and \
            par['type'].find('CHARACTER')!=0 and \
            par['type'].find('DISCRETE')!=0 and \
            par['type'].find('PACKED BITS')!=0 and \
            par['type'].find('UTC')!=0 :
        print('!!!Warning!!! Data Type "%s" Decoding maybe NOT correct.\n' % (par['type']) )

    #----------打开zip压缩文件-----------
    try:
        fzip=zipfile.ZipFile(FNAME,'r') #打开zip文件
    except zipfile.BadZipFile as e:
        print('==>ERR,FailOpenZipFile',e,FNAME,flush=True)
        raise(Exception('ERR,FailOpenZipFile,%s'%FNAME))
    filename_zip='raw.dat'
    buf=fzip.read(filename_zip)
    fzip.close()

    #----------寻找起始位置-----------
    ttl_len=len(buf)
    frame_pos=0  #frame开始位置,字节指针
    frame_pos=find_SYNC1(buf, ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4) )
    if frame_pos > 0:
        print('!!!Warning!!! First SYNC at x%X, not beginning of DATA.'%(frame_pos),flush=True)
    if frame_pos >= ttl_len - sync_word_len *2:
        #整个文件都没找到同步字
        print('==>ERR, SYNC not found at end of DATA.',flush=True)
        raise(Exception('ERR,SYNC not found at end of DATA.'))
    
    #----------读参数-----------
    ii=0    #计数
    pm_list=[] #参数列表
    pm_sec=0.0   #参数的时间轴,秒数
    while True:
        # 有几个dataVer的数据,不是从文件头开始,只匹配sync1会找错。且不排除中间会错/乱。
        #所以每次都要用find_SYNC1()判断。  实际测试,发现有同步字错误,但frame间隔正确。
        frame_pos2=frame_pos   #保存旧位置
        frame_pos=find_SYNC1(buf, ttl_len, frame_pos, word_sec, sync_word_len, (sync1,sync2,sync3,sync4) )  #判断同步字，或继续寻找新位置
        if frame_pos>=ttl_len -2:
            #-----超出文件结尾，退出-----
            break
        if frame_pos>frame_pos2:
            print('==>ERR, SYNC loss at x%X，refound at x%X' % (frame_pos2, frame_pos) )
            pm_sec +=4  #如果失去同步,重新同步后,时间加4秒。(这里应该根据跳过的距离确定时间增量,这里就简单粗暴了)


        sec_add = 4.0 / len(param_set)  #一个frame是4秒
        for pm_set in param_set:
            value=get_arinc429(buf, frame_pos, pm_set, word_sec )  #ARINC 429 format
            value =arinc429_decode(value ,par )

            pm_list.append({'t':round(pm_sec,10),'v':value})
            #pm_list.append({'t':round(pm_sec,10),'v':bin(value)})
            pm_sec += sec_add   #时间轴累加

        frame_pos += word_sec * 4 * 2   # 4subframe, 2bytes
    return pm_list

def find_SYNC1(buf, ttl_len, frame_pos, word_sec, sync_word_len, sync):
    '''
    判断 frame_pos 位置，是否满足同步字特征。如果不满足, 继续寻找下一个起始位置
    '''
    #ttl_len=len(buf)
    while frame_pos<ttl_len - sync_word_len *2:  #寻找frame开始位置
        #----似乎只判断连续两个同步字位置正确, 就够了-----
        if getWord(buf,frame_pos, sync_word_len) == sync[0] and \
                getWord(buf,frame_pos+word_sec*2,sync_word_len) == sync[1] :
        #if getWord(buf,frame_pos, sync_word_len) == sync[0] and \
        #        getWord(buf,frame_pos+word_sec*2,sync_word_len) == sync[1] and \
        #        getWord(buf,frame_pos+word_sec*4,sync_word_len) == sync[2] and \
        #        getWord(buf,frame_pos+word_sec*6,sync_word_len) == sync[3] :
            #print('==>Mark,x%X'%(frame_pos,))
            break
        frame_pos +=1
    return frame_pos

def getDataFrameSet(fra2,word_sec):
    '''
    整理参数在arinc717位置记录的配置(在12 bit word中的位置)
    如果不是 self-distant , 会有每个位置的配置。 对所有的位置记录分组。
        需要根据rate值，补齐其他的subframe。
        比如:rate=4, 就是1-4subframe都有。rate=2，就是在1,3或2,4subframe中。
    如果是 self-distant , 只有第一个位置的配置。 根据 rate, 补齐所有的位置记录，并分组。
        需要根据rate值，补齐其他的subframe, 和word位置。
        subframe的补齐同上，word的间隔是,用 word/sec除以记录数确定。在每个subframe中均匀分部的。
        author:南方航空,LLGZ@csair.com  
    '''
    # ---分组---
    group_set=[]
    p_set=[]  #临时变量
    last_part=0
    for vv in fra2:
        vv[0]=int(vv[0]) #part
        if vv[0]<=last_part:
            #part=1,2,3 根据part分组
            group_set.append(p_set)
            p_set=[]
        last_part=vv[0]
        #rate: 1=1/4HZ(一个frame一个记录), 2=1/2HZ, 4=1HZ(每个subframe一个记录), 8=2HZ, 16=4HZ, 32=8HZ(每个subframe有8条记录)
        p_set.append({
            'part':vv[0],
            'rate':int(vv[1]),
            'sub' :int(vv[2]),
            'word':int(vv[3]),
            'bout':int(vv[4]),
            'blen':int(vv[5]),
            'bin' :int(vv[6]),
            'occur' :int(vv[7]) if len(vv[7])>0 else -1,
            })
    if len(p_set)>0: #最后一组
        group_set.append(p_set)

    # --------打印 分组配置----------
    #print('分组配置: len:%d'%(len(group_set) ) )
    #for vv in group_set:
    #    print(vv)

    # --------根据rate补齐记录-------
    param_set=[]
    frame_rate=group_set[0][0]['rate']
    if frame_rate>4:
        frame_rate=4           #一个frame中占几个subframe
    subf_sep=4//frame_rate  #整除
    for subf in range(0,4,subf_sep):  #补subframe, 仅根据第一条记录的rate补
        for group in group_set:
            frame_rate=group[0]['rate']
            if frame_rate>4:
                sub_rate=frame_rate//4  #一个subframe中有几个记录 ,整除
            else:
                sub_rate=1
            word_sep=word_sec//sub_rate  #整除
            for word_rate in range(sub_rate):  #补word, 根据分组记录的第一条rate补
                p_set=[]  #临时变量
                for vv in group:
                    p_set.append({
                        'part':vv['part'],
                        'rate':vv['rate'],
                        'sub' :vv['sub']+subf,
                        'word':vv['word']+word_rate*word_sep,
                        'bout':vv['bout'],
                        'blen':vv['blen'],
                        'bin' :vv['bin'],
                        'occur':vv['occur'],
                        })
                param_set.append(p_set)
    return param_set

def arinc429_decode(word,conf):
    '''
    par可能有的 Type: 'CONSTANT' 'DISCRETE' 'PACKED BITS' 'BNR LINEAR (A*X)' 'COMPUTED ON GROUND' 'CHARACTER' 'BCD' 'BNR SEGMENTS (A*X+B)' 'UTC'
    par实际有的 Type: 'BNR LINEAR (A*X)' 'BNR SEGMENTS (A*X+B)' 'CHARACTER' 'BCD' 'UTC' 'PACKED BITS'
        author:南方航空,LLGZ@csair.com  
    '''
    if conf['type'].find('BNR')==0 or \
            conf['type'].find('PACKED BITS')==0:
        return arinc429_BNR_decode(word ,conf)
    elif conf['type'].find('BCD')==0 or \
            conf['type'].find('CHARACTER')==0:
        return arinc429_BCD_decode(word ,conf)
    elif conf['type'].find('UTC')==0:
        val=arinc429_BNR_decode(word ,conf)
        ss= val & 0x3f         #6bits
        mm= (val >>6) & 0x3f   #6bits
        hh= (val >>12) & 0x1f  #5bits
        return '%02d:%02d:%02d' % (hh,mm,ss)
    else:
        return arinc429_BNR_decode(word ,conf)

def arinc429_BCD_decode(word,conf):
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

def arinc429_BNR_decode(word,conf):
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
    else:
        #----已知 PACKED BITS, UTC, DISCRETE, 就应该按 BNR 处理---
        #其他不能识别的类型，默认按BNR处理
        #在此，无需给出错误提示
        pass
    return value 

def get_arinc429(buf, frame_pos, param_set, word_sec ):
    '''
    根据 fra的配置，获取arinc429格式的32bit word
      另:fra 配置中有多条不同的记录,对应多个32bit word(完成)
      bit位置，是从1开始编号。word位置也是从1开始编号。同步字位置为1，数据字是从2开始编号(假设同步字只占1word)。
    author:南方航空,LLGZ@csair.com
    '''
    value=0
    pre_id=0
    for pm_set in param_set:
        #if pm_set['part']>pre_id:  #有多组配置，只执行第一组。//配置经过整理，只剩一组了。
        #    pre_id=pm_set['part']
        #else:
        #    break
        word=getWord(buf,
                frame_pos + word_sec *2 *(pm_set['sub']-1) +(pm_set['word']-1)*2  #同步字所占的位置,编号为1,所以要-1
                )
        #根据blen，获取掩码值
        bits= (1 << pm_set['blen']) -1
        #根据bout，把掩码移动到对应位置
        bits <<= pm_set['bout'] - pm_set['blen']
        word &= bits  #获取值
        #把值移动到目标位置
        move=pm_set['bin'] - pm_set['bout']
        if move>0:
            word <<= move
        elif move<0:
            word >>= -1 * move
        value |= word
    return value

def getWord(buf,pos, word_len=1):
    '''
    读取两个字节，取12bit为一个word。低位在前。littleEndian,low-byte first.
    支持取 12bits,24bits,36bits,48bits,60bits
       author:南方航空,LLGZ@csair.com
    '''
    #print(type(buf), type(buf[pos]), type(buf[pos+1])) #bytes, int, int

    ttl=len(buf)  #读数据的时候,开始位置加上subframe和word的偏移，可能会超限
    if word_len==1:
        if pos+1 >= ttl:
            return 0  #超限返回0
        else:
            return ((buf[pos +1] << 8 ) | buf[pos] ) & 0xFFF

    #word_len>1 //只有获取大于1个word 的同步字,才有用
    word=0
    for ii in range(0,word_len):
        if pos+ii*2+1 >= ttl:
            high = 0
        else:
            high = ((buf[pos+ii*2+1] << 8 ) | buf[pos +ii*2] ) & 0xFFF
        word |= high << (12 * ii)
    return word

def getPAR(dataver,param):
    '''
    获取参数在arinc429的32bit word中的位置配置
    挑出有用的,整理一下,返回
       author:南方航空,LLGZ@csair.com
    '''
    global DATA
    if not hasattr(DATA,'par'):
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

def getFRA(dataver,param):
    '''
    获取参数在arinc717的12bit word中的位置配置
    挑出有用的,整理一下,返回
       author:南方航空,LLGZ@csair.com
    '''
    global PARAMLIST
    global DATA

    if not hasattr(DATA,'fra'):
        DATA.fra=FRA.read_parameter_file(dataver)
    if DATA.fra is None:
        return {}

    if PARAMLIST:
        return DATA.fra

    ret2=[]  #for regular
    ret3=[]  #for superframe
    ret4=[]  #for superframe pm
    if len(param)>0:
        param=param.upper() #改大写
        #---find regular parameter----
        tmp=DATA.fra['2']
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
        tmp=DATA.fra['4']
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
            tmp=DATA.fra['3']
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
                DATA.fra['1'].iat[1,1],  #Word/Sec
                DATA.fra['1'].iat[1,2],  #sync length
                DATA.fra['1'].iat[1,3],  #sync1
                DATA.fra['1'].iat[1,4],  #sync2
                DATA.fra['1'].iat[1,5],  #sync3
                DATA.fra['1'].iat[1,6],  #sync4
                DATA.fra['1'].iat[1,7],  #subframe, [superframe counter]
                DATA.fra['1'].iat[1,8],  #word
                DATA.fra['1'].iat[1,9],  #bitOut
                DATA.fra['1'].iat[1,10], #bitLen
                DATA.fra['1'].iat[1,11], #Value in 1st frame (0/1)
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
        return [0,0,0]

def getREG(fname):
    '''
    从zip文件名中，找出机尾号
       author:南方航空,LLGZ@csair.com
    '''
    tmp=fname.strip().split('_',1)
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
    print(u' 读取 wgl中 raw.dat,根据参数编码规则,解码一个参数。')

    print(sys.argv[0]+' [-h|--help]')
    print('   * (必要参数)')
    print('   -h, --help                 print usage.')
    print(' * -f, --file xxx.wgl.zip     "....wgl.zip" filename')
    print(' * -p, --param alt_std        show "ALT_STD" param. 自动全部大写。')
    print('   --paramlist                list all param name.')
    print('   -w xxx.csv            参数写入文件"xxx.csv"')
    print('   -w xxx.csv.gz         参数写入文件"xxx.csv.gz"')
    print(u'\n               author:南方航空,LLGZ@csair.com')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hw:df:p:',['help','file=','paramlist','param=',])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    WFNAME=None
    DUMPDATA=False
    PARAMLIST=False
    PARAM=None
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
        elif op in('--paramlist',):
            PARAMLIST=True
        elif op in('-p','--param',):
            PARAM=value
    if len(args)>0:  #命令行剩余参数
        FNAME=args[0]  #只取第一个
    if FNAME is None:
        usage()
        exit()
    if os.path.isfile(FNAME)==False:
        print(FNAME,'Not a file')
        exit()

    main()

