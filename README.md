# FlightDataDecode
Flight Data Decode

[FOQA (Flight Operations Quality Asurance)](http://en.wikipedia.org/wiki/Flight_operations_quality_assurance)

这个项目，并没有达到可用状态。  
只是我在研究 无线QAR(WQAR) 原始 raw.dat 文件过程中，编写的测试程序。  
有兴趣的，可以参考一下，继续研究。  

这些程序都在 [wgl 目录中](https://github.com/osnosn/FlightDataDecode/tree/main/wgl)。

## 更新
* 2022-02 第一次更新  
  - `get_param_from_wgl.py`最终可以提取出单个的记录参数(原始值,还没转换为使用值)。  
* 2022-02 再次更新  
  - `get_param_from_wgl.py` 可以获取部分 BNR,BCD,CHARACTER 类型的值，并转换为使用值。  
  - 问题: UTC 类型的似乎不行。参数的rate没有处理。  


