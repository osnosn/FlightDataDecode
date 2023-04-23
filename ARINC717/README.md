# ARINC717 目录   

### 更新   
* 整理完成。 2022-02   
* 使用的例程是 `TEST_myqar.py`。   
* 预计,今后不再更新了。2022-02   
* 附加了一个arinc717的样例。样例数据经过处理，**修改/脱敏了部分内容**。包括且不限于: 机号,航班号,日期,经纬度.... 2023-04   



### 说明   
**此目录的程序，是用来解码 ARINC 717 Aligned 格式的文件。**   
ARINC 717 Aligned 文件,是从 ARINC 717 文件整理而来。主要做了两件事,   
* 把 12 bits word 找出来, 存为 16 bits(2 bytes)。补在高位的 4 bits 可以根据需要设置些状态。比如,表示当前帧是补的。   
* 根据同步字, 如果源文件有缺帧/漏帧, 则用空帧补齐。为了在解码时,能够直接计算参数位置, 而无需扫描文件。  


所有python3程序用到的库   
  * `import csv`  
  * `from io import StringIO`  
  * `import gzip`  
  * `import os,sys,getopt`  
  * `import zipfile`  


编写时使用的是 python-3.9.2 版本。import包都是 python-3.9.2内置或自带的包。   
在 python-3.6.8 中测试OK。   
理论上,在所有的 python-3.x 都能运行。   

这些程序需要 vec 目录中的配置文件。(机型编码规范, 或者参数编码规则)    
配置文件的来源，请看 [vec目录中的README](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC717/vec).    

此目录中的 py 脚本，都可以作为命令行程序运行。   
直接运行，会给出帮助。   
```
$ ./TEST_myqar.py  -h
Usage:
   命令行工具。
 读取 wgl中 raw.dat,根据参数编码规则,解码一个参数。
./TEST_myqar.py [-h|--help]
   * (必要参数)
   -h, --help                 print usage.
 * -f, --file xxx.wgl.zip     "....wgl.zip" filename
 * -p, --param alt_std        show "ALT_STD" param. 自动全部大写。
   --paramlist                list all param name.
   -w xxx.csv            参数写入文件"xxx.csv"
   -w xxx.csv.gz         参数写入文件"xxx.csv.gz"
```
* 这几个文件，是用于修改原始数据的程序。  
  * Get_param_from_arinc717_aligned_modify.py   
  * modify_tag.py   
  * modify_TEST_myqar.py   


### 其他  
* 认为此项目对您有帮助，请点个星星，或留个言，或发封邮件给我，让我高兴一下.  
  If you think this project is helpful to you, click a Star, or leave a message, or send me an Email to make me happy.


