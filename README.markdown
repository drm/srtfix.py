## srtfix.py: fix badly converted SRT files ##

Ever downloaded badly synced SRT files, because someone converted framebased subtitle files to SRT without considering the right framerate? I have, and it annoys me pretty much. UI tools usually take more time in fixing this (because they generally do not offer the options of converting a framerate in a time-based format such as SRT). With this little command line tool you'll fix within seconds.

### Examples ###

Convert 25-based to 24-based framerate

    $ python2.7 srtfix.py -i src.srt -o out.srt -f 25/24
    
Convert 23.976 to 25 based and shift the SRT 3 minutes right

    $ python2.7 srtfix.py -i src.srt -o out.srt -f 23.976/25 -s 3m
    
Use pipes in stead of arguments

    $ python2.7 srtfix.py -f 25/24 < src.srt > out.srt
  

