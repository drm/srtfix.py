"""Unit tests for the srtfix.py lib"""
from exceptions import Exception
from srtfix import Time, Span, TimeParseError
import unittest
import random

__author__ = "Gerard van Helden <drm@melp.n>"


def data_provider(data):
    """Data provider decorator, allows a callable to provide the data for the test"""
    if callable(data):
        data = data()

    if not all(isinstance(i, tuple) for i in data):
        raise Exception("Need a sequence of tuples as data...")

    def test_decorator(fn):
        def test_decorated(self, *args):
            for i in data:
                try:
                    fn(self, *(i + args))
                except AssertionError as e:
                    raise AssertionError(e.message + " (data set used: %s)" % repr(i))
        return test_decorated
    return test_decorator

def expect_exception(exception):
    """Marks test to expect the specified exception. Call assertRaises internally"""
    def test_decorator(fn):
        def test_decorated(self, *args, **kwargs):
            self.assertRaises(exception, fn, self, *args, **kwargs)
        return test_decorated
    return test_decorator

class TimeTest(unittest.TestCase):
    srt_format_data = (
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

    @data_provider( (("",), ("unparsable",), ( "--0",),) )
    @expect_exception(TimeParseError)
    def test_parse_invalid_format(self, format):
        Time.parse(format)

    shorthand_format_data = (
        (1, '1ms'),
        (1000, '1s'),
        (60000, '1m'),
        (3600000, '1h'),

        (-1, '-1ms'),
        (-1000, '-1s'),
        (-60000, '-1m'),
        (-3600000, '-1h'),

        (-1, '1ms-'),
        (-1000, '1s-'),
        (-60000, '1m-'),
        (-3600000, '1h-'),

        (1001, '1ms1s'),
        (1001, '1s1ms'),
        (3600001, '1h1ms'),
        (3661001, '1h1s1m1ms'),
        (3661001, '1ms1s1m1h'),
        (3661001, '1m1ms1h1s'),

        (-1001, '-1ms1s'),
        (-1001, '-1s1ms'),
        (-3600001, '-1h1ms'),
        (-3661001, '-1h1s1m1ms'),
        (-3661001, '-1ms1s1m1h'),
        (-3661001, '-1m1ms1h1s'),

        (-1001, '1ms1s-'),
        (-1001, '1s1ms-'),
        (-3600001, '1h1ms-'),
        (-3661001, '1h1s1m1ms-'),
        (-3661001, '1ms1s1m1h-'),
        (-3661001, '1m1ms1h1s-'),
    )

    @data_provider(shorthand_format_data)
    def test_parse_shorthand_format(self, expected, shorthand_format):
        self.assertEquals(expected, Time.parse(shorthand_format).ms)

    str_data = (
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

        (-1, '-00:00:00,001'),
        (-1000, '-00:00:01,000'),
        (-1001, '-00:00:01,001'),
        (-60000, '-00:01:00,000'),
        (-60001, '-00:01:00,001'),
        (-61000, '-00:01:01,000'),
        (-61001, '-00:01:01,001'),
        (-3600000, '-01:00:00,000'),
        (-3660000, '-01:01:00,000'),
        (-3661000, '-01:01:01,000'),
        (-3661001, '-01:01:01,001'),
        (-35999999, '-09:59:59,999'),
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

    def test_int(self):
        r = random.randint(1, 99999999)
        t = Time(r)
        self.assertEquals(int(t), r)

    add_data = (
        (3000, Time(1000), Time(2000)),
        (3000, Time(1000), '2s'),
        (-1000, Time(1000), '-2s'),
        (3000, Time(1), '2999ms'),
        (1, Time(3000), '-2999ms'),
        (3000, Time(1000), '0:0:2,000'),
        (3000, Time(5999), '-2999ms'),
    )

    @data_provider(add_data)
    def test_add(self, expect, t1, t2):
        self.assertEquals(expect, int(t1 + t2))

    mul_data = (
        (3000, Time(1000), 3),
    )

    @data_provider(mul_data)
    def test_mul(self, expect, t1, t2):
        self.assertEquals(expect, int(t1 * t2))


class SpanTest(unittest.TestCase):
    span_format_data = (
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

    str_data = (
        ( '00:00:00,001 --> 00:00:00,002', '0:0:0,1 --> 0:0:0,2' ),
        ( '09:59:59,990 --> 09:59:59,999', '9:59:59,990 --> 9:59:59,999' ),
    )
    @data_provider(str_data)
    def test_mul(self, formatted, span_format):
        s = Span.parse(span_format)
        self.assertEquals(formatted, str(s))


