
import unittest
from os.path import join as pjoin
from os.path import dirname
from io import StringIO
from os import remove
from tempfile import NamedTemporaryFile
from subprocess import check_output

from vcf import Reader

from vcf_crumbs.utils import (TEST_DATA_DIR, compress_with_bgzip,
                              index_vcf_with_tabix)
from vcf_crumbs.writers import (IlluminaWriter, _replace_snvs_with_iupac)


VCF_PATH = pjoin(TEST_DATA_DIR, 'sample.vcf.gz')
REF_PATH = pjoin(TEST_DATA_DIR, 'sample_ref.fasta')
VCF_INDEL_PATH = pjoin(TEST_DATA_DIR, 'sample_indel.vcf.gz')


class BareBoneSNP(object):
    def __init__(self, alleles, start, end, is_sv=False):
        self.alleles = alleles
        self.POS = start + 1
        self.start = start
        self.end = end
        allele_lens = [len(allele) for allele in alleles]
        self.is_sv = is_sv
        if is_sv:
            # sv
            self.is_snp = False
            self.is_deletion = False
            self.is_indel = False
        elif len(set(allele_lens)) == 1:
            # snp
            self.is_snp = True
            self.is_deletion = False
            self.is_indel = False
        elif allele_lens[0] == 1:
            # insertion
            self.is_snp = False
            self.is_deletion = False
            self.is_indel = True
        else:
            # deletion
            self.is_snp = False
            self.is_deletion = True
            self.is_indel = True
        self.is_sv = is_sv


