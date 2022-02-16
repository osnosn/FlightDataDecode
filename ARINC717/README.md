# ARINC717 目录   

### 更新   
* 整理完成。 2022-02. 使用的例程是 `myqar_test.py`。 



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


编写时使用的是 python3.9 版本。   

这些程序需要 vec 目录中的配置文件。(机型编码规范, 或者参数编码规则)    
配置文件的来源，请看 [vec目录中的README](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC717/vec).    


