# vec 目录  

是用来存放   
* xxxxxx.vec (DataVer,Parameter,Data Frame 配置文件) ARINC 573 PCM  
* aircraft.air (机号的配置文件)  

vec 和 air 配置文件，是从 AGS 软件中导出的。   

如图:   
<img src="https://github.com/osnosn/FlightDataDecode/raw/main/wgl/vec/readme01.png" width="300" />   
   ----  图1  ----   

----

从airfase中，可以导出4种文件。FAP, Frame, PRM, FRED.   
* FAP, Frame 文件是加密的，无法解开。   
* PRM 是个文本文件。从 PRM 看，配置文件不相同，本程序不适合使用。原理相同,也许你可以自己重写一个程序。   
  参考另一个项目 【[osnosn/FlightDataDecode2/](https://github.com/osnosn/FlightDataDecode2/)】   
* FRED 没见过, 不知道内容。   

其他文件，如图:   
<img src="https://github.com/osnosn/FlightDataDecode/raw/main/wgl/vec/airfase-app.jpg" width="300" />   
   ----  图2  ----   
<img src="https://github.com/osnosn/FlightDataDecode/raw/main/wgl/vec/airfase-FAP.png" width="500" />   
   ----  图3  ----   
<img src="https://github.com/osnosn/FlightDataDecode/raw/main/wgl/vec/airfase-Frame.png" width="300" />   
   ----  图4  ----   
<img src="https://github.com/osnosn/FlightDataDecode/raw/main/wgl/vec/airfase-PRM-header.png" width="300" />   
   ----  图5  ----   
<img src="https://github.com/osnosn/FlightDataDecode/raw/main/wgl/vec/airfase-regular.png" width="500" />   
   ----  图6  ----   
<img src="https://github.com/osnosn/FlightDataDecode/raw/main/wgl/vec/airfase-superframe.png" width="500" />   
   ----  图7  ----   