class IlluminaWriterTest(unittest.TestCase):
    def test_illumina_writer(self):
        # 01234
        # 1234567890
        # CCTGATTT-A
        # TAACGA
        #   -  C -A
        vcf = '''##fileformat=VCFv4.1
#CHROM POS ID REF ALT QUAL FILTER INFO
ref 1 . C T 10 PASS .
ref 2 . CT CA,C 10 PASS .
ref 3 . T A 10 PASS .
ref 4 . G C 10 PASS .
ref 5 . A G 10 PASS .
ref 6 . T A,C 10 PASS .
ref 7 . TT T 10 PASS .
ref 8 . T TA 10 PASS .
ref 10 . A C 10 PASS .
'''

        vcf = vcf.replace(' ', '\t')
        vcf_fhand = NamedTemporaryFile(suffix='.vcf')
        vcf_fhand.write(vcf)
        vcf_fhand.flush()
        vcf_compressed = NamedTemporaryFile(suffix='.vcf.gz')
        compress_with_bgzip(vcf_fhand, vcf_compressed)
        index_vcf_with_tabix(vcf_compressed.name)

        ref_fhand = NamedTemporaryFile(suffix='.fasta')
        ref_fhand.write('>ref\nACTGATTTA\n')
        ref_fhand.flush()

        out_fhand1 = StringIO()
        writer = IlluminaWriter(ref_fhand.name, out_fhand1, min_length=0,
                                vcf_fpath=vcf_compressed.name)
        for snp in Reader(filename=vcf_compressed.name):
            writer.write(snp)

        # With no SNPs converted to IUPAC around
        out_fhand2 = StringIO()
        writer = IlluminaWriter(ref_fhand.name, out_fhand2, min_length=0)
        for snp in Reader(filename=vcf_compressed.name):
            writer.write(snp)

        remove(vcf_compressed.name + '.tbi')
        expected = u'CHROM\tPOS\tID\tseq\n'
        expected += u'ref\t1\t.\t[C/T]*WSRHT-^A\n'
        expected += u'ref\t2\t.\tY[CT/CA/C]SRHT-^A\n'
        expected += u'ref\t3\t.\tYC[T/A]SRHT-^A\n'
        expected += u'ref\t4\t.\tY*W[G/C]RHT-^A\n'
        expected += u'ref\t5\t.\tY*WS[A/G]HT-^A\n'
        expected += u'ref\t6\t.\tY*WSR[T/A/C]T-^A\n'
        expected += u'ref\t7\t.\tY*WSRH[TT/T]A\n'
        expected += u'ref\t8\t.\tY*WSRHT[T/TA]A\n'
        expected += u'ref\t10\t.\tY*WSRHT-^A[A/C]\n'
        assert expected == out_fhand1.getvalue()

        expected = u'CHROM\tPOS\tID\tseq\nref\t1\t.\t[C/T]'
        assert expected in out_fhand1.getvalue()

    def test_iupac_formater(self):
        seq = 'ACTGA'
        snp = BareBoneSNP(['T', 'A'], 3, 4)
        iupac_seq = _replace_snvs_with_iupac(seq, [snp], seq_offset=1)
        assert iupac_seq == 'ACWGA'

        snp = BareBoneSNP(['T', 'A', 'G'], 3, 4)
        iupac_seq = _replace_snvs_with_iupac(seq, [snp], seq_offset=1)
        assert iupac_seq == 'ACDGA'

        snp = BareBoneSNP(['T', 'A', 'G', 'C'], 3, 4)
        iupac_seq = _replace_snvs_with_iupac(seq, [snp], seq_offset=1)
        assert iupac_seq == 'ACNGA'

        snp = BareBoneSNP(['CT', 'C'], 2, 4)
        iupac_seq = _replace_snvs_with_iupac(seq, [snp], seq_offset=1)
        assert iupac_seq == 'AC-GA'

        snp = BareBoneSNP(['C', 'CC'], 2, 3)
        iupac_seq = _replace_snvs_with_iupac(seq, [snp], seq_offset=1)
        assert iupac_seq == 'AC^TGA'

    def test_errors(self):
        # 01234
        # 1234567890
        # CCTGATTT-A
        # TAACGA
        #   -  C -A
        vcf = '''##fileformat=VCFv4.1
#CHROM POS ID REF ALT QUAL FILTER INFO
ref 1 . C T 10 PASS .
ref 2 . CT CA,C 10 PASS .
ref 3 . T A 10 PASS .
ref 4 . G C 10 PASS .
ref 5 . A G 10 PASS .
ref 6 . T A,C 10 PASS .
ref 7 . TT T 10 PASS .
ref 8 . T TA 10 PASS .
ref 10 . A C 10 PASS .
'''

        vcf = vcf.replace(' ', '\t')
        vcf_fhand = NamedTemporaryFile(suffix='.vcf')
        vcf_fhand.write(vcf)
        vcf_fhand.flush()
        vcf_compressed = NamedTemporaryFile(suffix='.vcf.gz')
        compress_with_bgzip(vcf_fhand, vcf_compressed)
        index_vcf_with_tabix(vcf_compressed.name)

        ref_fhand = NamedTemporaryFile(suffix='.fasta')
        ref_fhand.write('>ref\nACTGATTTA\n')
        ref_fhand.flush()

        out_fhand = StringIO()
        writer = IlluminaWriter(ref_fhand.name, out_fhand,
                                vcf_fpath=vcf_compressed.name)
        snps = Reader(filename=vcf_compressed.name)
        snp = snps.next()
        try:
            writer.write(snp)
            self.fail('NotEnoughAdjacentSequenceError expected')
        except IlluminaWriter.NotEnoughAdjacentSequenceError:
            pass

    def test_run_binary(self):
        binary = pjoin(dirname(__file__), '..', 'bin',
                       'write_snps_for_illumina')
        assert 'usage' in check_output([binary, '-h'])

        reference = pjoin(TEST_DATA_DIR, 'sample_ref.fasta')
        vcf = pjoin(TEST_DATA_DIR, 'sample.vcf.gz')

        cmd = [binary, '-r', reference, '-m', '0', vcf]
        stdout = check_output(cmd)
        assert 'GAAAT[A/C]AA' in stdout
        
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'FilterTest.test_close_to_filter']
    unittest.main()
