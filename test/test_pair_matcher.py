# This file is part of seq_crumbs.
# seq_crumbs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# seq_crumbs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR  PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with seq_crumbs. If not, see <http://www.gnu.org/licenses/>.

import unittest
import os
from cStringIO import StringIO
from subprocess import check_output, CalledProcessError
from tempfile import NamedTemporaryFile

from crumbs.utils.test_utils import TEST_DATA_DIR
from crumbs.pairs import match_pairs, interleave_pairs, deinterleave_pairs
from crumbs.iterutils import flat_zip_longest
from crumbs.utils.bin_utils import BIN_DIR
from crumbs.seqio import read_seqrecords
from crumbs.exceptions import InterleaveError

# pylint: disable=R0201
# pylint: disable=R0904


class PairMatcherTest(unittest.TestCase):
    'It tests the mate pair checker'

    @staticmethod
    def test_mate_pair_checker():
        'It test the mate pair function'
        # with equal seqs but the last ones
        file1 = os.path.join(TEST_DATA_DIR, 'pairend1.sfastq')
        file2 = os.path.join(TEST_DATA_DIR, 'pairend2.sfastq')
        fwd_seqs = read_seqrecords([open(file1)], 'fastq')
        rev_seqs = read_seqrecords([open(file2)], 'fastq')

        out_fhand = StringIO()
        orphan_out_fhand = StringIO()
        out_format = 'fastq'
        seqs = flat_zip_longest(fwd_seqs, rev_seqs)
        match_pairs(seqs, out_fhand, orphan_out_fhand, out_format)

        output = out_fhand.getvalue()
        assert '@seq1:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG' in output
        assert '@seq2:136:FC706VJ:2:2104:15343:197393 2:Y:18:ATCACG' in output
        orp = orphan_out_fhand.getvalue()
        assert '@seq8:136:FC706VJ:2:2104:15343:197393 2:Y:18:ATCACG' in orp

        # with the firsts seqs different
        file1 = os.path.join(TEST_DATA_DIR, 'pairend1.sfastq')
        file2 = os.path.join(TEST_DATA_DIR, 'pairend3.sfastq')
        fwd_seqs = read_seqrecords([open(file1)], 'fastq')
        rev_seqs = read_seqrecords([open(file2)], 'fastq')
        out_fhand = StringIO()
        orphan_out_fhand = StringIO()
        out_format = 'fastq'
        seqs = flat_zip_longest(fwd_seqs, rev_seqs)
        match_pairs(seqs, out_fhand, orphan_out_fhand, out_format)

        output = out_fhand.getvalue()
        assert '@seq4:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG' in output
        assert '@seq5:136:FC706VJ:2:2104:15343:197393 2:Y:18:ATCACG' in output
        orp = orphan_out_fhand.getvalue()
        assert '@seq1:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG' in orp
        assert '@seq3:136:FC706VJ:2:2104:15343:197393 2:Y:18:ATCACG' in orp
        assert '@seq6:136:FC706VJ:2:2104:15343:197393 2:Y:18:ATCACG' in orp

        file1 = os.path.join(TEST_DATA_DIR, 'pairend4.sfastq')
        file2 = os.path.join(TEST_DATA_DIR, 'pairend2.sfastq')
        fwd_seqs = read_seqrecords([open(file1)], 'fastq')
        rev_seqs = read_seqrecords([open(file2)], 'fastq')
        out_fhand = StringIO()
        orphan_out_fhand = StringIO()
        out_format = 'fastq'

        seqs = flat_zip_longest(fwd_seqs, rev_seqs)
        match_pairs(seqs, out_fhand, orphan_out_fhand, out_format)

        output = out_fhand.getvalue()
        assert '@seq8:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG' in output
        assert '@seq8:136:FC706VJ:2:2104:15343:197393 2:Y:18:ATCACG' in output
        orp = orphan_out_fhand.getvalue()
        assert '@seq1:136:FC706VJ:2:2104:15343:197393 2:Y:18:ATCACG' in orp
        assert '@seq2:136:FC706VJ:2:2104:15343:197393 2:Y:18:ATCACG' in orp


