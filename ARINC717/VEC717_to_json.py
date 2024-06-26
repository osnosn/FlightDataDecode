#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
读取VEC 配置，输出json格式的配置

仅支持 ARINC 573/717 Aligned 格式
  --------------------------------------------  
   author: osnosn@126.com
  --------------------------
"""
import config_vec as conf
import read_fra as FRA
import read_par as PAR
import gzip
import json
#import pandas as pd

class ARINC717():
    '''
    从 ARINC 573/717 ALIGNED 格式文件中，获取参数
    '''
    def __init__(self,dataver):
        '''
        用来保存配置参数的实例变量
        '''
        self.fra=None
        self.fra_dataver=-1
        self.par=None
        self.par_dataver=-1
        if len(dataver)>0:
            self.dataver(dataver)

    def dataver(self,dataver):
        self.readFRA(dataver)
        self.readPAR(dataver)

    def get_param(self, parameter):
        fra =self.getFRA(parameter)
        par =self.getPAR(parameter)
        if len(fra)<1:
            print('Empty dataVer.',flush=True)
            return fra,par
        if len(fra['2'])<1 and len(fra['4'])<1:
            print('Parameter not found.',flush=True)
            return fra,par
        return fra,par

    def getDataFrameSet(self,fra2,word_sec):
        '''
        整理参数在arinc717位置记录的配置(在12 bit word中的位置)
        如果不是 self-distant , 会有每个位置的配置。 对所有的位置记录分组。
            需要根据rate值，补齐其他的subframe。
            比如:rate=4, 就是1-4subframe都有。rate=2，就是在1,3或2,4subframe中。
        如果是 self-distant , 只有第一个位置的配置。 根据 rate, 补齐所有的位置记录，并分组。
            需要根据rate值，补齐其他的subframe, 和word位置。
            subframe的补齐同上，word的间隔是,用 word/sec除以记录数确定。在每个subframe中均匀分部的。
            author: osnosn@126.com  
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
                            'sub' :0 if subf_sep==1 else vv['sub']+subf , #4个subframe都有,则设subframe=0
                            'word':vv['word']+word_rate*word_sep,
                            'bout':vv['bout'],
                            'blen':vv['blen'],
                            'bin' :vv['bin'],
                            'occur':vv['occur'],
                            })
                    param_set.append(p_set)
            if subf_sep ==1:
                #4个subframe都有,则设subframe=0,无需继续填写其他subframe
                break
        return param_set

    def readPAR(self,dataver):
        '读 par 配置'
        if isinstance(dataver,(str,float)):
            dataver=int(dataver)
        if self.par is None or self.par_dataver != dataver: #有了就不重复读
            self.par=PAR.read_parameter_file(dataver)
            self.par_dataver = dataver

    def getPAR(self,param):
        '''
        获取参数在arinc429的32bit word中的位置配置
        挑出有用的,整理一下,返回
           author: osnosn@126.com
        '''
        self.readPAR(self.par_dataver)
        if self.par is None or len(self.par)<1:
            return {}
        param=param.upper()  #改大写
        pm_find=None  #临时变量
        for row in self.par:  #找出第一条匹配的记录, par中只会有一条记录
            if row[0] == param:
                pm_find=row
                break
        if pm_find is None:
            return {}
        else:
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

    def readFRA(self,dataver):
        '读 fra 配置'
        if isinstance(dataver,(str,float)):
            dataver=int(dataver)
        if self.fra is None or self.fra_dataver != dataver: #有了就不重复读
            self.fra=FRA.read_parameter_file(dataver)
            self.fra_dataver = dataver

    def getFRA(self,param):
        '''
        获取参数在arinc717的12bit word中的位置配置
        挑出有用的,整理一下,返回
           author: osnosn@126.com
        '''
        self.readFRA(self.fra_dataver)
        if self.fra is None:
            print('Empty dataVer.',flush=True)
            return {}

        ret2=[]  #for regular
        ret3=[]  #for superframe
        ret4=[]  #for superframe pm
        if len(param)>0:
            param=param.upper() #改大写
            #---find regular parameter----
            tmp=self.fra['2']
            idx=[]
            ii=0
            for row in tmp: #找出所有记录,一个参数会有多条记录
                if row[0] == param: idx.append(ii)
                ii +=1

            if len(idx)>0:  #找到记录
                for ii in idx:
                    tmp2=[  #regular 参数配置
                        tmp[ii][1],   #part(1,2,3),会有多组记录,对应返回多个32bit word. 同一组最多3个part,3个part分别读出,写入同一个32bit word.
                        tmp[ii][2],   #recordRate, 记录频率(记录次数/Frame)
                        tmp[ii][3],   #subframe, 位于哪个subframe(1-4)
                        tmp[ii][4],   #word, 在subframe中第几个word(sync word编号为1)
                        tmp[ii][5],   #bitOut, 在12bit中,第几个bit开始
                        tmp[ii][6],   #bitLen, 共几个bits
                        tmp[ii][7],   #bitIn,  写入arinc429的32bits word中,从第几个bits开始写
                        tmp[ii][12],  #Occurence No
                        tmp[ii][8],   #Imposed,Computed
                        ]
                    ret2.append(tmp2)
            #---find superframe parameter----
            tmp=self.fra['4']
            idx=[]
            ii=0
            for row in tmp: #找出所有记录
                if row[0] == param: idx.append(ii)
                ii +=1

            if len(idx)>0:  #找到记录
                superframeNo=tmp[ idx[0] ][3] #取找到的第一条记录中的值
                for ii in idx:
                    tmp2=[ #superframe 单一参数记录
                        tmp[ii][1],   #part(1,2,3),会有多组记录,对应返回多个32bit word. 同一组最多3个part,3个part分别读出,写入同一个32bit word.
                        tmp[ii][2],   #period, 周期,每几个frame出现一次
                        tmp[ii][3],   #superframe no, 对应"superframe全局配置"中的superframe no
                        tmp[ii][4],   #Frame,  位于第几个frame (由superframe counter,找出编号为1的frame)
                        tmp[ii][5],   #bitOut, 在12bit中,第几个bit开始
                        tmp[ii][6],   #bitLen, 共几个bits
                        tmp[ii][7],   #bitIn,  写入arinc429的32bits word中,从第几个bits开始写
                        tmp[ii][10],  #resolution, 未用到
                        ]
                    ret4.append(tmp2)
                tmp=self.fra['3']
                idx=[]
                ii=0
                for row in tmp: #找出所有记录
                    if row[0] == superframeNo: idx.append(ii)
                    ii +=1

                if len(idx)>0:  #找到记录,通常一定会有记录
                    for ii in idx:
                        tmp2=[ #superframe 全局配置
                            tmp[ii][0],   #superframe no
                            tmp[ii][1],   #subframe, 位于哪个subframe(1-4)
                            tmp[ii][2],   #word, 在subframe中第几个word(sync word编号为1)
                            tmp[ii][3],   #bitOut, 在12bit中,第几个bit开始(通常=12)
                            tmp[ii][4],   #bitLen, 共几个bits(通常=12)
                            tmp[ii][5],   #superframe couter 1/2, 对应Frame总配置中的第几个counter
                            ]
                        ret3.append(tmp2)

        return { '1':
                [  #Frame 总配置, 最多两条记录(表示有两个counter)
                    self.fra['1'][1][1],  #Word/Sec, 每秒的word数量,即 word/subframe
                    self.fra['1'][1][2],  #sync length, 同步字长度(bits=12,24,36)
                    self.fra['1'][1][3],  #sync1, 同步字,前12bits
                    self.fra['1'][1][4],  #sync2
                    self.fra['1'][1][5],  #sync3
                    self.fra['1'][1][6],  #sync4
                    self.fra['1'][1][7],  #subframe, [superframe counter],每个frame中都有,这4项是counter的位置
                    self.fra['1'][1][8],  #word,     [superframe counter]
                    self.fra['1'][1][9],  #bitOut,   [superframe counter]
                    self.fra['1'][1][10], #bitLen,   [superframe counter]
                    self.fra['1'][1][11], #Value in 1st frame (0/1), 编号为1的frame,counter的值(counter的最小值)
                    ],
                 '2':ret2,
                 '3':ret3,
                 '4':ret4,
                }

    def paramlist(self):
        '''
        获取所有的记录参数名称，包括 regular 和 superframe 参数
        这里需要对这两个列表, 去重. 因为有重复的参数名
        '''
        if self.fra is None:
            print('Empty dataVer.',flush=True)
            return [],[]
        #---regular parameter
        regular_list=[]
        for vv in self.fra['2']:
            if vv[0] not in regular_list: #去重
                regular_list.append(vv[0])
        #---superframe parameter
        super_list=[]
        for vv in self.fra['4']:
            if vv[0] not in super_list: #去重
                super_list.append(vv[0])
        return regular_list,super_list
    def dataVer(self):
        '''
        获取当前文件的 DataVer
        '''
        return self.fra_dataver
    def close(self):
        '清除,保留的所有配置和数据'
        self.fra=None
        self.fra_dataver=-1
        self.par=None
        self.par_dataver=-1
    def to_dict(self):
        fra=self.fra
        SFperCycle=0
        if len(fra['4'])>1:
            tmp=[int(xx[2]) if xx[2].isdigit() else -1 for xx in fra['4'] ]  #超级参数的period值
            tmp2={}  #分别统计值出现的次数
            for key in tmp:
                tmp2[key]=tmp2.get(key,0)+1
            #print(tmp2,max(tmp2,key=tmp2.get), max(tmp2,key=lambda x:tmp2[x]))
            SFperCycle=max(tmp2,key=tmp2.get)  #取最多的值
            #SFperCycle=max(tmp)  #取最大值
        WordPerSec=int(fra['1'][1][1])
        VecConf={
                "WordPerSec": WordPerSec,
                "SyncBitLen":int(fra['1'][1][2]),
                "SyncWords": [
                    int(fra['1'][1][3],16),
                    int(fra['1'][1][4],16),
                    int(fra['1'][1][5],16),
                    int(fra['1'][1][6],16),
                    ],
                "SuperFramePerCycle": SFperCycle,
                "param": {
                    "SuperFrameCounter": {
                        #words: [ superFrame,subframe,word,lsb,msb,targetBit]
                        "words": [[
                            0, #为0, superFrame
                            int(fra['1'][1][7]),
                            int(fra['1'][1][8]),
                            int(fra['1'][1][9])-int(fra['1'][1][10])+1,
                            int(fra['1'][1][9]),
                            0,
                            ]],
                        "FirstValue": int(fra['1'][1][11]),
                        "res": [],
                        "signed": False,
                        "signRecType": False,
                        "superframe": 0,
                        "RecFormat": "BNR",
                        "ConvConfig": [],
                        "Unit": "",
                        "LongName": "SUPER FRAME COUNTER"
                        }
                    }
                }
        regularlist,superlist=self.paramlist() #已经去重
        print('------- regularlist 部分 ----------',file=sys.stderr,flush=True)
        regularlist.pop(0) #去除第一项 "Regular Parameter Name"
        fra_2=self.fra['2']
        for param in regularlist:
            #---find regular parameter----
            idx=[]
            ii=0
            for row in fra_2: #找出所有记录,一个参数会有多条记录
                if row[0] == param: idx.append(ii)
                ii +=1
            pm_fra=self.getFRA(param)
            if len(idx)<1 or len(pm_fra['2'])<1:
                #通常,不会找不到
                print('ERROR,',param,'NotFound',file=sys.stderr)
                continue
            pmset=self.getDataFrameSet(pm_fra['2'],WordPerSec)

            #---从par中找到记录---
            #par=self.getPAR(param) #没使用这个函数
            par=None
            for row in self.par:  #找出第一条匹配的记录, par中只会有一条记录
                if row[0] == param:
                    par=row
                    break
            if par is None:
                print("ERROR, NotFound par中没找到记录",param,file=sys.stderr)
                continue #regularlist:
                #break
            VecConf["param"][param]={
                #words: [ superFrame,subframe,word,lsb,msb,targetBit]
                "words": [],
                #res: 系数 A,B,C; 转换公式, A+B*X+C*X*X
                #res: [MinValue, MaxValue, resolutionA, resolutionB, resolutionC]
                "res": [],
                "signed":      True if len(par[6])>0 and int(par[6])>0 else False, #signBit
                #不用了"signRecType": True if len(par[6])>0 and int(par[6])>0 else False, #signBit
                "superframe": 0,
                "RecFormat": par[2], #Type (BCD,CHARACTER)
                #ConvConfig: 类型为BCD/ISO，每一位"数字/字符"占用的bit数
                "ConvConfig": [],
                "Unit": '',
                "LongName": par[1].strip(),

                "rate": 0,
                "FlagType": 0,
                "range": [],
                "rawRes": [],
                #Options: 类型为DIS，枚举值
                "Options": [],
                }
            VecConf["param"][param]['range'].append([
                float(par[15]),
                float(par[16]),
                ]) #operational range(Min,Max)
            resol=par[12]
            if len(resol)<1:
                resol=1.0
            elif resol.find('Resol=')==0:
                resol=float(resol[6:])
            else:
                print('resol:',resol,file=sys.stderr)
            #要根据fra中bitLen, 和par中MSB,bitLen调整系数，通常需要调整为原系数的2,4,8倍
            offset=0.0
            if par[11]=='0':
                pass
            elif par[11]=='100':
                offset=100.0
                if resol==1.0:
                    resol=0.01
                else:
                    print('offset=100; resol=',resol,file=sys.stderr)
                    #resol *=0.01
            elif len(par[11])>0:
                print('offset:',par[11],file=sys.stderr)
                offset=float(par[11])
            ## 需要用 fra中的bitIn,对比 par中MSB,bitLen 重新计算target值，
            resol_corr=self.correct_regular(param,pmset,par)
            # 因为fra中同一组的多个部分,bit会有重叠, 放入arinc429后,按par取值,会有错位
            # target值经过重新计算后,按需调整resol的值
            VecConf["param"][param]['res'].append([
                float(par[13]),
                float(par[14]),
                offset,
                resol * resol_corr,
                0.0,
                ]) #[WordMin,WordMax,Offset,Resol,0 ]
            for group in pmset:
                #group.reverse() #倒序
                group.sort(key=lambda x:x['bin']) #按bin排序
                one_set=[]
                for Iset in group:
                    one_set.extend([
                        0, #superFrame, 对于普通参数,为0
                        int(Iset['sub']),   #subframe, 位于哪个subframe(1-4)
                        int(Iset['word']),   #word, 在subframe中第几个word(sync word编号为1)
                        int(Iset['bout'])-int(Iset['blen'])+1,  #bitLen
                        int(Iset['bout']),   #bitOut,MSB 在12bit中,第几个bit开始
                        int(Iset['bin']),   #bitIn,  写入arinc429的32bits word中,从第几个bits开始写
                        ])
                VecConf["param"][param]['words'].append(one_set)
            for ii in idx:
                # rawRes取值位置，ragula与super不同,一个是8,9,10一个是 9,10,11
                VecConf["param"][param]['rawRes'].append([
                    float(fra_2[ii][9]) if len(fra_2[ii][9])>0 else 0,
                    float(fra_2[ii][10]) if len(fra_2[ii][10])>0 else 0,
                    float(fra_2[ii][11])
                    ]) #[min,max,resolution]
                VecConf["param"][param]['rate']=int(fra_2[ii][2])
            if isinstance(par[38], list):
                #如果有多个部分的bits的配置, 组合一下
                for ii in range(len(par[36])):
                    VecConf["param"][param]['ConvConfig'].append(int(par[38][ii]))
            elif isinstance(par[38], str) and len(par[38])>0:
                VecConf["param"][param]['ConvConfig'].append(int(par[38]))
            if isinstance(par[39], list):
                #如果有多个Option的配置, 组合一下
                for ii in range(len(par[39])):
                    VecConf["param"][param]['Options'].append(( int(par[39][ii]),par[40][ii] ))
            #检查一下
            if VecConf["param"][param]['RecFormat'].find('BCD')>=0 and len(VecConf["param"][param]['ConvConfig'])<1:
                print(' =>ERROR, {}, BCD has no ConvConfig'.format(param),file=sys.stderr)
            elif VecConf["param"][param]['RecFormat'].find('DIS')>=0 and len(VecConf["param"][param]['Options'])<1:
                print(' =>ERROR, {}, DISCRETE has no Options'.format(param),file=sys.stderr)
            #pass #regularlist:

        fra_3=self.fra['3']
        VecConf['SuperFramePosInfo']=fra_3.pop(0) #第一行是说明,保存在json中
        #SuperFramePos 的编号不是连续的
        SuperFramePos={}
        for vv in fra_3:
            SuperFramePos[int(vv[0])]=[int(xx) for xx in vv]
        VecConf['SuperFramePos']=SuperFramePos

        print('------- superlist 部分 ----------',file=sys.stderr,flush=True)
        superlist.pop(0) #去除第一项 "Superframe Parameter Name"
        fra_4=self.fra['4']
        for param in superlist:
            #---find superframe parameter----
            idx=[]
            ii=0
            for row in fra_4: #找出所有记录,一个参数会有多条记录
                if row[0] == param: idx.append(ii)
                ii +=1

            pm_fra=self.getFRA(param)
            if len(idx)<1 or len(pm_fra['4'])<1:
                #通常,不会找不到
                print('ERROR,',param,'NotFound',file=sys.stderr)
                continue
            if len(idx)>1:
                #有多条记录的
                print(param,idx,file=sys.stderr)

            #---从par中找到记录---
            #par=self.getPAR(param) #没有使用此函数
            par=None
            for row in self.par:  #找出第一条匹配的记录, par中只会有一条记录
                if row[0] == param:
                    par=row
                    break
            if par is None:
                print("ERROR, NotFound par中没找到记录",param,file=sys.stderr)
                continue #superlist:
                #break
            VecConf["param"][param]={
                #words: [ superFrame,subframe,word,lsb,msb,targetBit]
                "words": [],
                #res: 系数 A,B,C; 转换公式, A+B*X+C*X*X
                #res: [MinValue, MaxValue, resolutionA, resolutionB, resolutionC]
                "res": [],
                "signed":      True if len(par[6])>0 and int(par[6])>0 else False, #signBit
                #不用了"signRecType": True if len(par[6])>0 and int(par[6])>0 else False, #signBit
                "superframe": 0,
                "RecFormat": par[2], #Type (BCD,CHARACTER)
                #ConvConfig: 类型为BCD/ISO，每一位"数字/字符"占用的bit数
                "ConvConfig": [],
                "Unit": '',
                "LongName": par[1].strip(),

                "rate": 0,
                "FlagType": 0,
                "range": [],
                "rawRes": [],
                #Options: 类型为DIS，枚举值
                "Options": [],
                }
            VecConf["param"][param]['range'].append([
                float(par[15]),
                float(par[16]),
                ]) #operational range(Min,Max)
            resol=par[12]
            if len(resol)<1:
                resol=1.0
            elif resol.find('Resol=')==0:
                resol=float(resol[6:])
            else:
                print('resol:',resol,file=sys.stderr)
            offset=0.0
            if par[11]=='0':
                pass
            elif par[11]=='100':
                offset=100.0
                if resol==1.0:
                    resol=0.01
                else:
                    print('offset=100; resol=',resol,file=sys.stderr)
                    #resol *=0.01
            elif len(par[11])>0:
                print('offset:',par[11],file=sys.stderr)
                offset=float(par[11])
            pm_fra4=pm_fra['4']
            resol_corr=self.correct_super(param,pm_fra4,par)
            VecConf["param"][param]['res'].append([
                float(par[13]),
                float(par[14]),
                offset,
                resol * resol_corr,
                0,
                ]) #[WordMin,WordMax,Offset,Resol,0 ]
            superframe_old=0
            #对于super参数,应该都放入同一组中, 通常super参数, 在一个循环中只记录一次
            '''
            #分组 words
            # super参数, 如果有多个部分，通常都不在同一个superFrameCounter中, 也不在相同的subFrame中
            one_set=[]
            last_part=0
            for Iset in pm_fra4:
                Iset[0]=int(Iset[0])
                if Iset[0]<=last_part:
                    #part=1,2,3 根据part分组
                    one_set.sort(key=lambda x:x[5]) #6个一组,按bitIn排序
                    #展开one_set到一维数组, 两种方法
                    #VecConf["param"][param]['words'].append([i for j in one_set for i in j])
                    VecConf["param"][param]['words'].append(sum(one_set, []))
                    one_set=[]
                last_part=Iset[0]
                one_set.append([
                    #int(Iset[2]),   #SuperframeNo
                    int(Iset[3]), #superFrame
                    SuperFramePos[int(Iset[2])][1], #subframe, 位于哪个subframe(1-4)
                    SuperFramePos[int(Iset[2])][2], #word, 在subframe中第几个word(sync word编号为1)
                    int(Iset[4])-int(Iset[5])+1, #bitLen
                    int(Iset[4]),   #bitOut,MSB 在12bit中,第几个bit开始
                    int(Iset[6]),   #bitIn,  写入arinc429的32bits word中,从第几个bits开始写
                    #SuperFramePos[int(Iset[2])][3], #BitOut
                    #SuperFramePos[int(Iset[2])][4], #DataBits=bitLen
                    ])
            if len(one_set)>0: #最后一组
                one_set.sort(key=lambda x:x[5]) #6个一组,按bitIn排序
                VecConf["param"][param]['words'].append(sum(one_set, []))
            '''
            #不分组 words
            # super参数, 如果有多个部分，通常都不在同一个superFrameCounter中, 也不在相同的subFrame中
            one_set=[]
            for Iset in pm_fra4:
                one_set.append([
                    #int(Iset[2]),   #SuperframeNo
                    int(Iset[3]), #superFrame
                    SuperFramePos[int(Iset[2])][1], #subframe, 位于哪个subframe(1-4)
                    SuperFramePos[int(Iset[2])][2], #word, 在subframe中第几个word(sync word编号为1)
                    int(Iset[4])-int(Iset[5])+1, #bitLen
                    int(Iset[4]),   #bitOut,MSB 在12bit中,第几个bit开始
                    int(Iset[6]),   #bitIn,  写入arinc429的32bits word中,从第几个bits开始写
                    #SuperFramePos[int(Iset[2])][3], #BitOut
                    #SuperFramePos[int(Iset[2])][4], #DataBits=bitLen
                    ])
            #part=1,2,3 根据part分组
            one_set.sort(key=lambda x:x[5]) #6个一组,按bitIn排序
            #展开one_set到一维数组, 两种方法
            #VecConf["param"][param]['words'].append([i for j in one_set for i in j])
            VecConf["param"][param]['words'].append(sum(one_set, []))

            for ii in idx:
                # rawRes取值位置，ragula与super不同,一个是8,9,10一个是 9,10,11
                VecConf["param"][param]['rawRes'].append([
                    float(fra_4[ii][8]) if len(fra_4[ii][8])>0 else 0,
                    float(fra_4[ii][9]) if len(fra_4[ii][9])>0 else 0,
                    float(fra_4[ii][10])
                    ]) #[min,max,resolution]
                VecConf["param"][param]['rate']=int(fra_4[ii][1]) * -1 #Period of
                VecConf["param"][param]['period']=int(fra_4[ii][1]) #Period of
                VecConf["param"][param]['superframe']=int(fra_4[ii][4]) #superFrame
                if superframe_old<=0:
                    superframe_old=int(fra_4[ii][4])
                elif superframe_old != int(fra_4[ii][4]):
                    print(' =>ERROR,多个取值不在同一个SuperFrame中,{}->{}, {}'.format(superframe_old,int(fra_4[ii][4]),param,),file=sys.stderr)
                    superframe_old=int(fra_4[ii][4])
                if int(fra_4[ii][4])<1:
                    print(' =>ERROR,{},SuperFrame=0,{}->{}'.format(param,superframe_old,int(fra_4[ii][4])),file=sys.stderr)
            if isinstance(par[38], list):
                #如果有多个部分的bits的配置, 组合一下
                for ii in range(len(par[36])):
                    VecConf["param"][param]['ConvConfig'].append(int(par[38][ii]))
            elif isinstance(par[38], str) and len(par[38])>0:
                VecConf["param"][param]['ConvConfig'].append(int(par[38]))
            if isinstance(par[39], list):
                #如果有多个Option的配置, 组合一下
                for ii in range(len(par[39])):
                    VecConf["param"][param]['Options'].append(( int(par[39][ii]),par[40][ii] ))
            #检查一下
            if VecConf["param"][param]['RecFormat'].find('BCD')>=0 and len(VecConf["param"][param]['ConvConfig'])<1:
                print(' =>ERROR, {}, BCD has no ConvConfig'.format(param),file=sys.stderr)
            elif VecConf["param"][param]['RecFormat'].find('DIS')>=0 and len(VecConf["param"][param]['Options'])<1:
                print(' =>ERROR, {}, DISCRETE has no Options'.format(param),file=sys.stderr)
            #pass #superlist:

        #print(regularlist)
        #print(superlist)
        return VecConf
    def correct_regular(self,param,fra,par):
        '''
        可以对 fra,par 的内容直接修改，因为是引用参数
        -------------
        需要用 fra中的bitIn,对比 par中MSB,bitLen 重新计算target值，
        因为fra中同一组的多个部分,bit会有重叠, 放入arinc429后,按par取值,会有错位
        target值经过重新计算后,按需调整resol的值, 通常是2,4,8倍
        '''
        #print('----',param,'----')
        #print(fra)
        #fra[0][0]['bout']=99   #在这里修改,有效
        resol_corr=1.0  #默认值
        ii=0
        for group in fra:
            ii+=1
            gMsb=0
            gLsb=31
            group.sort(key=lambda x:x['bin']) #按bin排序
            for one in group:
                #one['bout']=99   #在这里修改,也有效
                oMsb=one['bin']
                oLsb=one['bin']-one['blen']+1
                #if (oMsb>=gLsb and oMsb<=gMsb):
                #    print('==ERR1a=={},Msb重叠: 当前,{}-{}, 加入,{}-{}'.format(param,gMsb,gLsb,oMsb,oLsb),file=sys.stderr)
                if(oLsb>=gLsb and oLsb<=gMsb):
                    #按bin排序后，只会出现Lsb重叠
                    print('==ERR1b=={},Lsb重叠: 当前,{}-{}, 加入,{}-{}'.format(param,gMsb,gLsb,oMsb,oLsb),file=sys.stderr)
                    one['blen'] -= gMsb-oLsb+1
                    print('==ERR1b=={},Lsb  改: 当前,{}-{}, 加入,{}-{}'.format(param,gMsb,gLsb,oMsb,one['bin']-one['blen']+1),file=sys.stderr)
                if gMsb < oMsb:
                    gMsb=oMsb
                if gLsb > oLsb:
                    gLsb=oLsb
                #print(param,ii,'bout:',one['bout'],'blen:',one['blen'],'bin:',one['bin'])
            pMsb=int(par[7])
            pLsb=int(par[7])- int(par[8]) +1
            #if int(par[8]) != gMsb-gLsb+1:
            #    print('==ERR2=={},取值/输出 长度不一致. 取{}-{}({}),输出{}-{}({})'.format(param,gMsb,gLsb, gMsb-gLsb+1, pMsb,pLsb,par[8],),file=sys.stderr)
            if pLsb != gLsb:  #这个不同,导致resol_corr不同
                resol_corr= 2.0 ** (gLsb - pLsb)
                print('==ERR3=={},取值/输出 Lsb不同. 取{}-{}({}),输出{}-{}({}), res:{}'.format(param,gMsb,gLsb, gMsb-gLsb+1, pMsb,pLsb,par[8],resol_corr,),file=sys.stderr)
        #print(param,'SSM:',par[7],'signBit:',par[8], 'MSB:',par[7],'dataBits:',par[8])
        # 这个是BCD,CHAR类型，分段取值的配置. 与本函数无关.
        #print(param,'Power:',par[35],'Digit:',par[36],'MSB:',par[37],'dataBits:',par[38])
        return resol_corr
    def correct_super(self,param,fra,par):
        '''
        可以对 fra,par 的内容直接修改，因为是引用参数
        -------------
        需要用 fra中的bitIn,对比 par中MSB,bitLen 重新计算target值，
        因为fra中同一组的多个部分,bit会有重叠, 放入arinc429后,按par取值,会有错位
        super参数，通常不需要调置resol. target值经过重新计算后,按需调整resol的值, 通常是2,4,8倍
        '''
        #print('----',param,'----')
        #print(fra)
        resol_corr=1.0  #默认值
        ii=0
        if 1:
            ii+=1
            gMsb=0
            gLsb=31
            fra.sort(key=lambda x:int(x[6])) #按bin排序
            for one in fra:
                #one: [5]:blen, [6]:bin
                oMsb=int(one[6])
                oLsb=int(one[6])-int(one[5])+1
                if(oLsb>=gLsb and oLsb<=gMsb):
                    #按bin排序后，只会出现Lsb重叠
                    print('==ERR1b=={},Lsb重叠: 当前,{}-{}, 加入,{}-{}'.format(param,gMsb,gLsb,oMsb,oLsb),file=sys.stderr)
                    one[5] = int(one[5]) - (gMsb-oLsb+1)
                    print('==ERR1b=={},Lsb  改: 当前,{}-{}, 加入,{}-{}'.format(param,gMsb,gLsb,oMsb,int(one[6])-int(one[5])+1),file=sys.stderr)
                if gMsb < oMsb:
                    gMsb=oMsb
                if gLsb > oLsb:
                    gLsb=oLsb
            pMsb=int(par[7])
            pLsb=int(par[7])- int(par[8]) +1
            if pLsb != gLsb:  #这个不同,导致resol_corr不同
                resol_corr= 2.0 ** (gLsb - pLsb)
                print('==ERR3=={},取值/输出 Lsb不同. 取{}-{}({}),输出{}-{}({}), res:{}'.format(param,gMsb,gLsb, gMsb-gLsb+1, pMsb,pLsb,par[8],resol_corr,),file=sys.stderr)
        return resol_corr

def main():
    global WFNAME
    global PARAM,PARAMLIST
    myQAR=ARINC717('')
    myQAR.dataver(DATAVER)
    if PARAMLIST:
        #-----------列出记录中的所有参数名称--------------
        regularlist,superlist=myQAR.paramlist()
        #---regular parameter
        ii=0
        for vv in regularlist:
            print(vv, end=',\t')
            if ii % 10 ==0:
                print()
            ii+=1
        print()
        print('--------------------------------------------')
        #---superframe parameter
        ii=0
        for vv in superlist:
            print(vv, end=',\t')
            if ii % 10 ==0:
                print()
            ii+=1
        print()

        #-----------参数写入csv文件--------------------
        if WFNAME is not None and len(WFNAME)>0:
            print('Write into file "%s".' % WFNAME)
            with open(WFNAME,'w') as wfp:
                for vv in regularlist:
                    wfp.write(vv+'\n')
                for vv in superlist:
                    wfp.write(vv+'\n')
            #df_pm=pd.concat([pd.DataFrame(regularlist),pd.DataFrame(superlist)])
            #df_pm.to_csv(WFNAME,sep='\t',index=False)
            return
        return

    if TOJSON:
        VecConf=myQAR.to_dict()
        if WFNAME is not None and len(WFNAME)>0:
            print('Write into file "%s".' % WFNAME)
            if WFNAME.endswith('.gz'):
                with gzip.open(WFNAME,'wt',encoding='utf8') as wfp:
                    wfp.write(json.dumps(VecConf, ensure_ascii=False))
            else:
                with open(WFNAME,'wt',encoding='utf8') as wfp:
                    wfp.write(json.dumps(VecConf, ensure_ascii=False))
        else:
            print(json.dumps(VecConf, ensure_ascii=False, indent=3))
        return

    if PARAM is None:
        #-----------打印参数的配置内容-----------------
        for vv in ('ALT_STD','AC_TAIL7'):
            fra=myQAR.getFRA(vv)
            if len(fra)<1:
                print('Empty dataVer.')
                continue
            print('parameter:',vv)
            print('Word/SEC:{0[0]}, synchro len:{0[1]} bit, sync1:{0[2]}, sync2:{0[3]}s, sync3:{0[4]}, sync4:{0[5]}, '.format(fra['1']))
            print('   superframe counter:subframe:{0[6]:<5}, word:{0[7]:<5}, bitOut:{0[8]:<5}, bitLen:{0[9]:<5}, value in 1st frame:{0[10]:<5}, '.format(fra['1']) )
            for vv in fra['2']:
                print('Part:{0[0]:<5}, recordRate:{0[1]:<5}, subframe:{0[2]:<5}, word:{0[3]:<5}, bitOut:{0[4]:<5}, bitLen:{0[5]:<5}, bitIn:{0[6]:<5}, type:{0[7]:<5}, '.format(vv) )
            print()
        print('DataVer:',myQAR.dataVer())
        #print(myQAR.fra)
        #print()
        #print(myQAR.par)
    else:
        #-----------获取一个参数的配置--------------------
        fra,par =myQAR.get_param(PARAM)
        print('DataVer:',myQAR.dataVer())
        print(fra)
        print()
        print(par)

import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'   命令行工具。')
    print(u' 读取 vec 配置, 输出json格式配置。')

    print(sys.argv[0]+' [-h|--help]')
    print('   * (必要参数)')
    print('   -h, --help        print usage.')
    print(' * -v 88888          dataver')
    print(' * -p, --param alt_std        show "ALT_STD" param. 自动全部大写。')
    print('   -l, --paramlist     列出所有的参数名。')
    print('     -w out/out.txt      with "-l",输出所有的参数名到文件')
    print('   -j                  生成json格式的配置。')
    print('     -w out/xxx.json     with "-j",输出json格式的配置到文件')
    print('     -w out/xxx.json.gz  with "-j",输出json格式的配置到文件,gz压缩')
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
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hw:lv:p:j',['help','paramlist','param=',])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    DATAVER=None
    WFNAME=None
    TOJSON=False
    PARAMLIST=False
    PARAM=None
    if len(args)>0:  #命令行剩余参数
        DATAVER=args[0]  #只取第一个
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-v',):
            DATAVER=value
        elif op in('-j',):
            TOJSON=True
        elif op in('-w',):
            WFNAME=value
        elif op in('-l','--paramlist',):
            PARAMLIST=True
        elif op in('-p','--param',):
            PARAM=value
    if DATAVER is None:
        usage()
        exit()

    main()

