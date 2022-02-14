# Flight Data Decode  

[FOQA (Flight Operations Quality Asurance)](http://en.wikipedia.org/wiki/Flight_operations_quality_assurance)  

这个项目，可以使用。但没有达到完全可用状态。  
是我在了解 无线QAR(WQAR) 原始 raw.dat 文件过程中，编写的测试程序。**目前可以解码出所有的记录参数。**   
这些程序都在 [wgl 目录中](https://github.com/osnosn/FlightDataDecode/tree/main/wgl)。它们都有详细的注释。方便你学习/了解。   

整理后的代码，将会放在其他目录。【[ARINC717](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC717)】,【[ARINC767](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC767)】, 可能会删除很多注释。   

### 更新  
* [wgl 目录](https://github.com/osnosn/FlightDataDecode/tree/main/wgl), 测试程序。详细更新看 [wgl 目录中的 README](https://github.com/osnosn/FlightDataDecode/blob/main/wgl/README.md)   
  2022-02 最后更新   
  - 对于 ARINC 573/717 的记录格式   
    - `Get_param_from_wgl.py` 可以正确的获取所有记录参数。包括regular,superframe参数。  
    - 解码后的参数,可以存为 csv 文件。  
    - 能够处理7种: BCD, BNR LINEAR, BNR SEGMENTS, CHARACTER, DISCRETE, PACKED BITS, UTC 类型的值，并转换为使用值。  
    - 返回参数时，同时给出了对应的秒(从0开始)。  
    - 程序会根据 rate 值，把所有的记录值都解码出来。比如: VRTG 是每秒 8 个记录。  
    - 记录参数中，有 `UTC_HOUR, UTC_MIN, UTC_SEC, DAT_YEAR, DAT_MONTH, DAT_DAY` 这些记录参数。(有的解码库会缺少某些参数)。你可以用这些参数来修正 frame time。  
  - 对于 ARINC 767 的记录格式   
    - 只能找出每帧的开始和结束。找出帧头,和帧尾的格式。   
* [ARINC717 目录](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC717), 从 wgl 整理后的程序。详细更新看 [ARINC717 目录中的 README](https://github.com/osnosn/FlightDataDecode/blob/main/ARINC717/README.md)  
  * 还没做  
* [ARINC767 目录](https://github.com/osnosn/FlightDataDecode/blob/main/wgl/README.md), 从 wgl 整理后的程序。详细更新看 [ARINC767 目录中的 README](https://github.com/osnosn/FlightDataDecode/blob/main/ARINC767/README.md)  
  * 等测试程序完成后，再整理。  


