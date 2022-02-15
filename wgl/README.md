# wgl 目录  

### 更新  
* 2022-02 第一次更新  
  - `get_param_from_wgl.py`最终可以提取出单个的记录参数(原始值,还没转换为使用值)。  
* 2022-02 再次更新  
  - `get_param_from_wgl.py` 可以获取部分 BNR, BCD, CHARACTER 类型的值，并转换为使用值。  
  - 问题: UTC 类型的似乎不行。参数的rate没有处理。  
* 2022-02 再次更新  
  - 对于 ARINC 573/717 的记录格式   
    - `Get_param_from_wgl.py` 可以正确的获取所有记录参数(除了超级帧参数)。能够处理 BNR,BCD,CHARACTER 类型的值，并转换为使用值。  
    - 解码后的参数,可以存为 csv 文件。  
    - 返回参数时，同时给出了对应的秒(从0开始)。  
    - 程序会根据 rate 值，把所有的记录值都解码出来。比如: VRTG 是每秒 8 个记录。  
    - 记录参数中，有 `UTC_HOUR, UTC_MIN, UTC_SEC, DAT_YEAR, DAT_MONTH, DAT_DAY` 这些记录参数。(有的解码库会缺少某个参数)。你可以用这些参数来修正 frame time。  
    - 问题: 没有处理超级帧。如果参数是记录在超级帧中，解码会失败，或者解码出的内容是错误的。  
  - 对于 ARINC 767 的记录格式   
    - 只能找出每帧的开始和结束。找出帧头,和帧尾的格式。   
* 2022-02 再次更新  
  - 对于 ARINC 573/717 的记录格式: 增加支持 DISCRETE, PACKED BITS, UTC, 类型的值。共支持7种: BCD, BNR LINEAR, BNR SEGMENTS, CHARACTER, DISCRETE, PACKED BITS, UTC.    
* 2022-02 再次更新  
  - 对于 ARINC 573/717 的记录格式: 可以解码所有的参数，包括 regular, superframe 参数。  



### 说明
这个目录中的py程序，可以使用。但没有达到完全可用状态。  
是我在了解 无线QAR(WQAR) 原始 raw.dat 文件过程中，编写的程序。   
**目前可以解码出所有的记录参数。**   
有兴趣的，可以参考一下。  

整理后的代码，将会放在其他目录。【[ARINC717](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC717)】,【[ARINC767](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC767)】   

-----------
此目录中的 py 脚本，都可以作为命令行程序运行。   
直接运行，会给出帮助。   
```
$ ./Get_param_from_wgl.py
Usage:
   命令行工具。
 读取 wgl中 raw.dat,根据参数编码规则,解码一个参数。
./Get_param_from_wgl.py [-h|--help]
   * (必要参数)
   -h, --help                 print usage.
 * -f, --file xxx.wgl.zip     "....wgl.zip" filename
 * -p, --param alt_std        show "ALT_STD" param. 自动全部大写。
   --paramlist                list all param name.
   -w xxx.csv            参数写入文件"xxx.csv"
   -w xxx.csv.gz         参数写入文件"xxx.csv.gz"
```

wgl 目录中有两个空文件，只是给出个例子，看看压缩包内,文件名的命名规律。  
  * `B-1234_20210121132255.wgl.zip` ,这是 ARINC 717 aligned   
  * `B-123420220102114550M.zip` ,这是 ARINC 767 格式  

这两个文件的内容是一样的。  
  * `Get_param_from_arinc717_aligned.py`   
  * `Get_param_from_wgl.py`   

所有python3程序用到的库   
  * `import os,sys,getopt`  
  * `from datetime import datetime`  
  * `import zipfile`  
  * `from io import BytesIO`  
  * `from io import StringIO`  
  * `import pandas as pd`   解码，未用到，读air配置文件,依赖了。读其他配置文件, 用到了。  
  * `import psutil`   解码，未用到  
  * `import struct`   解码，未用到  


编写时使用的是 python3.9 版本。   

这些程序需要 vec 目录中的配置文件。(机型编码规范, 或者参数编码规则)    
配置文件的来源，请看 [vec目录中的README](https://github.com/osnosn/FlightDataDecode/tree/main/wgl/vec).    


