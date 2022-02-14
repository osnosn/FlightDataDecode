# Flight Data Decode  

[FOQA (Flight Operations Quality Asurance)](http://en.wikipedia.org/wiki/Flight_operations_quality_assurance)  

这个项目，可以用。但没有达到完全可用状态。  
是我在了解 无线QAR(WQAR) 原始 raw.dat 文件过程中，编写的程序。   
**目前可以解码出所有的记录参数。**   
有兴趣的，可以参考一下，继续完善。  

这些程序都在 [wgl 目录中](https://github.com/osnosn/FlightDataDecode/tree/main/wgl)。  

## 更新  
* 2022-02 第一次更新  
  - `get_param_from_wgl.py`最终可以提取出单个的记录参数(原始值,还没转换为使用值)。  
* 2022-02 再次更新  
  - `get_param_from_wgl.py` 可以获取部分 BNR, BCD, CHARACTER 类型的值，并转换为使用值。  
  - 问题: UTC 类型的似乎不行。参数的rate没有处理。  
* 2022-02 再次更新  
  - 对于 ARINC 573/717 的记录格式   
    - `Get_param_from_wgl.py` 可以正确的获取所有记录参数(除了超级帧参数)。能够处理 BNR,BCD,CHARACTER 类型的值，并转换为使用值。  
    - 返回参数时，同时给出了对应的秒(从0开始)。  
    - 程序会根据 rate 值，把所有的记录值都解码出来。比如: VRTG 是每秒 8 个记录。  
    - 记录参数中，有 `UTC_HOUR, UTC_MIN, UTC_SEC, DAT_YEAR, DAT_MONTH, DAT_DAY` 这些记录参数。(有的解码库会缺少某个参数)。你可以用这些参数来修正 frame time。  
    - 问题: 没有处理超级帧。如果参数是记录在超级帧中，解码会失败，或者解码出的内容是错误的。  
  - 对于 ARINC 767 的记录格式   
    - 只能找出每帧的开始和结束。找出帧头,和帧尾的格式。   
* 2022-02 再次更新  
  - 对于 ARINC 573/717 的记录格式: 增加支持 DISCRETE, PACKED BITS, UTC, 类型的值。共支持7种: BCD, BNR LINEAR, BNR SEGMENTS, CHARACTER, DISCRETE, PACKED BITS, UTC.    
* 2022-02 再次更新  
  - 对于 ARINC 573/717 的记录格式: 可以解码所有的参数，包括regular,superframe参数。


