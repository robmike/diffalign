#!/usr/env python

import getopt
import re
import difflib
import functools
import os
import sys
import itertools
import time
from tempfile import TemporaryFile, NamedTemporaryFile
from subprocess import Popen, PIPE
from StringIO import StringIO
import pdb
from pprint import pprint
import logging

logging.basicConfig(level=logging.DEBUG)
logging.level=logging.DEBUG

hunk_header_re = re.compile(r'^@@ -(\d+)(,(\d+))? \+(\d+)(,(\d+))? @@$', re.M)

class DiffAlign(object):

    def __init__(self, lfile, rfile, diffopts=[],
                 alignpts=[(0,0)], diffcmd="diff", outfile=sys.stdout):
        self.lfile = lfile
        self.rfile = rfile
        # Must use unified output and we cannot currently handle
        # context.
        self.diffopts = diffopts + ['-U0']
        self._alignidx = 0
        self.diffcmd = diffcmd
        self.outfile = outfile

        self.alignpts = sorted(alignpts)
        # Implicit alignment at beginning of file
        if not alignpts:
            alignpts=[(0,0)]
        elif self.alignpts[0] != (0,0):
            self.alignpts.insert(0, (0,0))


    def write_diff_header(self):

        def mtime(fhandle):
            return time.ctime(os.stat(fhandle.name).st_mtime)

        header = '--- %s %s\n' % (self.lfile.name, mtime(self.lfile))
        header += '+++ %s %s\n' % (self.rfile.name, mtime(self.rfile))
        self.outfile.write(header)
        return

    def _increment_line_offset(self, m):
        l1 = int(m.group(1))
        r1 = int(m.group(4))
        l2 = m.group(2) or ''
        r2 = m.group(5) or ''

        alignpt = self.alignpts[self._alignidx]
        linc = alignpt[0]
        rinc = alignpt[1]
        s = '@@ -%i%s +%i%s @@' % (l1 + linc, l2, r1 + rinc, r2)
        logging.debug("Replacing %s with %s" % (m.group(0), s))
        return s

    def _diff_chunks(self):
        '''Diff the "current" subsections of lfile and rfile'''

        while self._alignidx < len(self.alignpts):

            # Copy "current" section of files into temp files to be passed
            # to diff command
            tmpfiles = [NamedTemporaryFile(), NamedTemporaryFile()]

            for i,f in enumerate([self.lfile, self.rfile]):
                alignidx = self._alignidx
                line_idx = self.alignpts[alignidx][i]

                while True:
                    # End is at next alignment point or end of file if none
                    if alignidx < len(self.alignpts) - 1:
                        if line_idx >= self.alignpts[alignidx+1][i]:
                            logging.debug("Reached alignment %i in %s" %
                                          (line_idx, f.name))
                            break
                    line = f.readline()
                    logging.debug("Read %s from %s" % (line.strip(), f.name))
                    if not line: # EOF
                        logging.debug("Reached EOF in %s" % f.name)
                        break
                    line_idx += 1
                    tmpfiles[i].write(line)
                    if alignidx >= len(self.alignpts):
                        logging.debug("Reached last alignment point")
                        break
                tmpfiles[i].flush()

            pargs = [self.diffcmd] + self.diffopts + [x.name for x in tmpfiles]
            proc = Popen(pargs, stdout=PIPE, stderr=PIPE)
            (diff_output, stderr_output) = proc.communicate()
            sys.stderr.write(stderr_output)

            repl_func = self._increment_line_offset
            diff_output = hunk_header_re.sub(repl_func, diff_output)

            # Remove diff header (first two lines)
            diff_output_io = StringIO(diff_output)
            [diff_output_io.readline() for i in range(0,2)]
            self.outfile.write(diff_output_io.read())

            self._alignidx += 1
        return diff_output


    def diff(self):
        self.write_diff_header()
        # Execute the generator until it yields no more
        self._diff_chunks()

def main():
    DiffAlign(open("/tmp/foo.txt"), open("/tmp/bar.txt"),
              alignpts=[(3,3)]).diff()

if __name__ == '__main__':
    main()
