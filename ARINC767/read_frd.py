#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
读解码库， 787xx 的 ARINC 767 记录格式，则读 xxx.frd 文件,
   ARINC-647A-1 的xml配置文件找不到。所以可能无法解码。
      author:南方航空,LLGZ@csair.com
"""
import os
import zipfile
import gzip
from io import StringIO
import config_vec as conf

def main():
    global FNAME,DUMPDATA
    global TOCSV
    global PARAMLIST
    global PARAM
    frd_conf=read_parameter_file(FNAME)
    if frd_conf is None:
        return

    #print(frd_conf)
    #print(frd_conf.keys())

    if PARAMLIST:
        #----------显示所有参数名-------------
        ii=0
        for vv in frd_conf['4']:
            print(vv[1], end=',\t')
            if ii % 9 ==0:
                print()
            ii+=1
        #----写CSV文件--------
        if len(TOCSV)>4:
            print('Write to CSV file:',TOCSV)
            if TOCSV.endswith('.gz'):
                fp=gzip.open(TOCSV,'wt',encoding='utf8')
            else:
                fp=open(TOCSV,'w',encoding='utf8')
            ii=0
            for row in frd_conf['2']:
                fp.write(str(ii)+'\t'+row[0]+'\n')
                ii+=1
            ii=0
            for row in frd_conf['4']:
                fp.write(str(ii)+'\t'+row[0]+'\n')
                ii+=1
            fp.close()
        return

    if PARAM is not None and len(PARAM)>0:  #显示单个参数名
        #----------显示单个参数的配置内容-------------
        print_frd(frd_conf, '1', [ '<13', '<22', '<31', '<12', '<26', '<9'] )  #这个也显示一下

        #param=PARAM.upper()
        buf_map=list(map(lambda x: PARAM==x[1] ,frd_conf['4'])) #在['4']中查找匹配, x[1]:Parameter Name
        idx4=buf_map.count(True)
        if idx4<1 or idx4>1:
            print('(4)Parameter "%s" not found OR error.'%param)
            return
        idx4=buf_map.index(True) #获取索引
        pm_long_name=frd_conf['4'][idx4][0]

        buf_map=list(map(lambda x: pm_long_name == x[2] ,frd_conf['3'])) #在['3']中,查找匹配, x[2]:Parameter long name
        idx3=buf_map.count(True)
        if idx3<1 or idx3>1:
            print('(4)Parameter "%s" not found OR error.'%param)
            return
        idx3=buf_map.index(True) #获取索引
        param_frame_id=frd_conf['3'][idx3][0]
        param_order=frd_conf['3'][idx3][1]

        buf_map=list(map(lambda x: param_frame_id == x[0] ,frd_conf['2'])) #在['3']中,查找匹配, x[2]:Parameter long name
        idx2=buf_map.index(True) #获取索引

        width=[ '^8', '^18', '^22', '<24', '<30', '<15']
        print('---- 2 ----------')
        for ii in (0,idx2):
            print('{:>4}'.format(ii) ,end='|')
            jj=0
            for vv in frd_conf['2'][ii]:
                fmt='{:%s}' % width[jj]
                jj+=1
                print(fmt.format(vv) ,end='|')
            print()
        print()
        width=['9', '15', '22', '18']
        print('---- 3 ----------')
        for ii in (0,idx3):
            print('{:>4}'.format(ii) ,end='|')
            jj=0
            for vv in frd_conf['3'][ii]:
                fmt='{:%s}' % width[jj]
                jj+=1
                print(fmt.format(vv) ,end='|')
            print()
        print()
        width=['23', '18']
        print('---- 4 ----------')
        for ii in (0,idx4):
            print('{:>4}'.format(ii) ,end='|')
            jj=0
            for vv in frd_conf['4'][ii]:
                fmt='{:%s}' % width[jj]
                jj+=1
                print(fmt.format(vv) ,end='|')
            print()
        print()

        print()
        return

    print_frd(frd_conf, '1', [ '<13', '<22', '<31', '<12', '<26', '<9'] )
    print_frd(frd_conf, '2', [ '^8', '^18', '^22', '<24', '<30', '<15'] )
    print_frd(frd_conf, '3', ['9', '15', '22', '18'] )
    print_frd(frd_conf, '4', ['23', '18'] )

    #-----打印frame id 的参数个数
    frame_id_count={}
    for vv in frd_conf['3']:
        if vv[0] not in frame_id_count:
            frame_id_count[vv[0]]=1
        else:
            frame_id_count[vv[0]]+=1
    print('----------------')
    print('{:>7}, {:>9}'.format('FrameID', 'param num') )
    for vv in frame_id_count:
        if vv.startswith('Frame')>0: continue
        print('{:>7}, {:>9}'.format(vv,frame_id_count[vv]) )
    print()

    if len(TOCSV)>4:
        print('==>ERR,  There has 4 tables. Can not save to 1 CSV.')

def print_frd(frd_conf, frdkey,colwidth):
    if frdkey not in frd_conf:
        print('ERR, %s not in list' % frdkey)
        return
    frd_len=len(frd_conf[frdkey])-1
    print('----',frdkey,'------------- recorder num:',frd_len,'-----')

    ommit_middle=False
    ii=-1
    for vv in frd_conf[frdkey]:
        ii+=1
        if ii>5 and ii< frd_len-5:
            ommit_middle=True
            continue
        if ii>= frd_len-5 and ommit_middle:
            ommit_middle=False
            print('...')
        print('{:>4}'.format(ii),end='|')
        jj=0
        for ww in vv:
            width='{:%s}' % colwidth[jj]
            jj+=1
            print(width.format(ww.strip()), end='|')
        print()

def read_parameter_file(dataver):
    '''
    frd_conf={
         '1': [ 
            [x,x,,....],   <-- items number
            [x,x,,....],
             ...
            ]
         '2': [
            [x,x,,....],
            [x,x,,....],
             ...
            ]
         '3': [
            [x,x,,....],
            [x,x,,....],
             ...
            ]
         '4': [
            [x,x,,....],
            [x,x,,....],
             ...
            ]
         '1_len': xx,
         '2_len': xx,
         '3_len': xx,
         '4_len': xx,

    }
    '''
    if isinstance(dataver,(str,float)):
        dataver=int(dataver)
    dataver='%06d' % dataver  #6位字符串

    filename_zip=dataver+'.frd'     #.vec压缩包内的文件名
    zip_fname=os.path.join(conf.vec,dataver+'.vec')  #.vec文件名

    if os.path.isfile(zip_fname)==False:
        print('ERR,ZipFileNotFound',zip_fname,flush=True)
        raise(Exception('ERR,ZipFileNotFound,%s'%(zip_fname)))

    #if not zipfile.Path(zip_fname,filename_zip).exists():  #判断vec中是否有.frd文件
    #    print('ERR,dataver %s not support.' % (dataver,) )
    #    print('Use "read_fra.py instead.')
    #    return None

    try:
        fzip=zipfile.ZipFile(zip_fname,'r') #打开zip文件
    except zipfile.BadZipFile as e:
        print('ERR,FailOpenZipFile',e,zip_fname,flush=True)
        raise(Exception('ERR,FailOpenZipFile,%s'%(zip_fname)))

    if filename_zip not in fzip.namelist():  #判断vec中是否有.frd文件
        fzip.close()
        print('ERR,dataver %s not support.' % (dataver,) )
        print('Use "read_fra.py instead.')
        return None

    frd_conf={}
    with StringIO(fzip.read(filename_zip).decode('utf16')) as fp:
        for line in fp.readlines():
            line_tr=line.strip('\r\n //')
            tmp1=line_tr.split('|',1)
            tmp2=tmp1[1].split('\t')
            if tmp1[0] in frd_conf:
                if frd_conf[ tmp1[0]+'_len' ] != len(tmp2):
                    print('ERR,data(%s) length require %d, but %d.' % (tmp1[0], frd_conf[ tmp1[0]+'_len' ], len(tmp2)) )
                    #raise(Exception('ERR,DataLengthNotSame,data(%s) require %d but %d.'% (tmp1[0], frd_conf[ tmp1[0]+'_len' ], len(tmp2)) ))
                frd_conf[ tmp1[0] ].append( tmp2 )
            else:
                frd_conf[ tmp1[0] ]=[ tmp2, ]
                frd_conf[ tmp1[0]+'_len' ]=len(tmp2)

    fzip.close()
    return frd_conf       #返回list


import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'   命令行工具。')
    print(u' 读解码库，787xx 的frad库,参数配置文件 vec 中 xx.frd 文件。比如 078XXX.frd')
    print(u'      ARINC-647A-1 的xml配置文件找不到。所以可能无法解码。')
    print(sys.argv[0]+' [-h|--help]')
    print('   -h, --help         print usage.')
    print('   -v, --ver=78727      dataver 中的参数配置表')
    print('   --csv xxx.csv        save to "xxx.csv" file.')
    print('   --csv xxx.csv.gz     save to "xxx.csv.gz" file.')
    print('   --paramlist          list all param name.')
    print('   -p,--param alt_std   show "alt_std" param.')
    print(u'\n               author:南方航空,LLGZ@csair.com')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hv:p:f:',['help','ver=','csv=','paramlist','param='])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    DUMPDATA=False
    TOCSV=''
    PARAMLIST=False
    PARAM=None
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-v','--ver'):
            FNAME=value
        elif op in('-d',):
            DUMPDATA=True
        elif op in('--csv',):
            TOCSV=value
        elif op in('--paramlist',):
            PARAMLIST=True
        elif op in('--param','-p',):
            PARAM=value
    if len(args)>0:  #命令行剩余参数
        FNAME=args[0]  #只取第一个
    if FNAME is None:
        usage()
        exit()

    main()

