# wgl 目录  

此目录中的 py 脚本，都可以作为命令行程序运行。   
直接运行，会给出帮助。   
```
$ ./get_param_from_wgl.py
Usage:
 读取 wgl中 raw.dat 。
   读解码一个参数。
 命令行工具。
./get_param_from_wgl.py [-h|--help] [-f|--file]
   * (必要参数)
   -h, --help                 print usage.
 * -f, --file xxx.wgl.zip     "....wgl.zip" filename
 * -p, --param alt_std        show "ALT_STD" param. 自动全部大写。
   --paramlist                list all param name.
   -w xxx.csv            参数写入文件"xxx.csv"
   -w xxx.csv.gz         参数写入文件"xxx.csv.gz"
```

wgl 目录中有两个空文件，只是给出个例子，看看压缩包中文件名的命名规律。  
  * `B-1234_20210121132255.wgl.zip` ,这是 ARINC 717 aligned   
  * `B-123420220102114550M.zip` ,这是 ARINC 767 格式  

`Get_param_from_arinc717_aligned.py` , `Get_param_from_wgl.py` 这两个文件的内容是一样的。  

这些程序需要 vec 目录中的配置文件。   
配置文件的来源，请看 [vec目录中的README](https://github.com/osnosn/FlightDataDecode/tree/main/wgl/vec).   




