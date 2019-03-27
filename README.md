================================

#  __The Spectator App.__

================================

## Overview  
The Spectator App. is developed for extension to a soccer monitor that is used in RoboCup soccer simulation 2D league. 
The aim of the extension is to make the experience of watching games more entertaining. 

This app. uses these softwares.  
- [soccerwindow2](https://ja.osdn.net/projects/rctools/downloads/68532/soccerwindow2-5.1.1.tar.gz/)  
- [librcsc](https://ja.osdn.net/projects/rctools/downloads/51941/librcsc-4.1.0.tar.gz/)  

## Demonstration
The demonstration and the tutorial are shown in the [YouTube](https://youtu.be/XFsRj6JVx_E).

## Requirement
- OS : Ubuntu  
- [rcssserver](https://github.com/rcsoccersim/rcssserver)  
- Python : 2.7.15  
- Tensorflow : 1.12.0  

## Install
```
git clone http://github.com/rinmunagi/spectator_app
```

## Usage
```
cd ./soccerwindow  
./bootstrap  
./configure 
make  
cd ../  
./execute  
```
The three windows (the two soccerwindows and the SituationScore window) are launched.  
Start the rcssserver, and connect **the both soccerwindows** to the server.  
Run the team scripts and 'KickOff'.  

## License
[MIT](https://github.com/rinmunagi/spectator_app/blob/master/LICENSE)


## Author
- Yudai Suzuki (Osaka Prefecture University)  
- Takuya Fukushima (Osaka Prefecture University)  
- Lea Thibout (Osaka Prefecture University)  
- Tomoharu Nakashima (Osaka Prefecture University)  
- Hidehisa Akiyama (Fukuoka University)  

