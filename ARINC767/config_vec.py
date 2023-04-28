#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
配置文件
   author:南方航空,LLGZ@csair.com
"""
import os
selfpath=os.path.dirname(os.path.realpath(__file__)) #本脚本自身所在的目录

vec=os.path.join(selfpath,'vec')
#aircraft=os.path.join(selfpath,'aircraft.air')
aircraft=os.path.join(vec,'aircraft.air')



def main():
    print('vec directory:',vec)
    print('aircraft file:',aircraft)

import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u'   配置文件')
    print(sys.argv[0]+' [-h|--help] ')
    print('   -h, --help     print usage.')
    print('   -d             show config.')
    print(u'\n               author:南方航空,LLGZ@csair.com')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hdf:',['help','file=',])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    FNAME=None
    DUMPDATA=False
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-f','--file'):
            FNAME=value
        elif op in('-d',):
            DUMPDATA=True
    if len(args)>0:  #命令行剩余参数
        FNAME=args[0]  #只取第一个

    if DUMPDATA:
        main()
    else:
        print('Do nothing.')

