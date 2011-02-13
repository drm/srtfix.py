"""A simple command line SRT convertor tool. Apply shift and factor to SRT timings."""
__author__ = "Gerard van Helden <drm@melp.n>"

import re
import sys
import argparse

class TimeParseError:
    'Thrown whenever a parse error occurs in Time.parse'
    def __init__(self, msg, time):
        self._msg = msg
        self._time = time

    def __str__(self):
        return "%s (%s)" % (self._msg, self._time)
    
class Time:
    '''A Time abstraction class, mapping time values to milliseconds internally and representing it
    as strings. The class implements adding, substracting, multiplication and division through
    arithmetic operators'''

    _HOURS = 3600000
    _MINS  = 60000
    _SECS  = 1000
    _MSECS = 1
    
    PARTS = {
        'h': _HOURS,
        'm': _MINS,
        's': _SECS,
        'ms': _MSECS
    }
    PARTS_V = PARTS.values()
    PARTS_V.sort(reverse=True)

    RE_TIME = re.compile(r'(\d{1,2}):(\d{1,2}):(\d{1,2}),(\d+)')
    RE_OFFSET = re.compile(r'^-?(\d+)(ms|[hms])-?')
    
    @classmethod
    def parse(cls, time):
        """Parses a string representation of time and returns a Time instance. Valid formats are:
        - 01:02:03,004
          1 hour, 2 minutes, 3 seconds and 4 milliseconds
        - 1h2m3s4ms
          Same value
        Any combination of 'h', 'm', 's', or 'ms' suffixed values. Values prefixed or suffixed by a dash are
        considered negative values."""

        time = str(time)
        offs = cls.RE_OFFSET.match(time)
        if offs:
            mapping = cls.PARTS
            negative = time[0] == "-" or time[-1] == "-"
            msecs = 0
            while offs:
                if offs.group(2) in mapping:
                    msecs += mapping[offs.group(2)] * float(offs.group(1))
                else:
                    msecs += mapping['s'] * float(offs.group(1))
                time = time[len(offs.group(0)):]
                if len(time):
                    offs = cls.RE_OFFSET.match(time)
                else:
                    offs = False

            if negative:
                msecs = -msecs
        else:
            try:
                t = map(int, cls.RE_TIME.match(time).group(1, 2, 3, 4))
            except AttributeError:
                raise TimeParseError("Invalid format, could not parse", time)
            msecs = 0
            for i, v in enumerate(cls.PARTS_V):
                msecs += v * t[i]
        return Time(msecs)
            
        
    def __init__(self, ms):
        self.ms = int(ms)
        self._ms = None
        
    def __str__(self):
        ret = ""
        if self.ms < 0:
            ret += "-"
        ret += ":".join(map(lambda d: "%02d" % abs(d), self._asdict().values()[0:3]))
        ret += ',%03d' % abs(self._asdict()[self._MSECS])
        return ret

    def __int__(self):
        return self.ms
           
    def __add__(self, ms):
        if isinstance(ms, str):
            ms = Time.parse(ms)
        if isinstance(ms, Time):
            ms = ms.ms

        return Time(self.ms + int(ms))
        
    def __mul__(self, factor):
        return Time(self.ms * factor)

    def _asdict(self):
        if None == self.ms or self.ms != self._ms:
            self._ms = self.ms
            self._d = {}
            rest = abs(self.ms)
            for i in Time.PARTS_V:
                self._d[i] = int(rest / i)
                if self._ms < 0:
                    self._d[i] *= -1
                rest %= i
        return self._d

class Span:
    SEP = " --> "
    
    @classmethod
    def parse(cls, line):
        return Span(*map(Time.parse, map(str.strip, line.split(cls.SEP))))
        
    def __init__(self, stime, etime):
        self.stime = stime
        self.etime = etime
        
    def __str__(self):
        return Span.SEP.join(map(str, (self.stime, self.etime)))
        
    def __add__(self, time):
        return Span(self.stime + time, self.etime + time)
        
    def __mul__(self, factor):
        return Span(self.stime * factor, self.etime * factor)


class Entry:
    RE_NUMBER = re.compile(r'^\d+$')

    @classmethod
    def group_lines(cls, lines):
        group = []
        index = 0
        for line in lines:
            m = cls.RE_NUMBER.match(line)
            if m:
                if len(group) > 0:
                    yield (index, group)
                    group = []
                index = int(m.group(0))
            else:
                group.append(line)
        if len(group):
            yield (index, group)

    def __init__(self, index, span, data):
        self.index = index
        self.span = span
        self.data = data
        
    def __str__(self):
        return "\r\n".join([
            str(self.index), 
            str(self.span), 
            str(self.data)
        ]) + "\r\n"
        
    def __add__(self, ms):
        return Entry(self.index, self.span + ms, self.data)
        
    def __mul__(self, factor):
        return Entry(self.index, self.span * factor, self.data)

    
    
class EntryList:
    @classmethod
    def parse(cls, lines):
        ret = cls()
        for i, entry in Entry.group_lines(map(str.strip, lines)):
            ret.append(Entry(i, Span.parse(entry[0]), "\r\n".join(entry[1:])))
        return ret
                
    def __init__(self):
        self.entries = {}
        
    def append(self, entry):
        self.entries[entry.index]=entry

    def __iter__(self):
        return iter(self.entries)
        
    def __getitem__(self, index):
        return self.entries[index]
        
    def __add__(self, time):
        ret = EntryList()
        for i in self.entries:
            ret.append(self.entries[i] + time)
        return ret
        
    def __mul__(self, factor):
        ret = EntryList()
        for i in self.entries:
            ret.append(self.entries[i] * factor)
        return ret
        
    def __str__(self):
        return "".join(map(str, self.entries.values()))


def main():
    parser = argparse.ArgumentParser(description="Fix an SRT file's timings")
    parser.add_argument(
        '-i',
        dest='input',
        metavar="INPUT",
        type=str,
        nargs=1,
        default='-',
        help="Input file (omit for stdin)"
    )
    parser.add_argument(
        '-o',
        dest='output',
        metavar="OUTPUT",
        type=str,
        nargs=1,
        default='-',
        help="Output file (omit for stdout)"
    )
    parser.add_argument(
        '-s',
        dest='shift',
        type=str,
        nargs=1,
        default=0,
        help="Shift the subtitles by number of hours, minutes, seconds or milliseconds. The format is either hh:mm:ss,ms or 01h02m03s04ms, whereas the latter can be provided in any combination. A minus can be appended to do a negative shift"
    )
    parser.add_argument(
        '-f',
        dest='convert_framerate',
        type=str,
        nargs=1,
        default=1.0,
        help="Apply framerate conversion. Format is -f 25/24 or -f 0.9"
    )

    o = parser.parse_args()

    if o.input[0] == '-':
        ifile = sys.stdin
    else:
        ifile = open(o.input[0], 'r')
    if o.output[0] == '-':
        ofile = sys.stdout
    else:
        ofile = open(o.output[0], 'w')
        
    data = EntryList.parse(iter(ifile))
    if o.shift:
        data += o.shift[0]
    if o.convert_framerate:
        try:
            (iframes, oframes) = map(float, o.convert_framerate[0].split('/'))
            o.convert_framerate = iframes/oframes
        except:
            pass
        data *= float(o.convert_framerate)
    ofile.write(str(data))
    
if __name__ == "__main__":
    main()

