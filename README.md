# Flight Data Decode  

[FOQA (Flight Operations Quality Asurance)](http://en.wikipedia.org/wiki/Flight_operations_quality_assurance)  

这个项目，完全可以使用。但程序并不完善，个别条件/逻辑没有去实现 (注释有写)。   
* 读入的参数编码规则 (配置文件)，没有整理后写入数据库。   

这是我在了解 无线QAR(WQAR) 原始文件过程中，编写的测试程序。   
**目前可以对 ARINC 717 Aligned 格式的文件，解码出所有的记录参数。**   
**目前可以对 ARINC 767 格式的文件，解码出所有的记录参数。**   
这些测试程序都在 [wgl 目录中](https://github.com/osnosn/FlightDataDecode/tree/main/wgl)。它们都有详细的注释。方便你学习/了解。   

**如果你想直接使用，请使用整理后的代码。**   
整理后的最终代码，放在了其他目录。【[ARINC717](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC717)】,【[ARINC767](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC767)】, 注释也被整理过。   

## 更新  
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
  * 一次解码所有参数，写入自定义格式文件。从自定义格式文件，读入pd.DataFrame中。(2024-05)   
  * 预计,今后不再更新了。   
* [ARINC767 目录](https://github.com/osnosn/FlightDataDecode/tree/main/ARINC767), 从 wgl 整理后的程序。详细更新看 [ARINC767 目录中的 README](https://github.com/osnosn/FlightDataDecode/blob/main/ARINC767/README.md)  
  * ~~等测试程序完成后，再整理。2022-02~~   
  * 格式不复杂, xml定义文件, 本应该随着原始记录文件,打包在一起的。可惜我拿到的原始记录文件中, xml被摘除了。所以无法通过 xml 定义文件解码。2022-02   
  * xml 定义文件，由 AGS 软件转换并保存。导出它的配置，可以完成解码。   
    解码测试程序完成。整理完成。2023-04   
  * 增加支持 "COMPUTED ON BOARD" 类型的值.    
  * 附加了一个 arinc767 的样例。通常,完整的压缩数据包几十 MB到几百 MB，比较大。    
    样例数据经过处理。**修改/脱敏了部分内容**。包括且不限于: 机号,航班号,日期....   
    样例数据是某机场地面滑行段。 2023-04更新   
  * 预计,今后不再更新了。   

## 数据处理的流程   
本项目, 没打算做成一个产品, 只是一个指引。   
顺便, 我自己也要用一下。   
所以, 本项目是可以用的。大部分的参数,解码都是正确的。   
希望, 让有兴趣的公司或个人, 有信心自己做解码。因为解码并不是那么的难。   

### ARINC717   
1. 获取未解码的原始数据。   
2. 判断格式，Bitstream OR Aligned. 用wgl目录中的程序。    
   `dump_rawdat_bitstream.py`,`dump_rawdat_aligned.py`分别扫描原始数据。   
   如果是bitstream则下一步，如果是aligned则跳过下一步。   
3. 用`bitstream2aligned.py`, 把bitstream格式转换为aligned格式, 并把数据帧对齐。(补帧未实现)   
   如果发现有帧损坏, 则用空白数据补齐这个损坏的帧。如果有缺帧, 则补空白帧。   
4. 两种办法继续处理。   
   1. 用`read_prm717.py`把PRM配置,改写为json配置文件。   
      或用`VEC717_to_json.py`把VEC配置, 改写为json配置文件。(202406)   
      跳去另一个项目[FlightDataDecode2](https://github.com/osnosn/FlightDataDecode2/), 用那边的程序继续处理。   
   1. 用ARINC717目录中的程序。直接使用VEC的配置。   
      - `TEST_myqar.py`一次解一个参数。   
      - `ALL_myqar.py`解所有参数,写CSV。   
      - `ALL_myqar2datafile_bin.py`解所有参数,写全参文件。   
5. 用程序(本项目中没写) 读取全参文件, 修改全参文件.   
   这一步, 可以通过修改`ALL_read_datafile.py`程序,达到目的。   
   比如: 修改Meta信息; 做飞行阶段的划分; 增加简单的计算参数; 判断简单的超限,生成超限事件; ...    
   以新增参数的方式, 加入到全参文件中。   
   这一步, 还需要对部分跳变的,异常的参数值做修正处理。   
5. 用`ALL_read_datafile.py`读取全参文件, 做复杂的分析处理.   
   这一步, 用python3, 是因为这个语言比较有优势。   

### ARINC767   
1. 获取未解码的原始数据。   
2. 用ARINC767目录中的程序。直接使用VEC的配置。   
   `TEST_myqar.py`一次解一个参数。   
3. 用程序(本项目中没写) 读取全参文件, 修改全参文件.   
   因为前面没做全参的解码。只能通过修改`TEST_myqar.py`达到目的。   
   比如: 修改Meta信息; 做飞行阶段的划分; 增加简单的计算参数; 判断简单的超限,生成超限事件; ...    
   以新增参数的方式, 加入到全参文件中。   
   这一步, 还需要对部分跳变的,异常的参数值做修正处理。   
   通常ARINC767格式异常值较少。   
3. 因为前面没做全参的解码。所以,要做复杂的分析, 只能通过修改`TEST_myqar.py`达到目的。   
   这一步, 用python3, 是因为这个语言比较有优势。   


## 其他  
* 认为此项目对您有帮助，请点个星星，或留个言，或发封邮件给我，让我高兴一下.  
  If you think this project is helpful to you, click a Star, or leave a message, or send me an Email to make me happy.


