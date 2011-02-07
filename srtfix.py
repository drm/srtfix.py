"""A simple command line SRT convertor tool. Apply shift and factor to SRT timings.
@author Gerard van Helden <drm@melp.nl>"""

import re;
import sys;
import argparse;

class Time:
    HOURS = 3600000
    MINS  = 60000
    SECS  = 1000
    MSECS = 1
    
    PARTS = {
        'h': HOURS,
        'm': MINS,
        's': SECS,
        'ms': MSECS
    }
    PARTS_V = PARTS.values()
    list.sort(PARTS_V)
    list.reverse(PARTS_V)

    
    RE_TIME = re.compile(r'(\d{1,2}):(\d{1,2}):(\d{1,2}),(\d+)')
    RE_OFFSET = re.compile(r'^-?(\d+)([hms]|ms)?$')
    
    @classmethod
    def parse(cls, time):
        offs = cls.RE_OFFSET.match(time)
        if(offs):
            mapping = cls.PARTS
            if offs.group(2) in mapping:
                msecs = mapping[offs.group(2)] * float(offs.group(1))
            else:
                msecs = mapping['s'] * float(offs.group(1))
            if time[0] == '-':
                msecs = -msecs;
        else:
            t = map(int, cls.RE_TIME.match(time).group(1, 2, 3, 4))
            msecs = cls.HOURS * t[0] + cls.MINS * t[1] + cls.SECS * t[2] + cls.MSECS * t[3]

        return Time(msecs)
            
        
    def __init__(self, ms):
        self.ms = int(ms)
        self._ms = -1
        
    def __str__(self):
        return ":".join(map(lambda d: "%02d" % d, (self.hours(), self.mins(), self.secs()))) + ',%03d' % self.msecs();
    
    def __int__(self):
        return self.ms
           
    def hours(self):
        return self._asdict()[Time.HOURS]
        
    def mins(self):
        return self._asdict()[Time.MINS]
        
    def secs(self):
        return self._asdict()[Time.SECS]
        
    def msecs(self):
        return self._asdict()[Time.MSECS]
        
    def __add__(self, ms):
        if isinstance(ms, str):
            ms = Time.parse(ms)
        if isinstance(ms, Time):
            ms = ms.ms

        return Time(self.ms + int(ms))
        
    def __mul__(self, factor):
        return Time(self.ms * factor)

    def _asdict(self):
        if self.ms != self._ms:
            self._ms = self.ms
            self._d = {}
            rest = self.ms;
            for i in Time.PARTS_V:
                self._d[i] = int(rest / i)
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
        count = 0;
        group = []
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
        ]) + "\r\n";
        
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
        return iter(self.entries);
        
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
    parser = argparse.ArgumentParser(description="Fix an SRT file's timings");
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
        help="Shift the subtitles by number of hours, minutes, seconds or milliseconds"
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

