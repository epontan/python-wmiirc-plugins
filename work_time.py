#!/usr/bin/env python

import os
import sys
import time


def secs2dec(secs):
    return secs / 3600.0

def secs2str(secs):
    return '%dh %02dm' % (secs / 3600, secs % 3600 / 60)

def str2time(t_str):
    return time.strptime(t_str, '%Y-%m-%d %H:%M:%S')

def time2unix(t):
    return int(time.mktime(t))


class WorkTime(object):

    def __init__(self, input_file=None):
        self.start = 0
        self.lunch = 0
        self.locked = 0
        self.timestamp = 0

        if input_file and os.path.exists(input_file):
            for line in open(input_file).readlines():
                self.analyze(line)


    # FIXME: This needs to be smarter
    def analyze(self, record):
        state, timestamp, activity = record.split('|', 2)
        t = str2time(timestamp)
        ts = time2unix(t)

        if not self.timestamp:
            self.start = ts

        if state == 'LOCKED':
            self.locked = ts

        elif state == 'UNLOCKED':
            lock_time = ts - self.locked

            if lock_time > 36000:
                self.start = ts
                self.lunch = 0
                self.locked = 0
                return

            if t.tm_hour >= 11 and t.tm_hour <= 13 and lock_time > 1800 and not self.lunch:
                self.lunch = lock_time > 5000 and 5000 or lock_time
                self.locked = 0

        self.timestamp = ts


    def get_time_worked(self):
        return secs2str(self.timestamp - self.start - self.lunch)

    def get_time_worked_decimal(self):
        return secs2dec(self.timestamp - self.start - self.lunch)

    def get_time_lunched(self):
        return secs2str(self.lunch)

    def get_time_lunched_decimal(self):
        return secs2dec(self.lunch)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'usage: %s FILE [FILE...]' % os.path.basename(sys.argv[0])
        sys.exit(0)

    print 'DAY FILE\tWORK TIME\tLUNCH TIME\tDEC'
    for f in sys.argv[1:]:
        if not os.path.isfile(f):
            print 'ERROR: "%s" does not exist or is not a file!' % f
            continue
        wt = WorkTime(f)
        print '%s:\t%7s\t\t[ %s ]\t%5.2f' % (
                os.path.basename(f),
                wt.get_time_worked(),
                wt.get_time_lunched(),
                wt.get_time_worked_decimal())

