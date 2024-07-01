# ARINC767 目录  

## 更新  
  * ~~等 wgl 目录中的测试程序完成后，再做。2022-02~~   
  * 格式不复杂, ~~xml定义文件, 本应该随着原始记录文件,打包在一起的。可惜我拿到的原始记录文件中, xml被摘除了。所以无法通过 xml 定义文件解码。2022-02~~   
  * xml 定义文件，由 AGS 软件转换并保存。导出它的配置，可以完成解码。   
    解码测试程序完成。整理完成。2023-04   
  * 使用的例程是 `TEST_myqar.py`。2023-04   
  * 增加支持 "COMPUTED ON BOARD" 类型的值.    
  * 附加了一个 arinc767 的样例。通常,完整的压缩数据包几十 MB到几百 MB，比较大。    
    样例数据经过处理。**修改/脱敏了部分内容**。包括且不限于: 机号,航班号,日期....   
    样例数据是某机场地面滑行段。 2023-04更新   
  * 预计,今后不再更新了。   


## 说明  
**此目录的程序，是用来解码 ARINC 767 格式的文件。**   
  * `647a-1.zip` XML 样例, 来源 https://www.aviation-ia.com/support-files/647a-1
  * 能找出每帧的开始和结束。找出帧头,和帧尾的格式。   
  * 通过导出 AGS 的"配置定义"，能解码所有记录参数。   

所有python3程序用到的库   
  * import csv   
  * from io import StringIO   
  * import gzip   
  * import os, sys, getopt   
  * import struct   
  * import zipfile   
  * 其他: psutil,   


编写时使用的是 python-3.9.2 版本。import包都是 python-3.9.2内置或自带的包。   
在 python-3.6.8 中测试OK。   
理论上,在所有的 python-3.x 都能运行。   

程序需要 vec 目录中的配置文件。(机型编码规范, 或者参数编码规则)    
配置文件的来源，请看 [vec目录中的README](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC767/vec).    
  * 目录中的 `aircraft.air` 和 `078711.vec` 是经过脱敏处理后的样例。2023-04   

此目录中的 py 脚本，都可以作为命令行程序运行。   
直接运行，会给出帮助。   
```
$ ./TEST_myqar.py  -h
Usage:
   命令行工具。
 读取,来源于PC卡的原始数据文件。尝试解码一个参数。
./TEST_myqar.py [-h|--help]
   -h, --help                print usage.
   -f, --file="....wgl.zip"     filename
   -p, --param ALT_STD       show "ALT_STD" param. 大小写敏感。
   --paramlist               list all param name.
   -w xxx.csv                参数写入文件"xxx.csv"
   -w xxx.csv.gz             参数写入文件"xxx.csv.gz"
```
* 这几个文件，是用于脱敏/修改原始数据的程序。2023-04   
  * Get_param_from_arinc767_modify.py   
  * modify_TEST_myqar.py   


## 其他  
* 认为此项目对您有帮助，请点个星星，或留个言，或发封邮件给我，让我高兴一下.  
  If you think this project is helpful to you, click a Star, or leave a message, or send me an Email to make me happy.


