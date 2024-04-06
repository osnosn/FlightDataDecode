#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
 把输入的整数，分别以 int,float32,float64 存储，再转为字节。
  用于在二进制(bin)文件中查找对应的值。
    author: osnosn@126.com OR LLGZ@csair.com
"""
import struct
#from datetime import datetime

def main():
    global VER  ,DUMPDATA

    ver=int(VER  )

    buf2=struct.pack('<l',ver) #int(4)
    print(ver)
    #print(buf2)
    print('int(4)   Hex:',buf2.hex(' '))
    #print(struct.unpack('<l',buf2)[0])
    print()

    ver=float(VER  )

    buf2=struct.pack('<f',ver)  #float(4)
    print(ver)
    #print(buf2)
    print('float(4) Hex:',buf2.hex(' '))
    #print(struct.unpack('<f',buf2)[0])
    print()

    buf2=struct.pack('<d',ver)  #float(8)
    print(ver)
    #print(buf2)
    print('float(8) Hex:',buf2.hex(' '))
    #print(struct.unpack('<d',buf2)[0])
    print()





import os,sys,getopt
def usage():
    print(u'Usage:')
    print(u' 把输入的整数，分别以 int,float32,float64 存储，再转为字节。')
    print(u' 用于在二进制(bin)文件中查找对应的值。')
    print(u' 命令行工具。')
    print(sys.argv[0]+' [-h|--help] [-v|--ver]  ')
    print('   -h, --help        print usage.')
    print('   -v, --ver=10234   整数')
    print(u'\n               author: osnosn@126.com')
    print()
    return
if __name__=='__main__':
    if(len(sys.argv)<2):
        usage()
        exit()
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:],'hv:d',['help','ver=','pd'])
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(2)
    VER  =None
    DUMPDATA=False
    for op,value in opts:
        if op in ('-h','--help'):
            usage()
            exit()
        elif op in('-v','--ver'):
            VER  =value
        elif op in('-d',):
            DUMPDATA=True
    if VER is None:
        usage()
        exit()

    main()

