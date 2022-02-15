#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
读解码库，参数配置文件 vec 中 xx.fra 文件。比如 010XXX.fra
仅支持 ARINC 573 PCM 格式
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
    FRA=read_parameter_file(FNAME)
    if FRA is None:
        return

    #print(FRA)
    #print(FRA.keys())

    if PARAMLIST:
        #----------显示所有参数名-------------
        #print(FRA['2'].iloc[:,0].tolist())
        #---regular parameter
        print('------------------------------------------------')
        ii=0
        for vv in FRA['2']:
            print(vv[0], end=',\t')
            if ii % 10 ==0:
                print()
            ii+=1
        print()
        #---superframe parameter
        print('------------------------------------------------')
        ii=0
        for vv in FRA['4']:
            print(vv[0], end=',\t')
            if ii % 10 ==0:
                print()
            ii+=1
        print()
        #----写CSV文件--------
        if len(TOCSV)>4:
            print('Write to CSV file:',TOCSV)
            if TOCSV.endswith('.gz'):
                fp=gzip.open(TOCSV,'wt',encoding='utf8')
            else:
                fp=open(TOCSV,'w',encoding='utf8')
            ii=0
            for row in FRA['2']:
                fp.write(str(ii)+'\t'+row[0]+'\n')
                ii+=1
            ii=0
            for row in FRA['4']:
                fp.write(str(ii)+'\t'+row[0]+'\n')
                ii+=1
            fp.close()
        return

    if PARAM is not None and len(PARAM)>0:  #显示单个参数名
        #----------显示单个参数的配置内容-------------
        param=PARAM.upper()
        #---regular parameter
        idx=0
        for row in FRA['2']:
            if row[0] == param: break
            idx +=1
        if idx < len(FRA['2']):
            for ii in range(FRA['2_items']):
                print(ii,FRA['2'][idx][ii], FRA['2'][0][ii], sep=',\t')
        else:
            print('Parameter %s not found in Regular parameter.'%param)
        print()
        #---superframe parameter
        idx=0
        for row in FRA['4']:
            if row[0] == param: break
            idx +=1
        if idx < len(FRA['4']):
            for ii in range(FRA['4_items']):
                print(ii,FRA['4'][idx][ii], FRA['4'][0][ii], sep=',\t')
        else:
            print('Parameter %s not found in Superframe parameter.'%param)
        print()

        return

    print_fra(FRA, '1')
    print_fra(FRA, '2')
    if len(FRA['3'])>1:
        print_fra(FRA, '3')
    else:
        print('No Superframe.')

    if len(FRA['4'])>1:
        print_fra(FRA, '4')
    else:
        print('No Superframe Parameter.')
    print()

    if len(TOCSV)>4:
        print('==>ERR,  There has 4 tables. Can not save to 1 CSV.')

def print_fra(FRA, frakey ):
    if frakey not in FRA:
        print('ERR, %s not in list' % frakey)
        return
    fra_len=len(FRA[frakey])-1
    print('----',frakey,'------------- recorder num:',fra_len,'-----')
    if fra_len>6:
        show_len=6
    else:
        show_len=fra_len
    for ii in range(FRA[frakey+'_items']):
        print(ii,end=',')
        for jj in range(1,show_len+1):
            print('\t',FRA[frakey][jj][ii], end=',')
        print('\t',FRA[frakey][0][ii])

def read_parameter_file(dataver):
    '''
    FRA={
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
         '1_items': xx,
         '2_items': xx,
         '3_items': xx,
         '4_items': xx,

    }
    '''
    if isinstance(dataver,(str,float)):
        dataver=int(dataver)
    if str(dataver).startswith('787'):
        print('ERR,dataver %s not support.' % (dataver,) )
        print('Use "read_frd.py instead.')
        return None
    dataver='%06d' % dataver  #6位字符串

    filename_zip=dataver+'.fra'     #.vec压缩包内的文件名
    zip_fname=os.path.join(conf.vec,dataver+'.vec')  #.vec文件名

    if os.path.isfile(zip_fname)==False:
        print('ERR,ZipFileNotFound',zip_fname,flush=True)
        raise(Exception('ERR,ZipFileNotFound,%s'%(zip_fname)))

    try:
        fzip=zipfile.ZipFile(zip_fname,'r') #打开zip文件
    except zipfile.BadZipFile as e:
        print('ERR,FailOpenZipFile',e,zip_fname,flush=True)
        raise(Exception('ERR,FailOpenZipFile,%s'%(zip_fname)))
    
    FRA={}
    with StringIO(fzip.read(filename_zip).decode('utf16')) as fp:
        for line in fp.readlines():
            line_tr=line.strip('\r\n //')
            tmp1=line_tr.split('|',1)
            if line.startswith('//') and tmp1[0] == '3':     # "3|..." 的标题比较特殊，末尾少了一个tab
                tmp1[1] += '\t'
            if line.startswith('//') and tmp1[0] == '7':     # "7|..." 的标题比较特殊，起始多了一个tab
                tmp1[1]=tmp1[0].lstrip()
            tmp2=tmp1[1].split('\t')
            if tmp1[0] in FRA:
                if FRA[ tmp1[0]+'_items' ] != len(tmp2):
                    print('ERR,data(%s) length require %d, but %d.' % (tmp1[0], FRA[ tmp1[0]+'_items' ], len(tmp2)) )
                    #raise(Exception('ERR,DataLengthNotSame,data(%s) require %d but %d.'% (tmp1[0], FRA[ tmp1[0]+'_items' ], len(tmp2)) ))
                FRA[ tmp1[0] ].append( tmp2 )
            else:
                FRA[ tmp1[0] ]=[ tmp2, ]
                FRA[ tmp1[0]+'_items' ]=len(tmp2)
    fzip.close()
    return FRA       #返回list



import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'   命令行工具。')
    print(u' 读解码库，参数配置文件 vec 中 xx.fra 文件。比如 010XXX.fra')
    print(sys.argv[0]+' [-h|--help]')
    print('   -h, --help        print usage.')
    print('   -v, --ver=10XXX      dataver 中的参数配置表')
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
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hvp:f:',['help','ver=','csv=','paramlist','param='])
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

