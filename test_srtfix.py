from srtfix import Time, Span;
import unittest
import random

def data_provider(fn_data_provider):
    """Data provider decorator, allows another callable to provide the data for the test"""
    def test_decorator(fn):
        def repl(self, *args):
            for i in fn_data_provider():
                try:
                    fn(self, *i)
                except AssertionError:
                    print "Assertion error caught with data set ", i
                    raise
        return repl
    return test_decorator


class TimeTest(unittest.TestCase):
    srt_format_data = lambda: (
        (0, '0:0:0,0'),
        (1, '0:0:0,1'),
        (1000, '0:0:1,0'),
        (1001, '0:0:1,1'),
        (60000, '0:1:0,0'),
        (60001, '0:1:0,1'),
        (61000, '0:1:1,0'),
        (61001, '0:1:1,1'),
        (3600000, '1:0:0,0'),
        (3660000, '1:1:0,0'),
        (3661000, '1:1:1,0'),
        (3661001, '1:1:1,1'),
        (35999999, '9:59:59,999'),
    )

    @data_provider(srt_format_data)
    def test_parse_srt_format(self, expected, srt_format):
        self.assertEquals(expected, Time.parse(srt_format).ms)

    shorthand_format_data = lambda: (
        (1, '1ms'),
        (1000, '1s'),
        (1000, '1'),
        (60000, '1m'),
        (3600000, '1h'),
        
        (-1, '-1ms'),
        (-1000, '-1s'),
        (-1000, '-1'),
        (-60000, '-1m'),
        (-3600000, '-1h'),
    )
    @data_provider(shorthand_format_data)
    def test_parse_shorthand_format(self, expected, shorthand_format):
        self.assertEquals(expected, Time.parse(shorthand_format).ms)
        
    str_data = lambda: (
        (0, '00:00:00,000'),
        (1, '00:00:00,001'),
        (1000, '00:00:01,000'),
        (1001, '00:00:01,001'),
        (60000, '00:01:00,000'),
        (60001, '00:01:00,001'),
        (61000, '00:01:01,000'),
        (61001, '00:01:01,001'),
        (3600000, '01:00:00,000'),
        (3660000, '01:01:00,000'),
        (3661000, '01:01:01,000'),
        (3661001, '01:01:01,001'),
        (35999999, '09:59:59,999'),
    )
    @data_provider(str_data)
    def test_str(self, time, expected):
        self.assertEquals(expected, str(Time(time))) 
    
    
    parts_data = lambda: (
        (0, (0, 0, 0, 0)),
        (1, (0, 0, 0, 1)),
        (1000, (0, 0, 1, 0)),
        (1001, (0, 0, 1, 1)),
        (60000, (0, 1, 0, 0)),
        (60001, (0, 1, 0, 1)),
        (61000, (0, 1, 1, 0)),
        (61001, (0, 1, 1, 1)),
        (3600000, (1, 0, 0, 0)),
        (3660000, (1, 1, 0, 0)),
        (3661000, (1, 1, 1, 0)),
        (3661001, (1, 1, 1, 1)),
        (35999999, (9, 59, 59, 999)),
    )
    
    @data_provider(parts_data)
    def test_parts(self, time, parts):
        t = Time(time)
        self.assertEquals(parts, (t.hours(), t.mins(), t.secs(), t.msecs()))

    def test_int(self):
        r = random.randint(1, 99999999)
        t = Time(r)
        self.assertEquals(int(t), r);
        
    add_data = lambda: (
        (3000, Time(1000), Time(2000)),
        (3000, Time(1000), '2'),
        (3000, Time(1), '2999ms'),
        (3000, Time(1000), '0:0:2,000'),
        (3000, Time(5999), '-2999ms'),
    )
    @data_provider(add_data)
    def test_add(self, expect, t1, t2):
        self.assertEquals(expect, int(t1 + t2))
        
    mul_data = lambda: (
        (3000, Time(1000), 3),
    )
    @data_provider(mul_data)
    def test_mul(self, expect, t1, t2):
        self.assertEquals(expect, int(t1 * t2))
  
        
class SpanTest(unittest.TestCase):
    span_format_data = lambda: (
        ( [1, 2], '0:0:0,1 --> 0:0:0,2' ),
        ( [35999990, 35999999], '9:59:59,990 --> 9:59:59,999' ),
    )

    @data_provider(span_format_data)
    def test_parse(self, times, span_format):
        s = Span.parse(span_format)
        self.assertEquals(times, map(int, (s.stime, s.etime)))
        
    @data_provider(span_format_data)
    def test_add(self, times, span_format):
        s = Span.parse(span_format) + 100
        self.assertEquals(map(lambda t: t + 100, times), map(int, (s.stime, s.etime))) 
    
    @data_provider(span_format_data)
    def test_mul(self, times, span_format):
        s = Span.parse(span_format) * 4
        self.assertEquals(map(lambda t: t * 4, times), map(int, (s.stime, s.etime))) 
        
    str_data = lambda: (
        ( '00:00:00,001 --> 00:00:00,002', '0:0:0,1 --> 0:0:0,2' ),
        ( '09:59:59,990 --> 09:59:59,999', '9:59:59,990 --> 9:59:59,999' ),
    )    
    
    @data_provider(str_data)
    def test_mul(self, formatted, span_format):
        s = Span.parse(span_format)
        self.assertEquals(formatted, str(s)) 