class PairMatcherbinTest(unittest.TestCase):
    'It test the matepair binary'
    def test_pair_matcher_bin(self):
        'It test the pair matcher binary'
        pair_matcher_bin = os.path.join(BIN_DIR, 'pair_matcher')
        assert 'usage' in check_output([pair_matcher_bin, '-h'])

        in_fpath = os.path.join(TEST_DATA_DIR, 'pairend5.sfastq')
        out_fhand = NamedTemporaryFile()
        orphan_fhand = NamedTemporaryFile()
        check_output([pair_matcher_bin, '-o', out_fhand.name,
                      '-p', orphan_fhand.name, in_fpath])

        result = open(out_fhand.name).read()
        assert '@seq1:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG' in result
        assert '@seq1:136:FC706VJ:2:2104:15343:197393 2:Y:18:ATCACG' in result

        orp = open(orphan_fhand.name).read()
        assert '@seq8:136:FC706VJ:2:2104:15343:197393 2:Y:18:ATCACG' in orp

        in_fpath = os.path.join(TEST_DATA_DIR, 'pairend5.sfastq')
        out_fhand = NamedTemporaryFile()
        orphan_fhand = NamedTemporaryFile()
        stderr = NamedTemporaryFile()
        try:
            check_output([pair_matcher_bin, '-o', out_fhand.name,
                          '-p', orphan_fhand.name, in_fpath, '-l', '1'],
                         stderr=stderr)
            self.fail('error expected')
        except CalledProcessError:
            assert 'There are too many consecutive' in open(stderr.name).read()


class InterleavePairsTest(unittest.TestCase):
    'It tests the interleaving and de-interleaving of pairs'
    def test_interleave(self):
        'It interleaves two iterators with paired reads'
        file1 = os.path.join(TEST_DATA_DIR, 'pairend1.sfastq')
        file2 = os.path.join(TEST_DATA_DIR, 'pairend2.sfastq')
        fwd_seqs = read_seqrecords([open(file1)], 'fastq')
        rev_seqs = read_seqrecords([open(file2)], 'fastq')

        try:
            list(interleave_pairs(fwd_seqs, rev_seqs))
            self.fail('InterleaveError expected')
        except InterleaveError:
            pass

        file1 = os.path.join(TEST_DATA_DIR, 'pairend1.sfastq')
        file2 = os.path.join(TEST_DATA_DIR, 'pairend1b.sfastq')
        fwd_seqs = read_seqrecords([open(file1)], 'fastq')
        rev_seqs = read_seqrecords([open(file2)], 'fastq')

        seqs = list(interleave_pairs(fwd_seqs, rev_seqs))
        assert len(seqs) == 8

    def test_deinterleave(self):
        'It de-interleaves an iterator of alternating fwd and rev reads'

        fhand1 = os.path.join(TEST_DATA_DIR, 'pairend1.sfastq')
        fhand2 = os.path.join(TEST_DATA_DIR, 'pairend1b.sfastq')
        fwd_seqs = read_seqrecords([open(fhand1)], 'fastq')
        rev_seqs = read_seqrecords([open(fhand2)], 'fastq')

        seqs = interleave_pairs(fwd_seqs, rev_seqs)
        out_fhand1 = StringIO()
        out_fhand2 = StringIO()
        out_format = 'fastq'
        deinterleave_pairs(seqs, out_fhand1, out_fhand2, out_format)
        result1 = out_fhand1.getvalue()
        result2 = out_fhand2.getvalue()
        assert result1.strip() == open(fhand1).read().strip()
        assert result2.strip() == open(fhand2).read().strip()


class InterleaveBinTest(unittest.TestCase):
    'test of the interleave and deinterleave'

    def test_binaries(self):
        'It test the binaries'
        interleave_bin = os.path.join(BIN_DIR, 'interleave_pairs')
        deinterleave_bin = os.path.join(BIN_DIR, 'deinterleave_pairs')
        assert 'usage' in check_output([interleave_bin, '-h'])
        assert 'usage' in check_output([deinterleave_bin, '-h'])

        in_fpath1 = os.path.join(TEST_DATA_DIR, 'pairend1.sfastq')
        in_fpath2 = os.path.join(TEST_DATA_DIR, 'pairend1b.sfastq')
        out_fhand = NamedTemporaryFile()

        check_output([interleave_bin, '-o', out_fhand.name,
                      in_fpath1, in_fpath2])
        result = open(out_fhand.name).read()
        assert '@seq5:136:FC706VJ:2:2104:15343:197393 2:Y:18:ATCACG' in result
        assert '@seq5:136:FC706VJ:2:2104:15343:197393 1:Y:18:ATCACG' in result

        out_fhand1 = NamedTemporaryFile()
        out_fhand2 = NamedTemporaryFile()
        check_output([deinterleave_bin, '-o', out_fhand1.name, out_fhand2.name,
                      out_fhand.name])
        assert open(in_fpath1).read() == open(out_fhand1.name).read()
        assert open(in_fpath2).read() == open(out_fhand2.name).read()


if __name__ == '__main__':
    #import sys;sys.argv = ['', 'IterutilsTest.test_group_in_packets']
    unittest.main()