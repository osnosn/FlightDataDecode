# Flight Data Decode  

[FOQA (Flight Operations Quality Asurance)](http://en.wikipedia.org/wiki/Flight_operations_quality_assurance)  

这个项目，完全可以使用。但程序并不完善，个别条件/逻辑没有去实现 (注释有写)。   
* 读入的参数编码规则 (配置文件)，没有整理后写入数据库。   
* 不能同时解出多个参数。   

这是我在了解 无线QAR(WQAR) 原始文件过程中，编写的测试程序。   
**目前可以对 ARINC 717 Aligned 格式的文件，解码出所有的记录参数。**   
**目前可以对 ARINC 767 格式的文件，解码出所有的记录参数。**   
这些测试程序都在 [wgl 目录中](https://github.com/osnosn/FlightDataDecode/tree/main/wgl)。它们都有详细的注释。方便你学习/了解。   

**如果你想直接使用，请使用整理后的代码。**   
整理后的最终代码，放在了其他目录。【[ARINC717](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC717)】,【[ARINC767](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC767)】, 注释也被整理过。   

### 更新  
* [wgl 目录](https://github.com/osnosn/FlightDataDecode/tree/main/wgl), 测试程序。详细更新看 [wgl 目录中的 README](https://github.com/osnosn/FlightDataDecode/blob/main/wgl/README.md)   
  **2023-04 最后更新**   
  - 对于 ARINC 573/717 的记录格式   
    - `Get_param_from_arinc717_aligned.py` 可以正确的获取所有记录参数。包括 regular,superframe 参数。  
    - 解码后的参数,可以存为 csv 文件。  
    - 能够处理7种: BCD, BNR LINEAR, BNR SEGMENTS, CHARACTER, DISCRETE, PACKED BITS, UTC 类型的值，并转换为使用值。  
    - 返回参数时，同时给出了对应的秒(从0开始)。  
    - 程序会根据 rate 值，把所有的记录值都解码出来。比如: VRTG 是每秒 8 个记录。  
    - 记录参数中，有 `UTC_HOUR, UTC_MIN, UTC_SEC, DAT_YEAR, DAT_MONTH, DAT_DAY` 这些记录参数。(有的解码库会缺少某些参数)。你可以用这些参数来修正 frame time。  
  - 对于 ARINC 767 的记录格式   
    - `Get_param_from_arinc767_new2023.py`   
    - 能找出每帧的开始和结束。找出帧头,和帧尾的格式。   
    - 通过导出 AGS 的"配置定义"，能解码所有记录参数。   
* [ARINC717 目录](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC717), 从 wgl 整理后的程序。详细更新看 [ARINC717 目录中的 README](https://github.com/osnosn/FlightDataDecode/blob/main/ARINC717/README.md)  
  * 整理完成。2022-02更新   
  * 附加了一个 arinc717 Aligned 的样例。通常,完整的压缩数据包几 MB到几十 MB。   
    样例数据经过处理，**修改/脱敏了部分内容**。包括且不限于: 机号,航班号,日期,经纬度.... 2023-04更新   
  * 预计,今后不再更新了。   
* [ARINC767 目录](https://github.com/osnosn/FlightDataDecode/blob/main/wgl/README.md), 从 wgl 整理后的程序。详细更新看 [ARINC767 目录中的 README](https://github.com/osnosn/FlightDataDecode/blob/main/ARINC767/README.md)  
  * ~~等测试程序完成后，再整理。2022-02~~   
  * 格式不复杂, xml定义文件, 本应该随着原始记录文件,打包在一起的。可惜我拿到的原始记录文件中, xml被摘除了。所以无法通过 xml 定义文件解码。2022-02   
  * xml 定义文件，由 AGS 软件转换并保存。导出它的配置，可以完成解码。   
    解码测试程序完成。整理完成。2023-04   
  * 增加支持 "COMPUTED ON BOARD" 类型的值.    
  * 附加了一个 arinc767 的样例。通常,完整的压缩数据包几十 MB到几百 MB，比较大。    
    样例数据经过处理。**修改/脱敏了部分内容**。包括且不限于: 机号,航班号,日期....   
    样例数据是某机场地面滑行段。 2023-04更新   
  * 预计,今后不再更新了。   

### 其他  
* 认为此项目对您有帮助，请点个星星，或留个言，或发封邮件给我，让我高兴一下.  
  If you think this project is helpful to you, click a Star, or leave a message, or send me an Email to make me happy.


