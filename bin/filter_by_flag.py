#!/usr/bin/env python
'''
Created on 2013 urt 18

@author: peio
'''
import argparse
import sys
import subprocess
from operator import or_

SAM_FLAG_BITS = {
    'is_paired': 0x0001,  # the read is paired in sequencing
    'is_in_proper_pair': 0x0002,  # the read is mapped in a proper pair
    'is_unmapped': 0x0004,  # the query sequence itself is unmapped
    'mate_is_unmapped': 0x0008,  # the mate is unmapped
    'strand': 0x0010,  # strand of the query (1 for reverse)
    'mate_strand': 0x0020,  # strand of the mate
    'is_first_in_pair': 0x0040,  # the read is the first read in a pair
    'is_second_in_pair': 0x0080,  # the read is the second read in a pair
    'is_not_primary': 0x0100,  # the alignment is not primary
    'failed_quality': 0x0200,  # the read fails platform/vendor quality checks
    'is_duplicate': 0x0400,  # the read is either a PCR or an optical duplicate
}

SAM_FLAG_TAGS = list(sorted(SAM_FLAG_BITS.viewkeys()))


def create_sam_flag(bit_tags):
    'It returns the integer corresponding to the bitwise or of the tags'
    return reduce(or_, [SAM_FLAG_BITS[t] for t in bit_tags])


def filter_bam(in_fpath, out_fpath, min_mapq=0, required_flag_tags=None,
               filtering_flag_tags=None, regions=None):
    'It filters a BAM file'
    cmd = ['samtools', 'view', '-bh']

    if min_mapq:
        cmd.extend(['-q', str(min_mapq)])

    if required_flag_tags:
        flag = create_sam_flag(required_flag_tags)
        cmd.extend(['-f', str(flag)])

    if filtering_flag_tags:
        flag = create_sam_flag(filtering_flag_tags)
        cmd.extend(['-F', str(flag)])

    cmd.extend(['-o', out_fpath, in_fpath])

    if regions:
        regions = ['{0}:{1}-{2}'.format(*s) for s in regions.segments]
        cmd.extend(regions)

    subprocess.check_call(cmd)


def _setup_argparse():
    'It prepares the command line argument parsing.'
    description = 'Rename the trinity output file seqs'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('input', help="bam file with mapping result",
                       type=argparse.FileType('rt'))

    parser.add_argument('-o', '--bam_output', default='output.bam',
                        help='gff output file', type=argparse.FileType('wt'))
    parser.add_argument('--req_flag', action='append',
                        help='required SAM flag', choices=SAM_FLAG_TAGS)
    parser.add_argument('--filter_flag', action='append',
                        help='filtering SAM flag', choices=SAM_FLAG_TAGS)
    msg = 'Minimum mapq to use the read to count coverage'
    parser.add_argument('-p', '--min_mapq', help=msg, type=int)

    return parser


def _parse_args(parser):
    '''It parses the command line and it returns a dict with the arguments.'''
    parsed_args = parser.parse_args()
    args = {}
    args['bam_fhand'] = parsed_args.input
    args['gff_fhand'] = parsed_args.gff_output
    args['required_flags'] = parsed_args.req_flag
    args['filtering_flags'] = parsed_args.filter_flag
    args['min_mapq'] = parsed_args.min_mapq

    return args


def main():
    'the main part'
    parser = _setup_argparse()
    args = _parse_args(parser)

    filter_bam(in_fpath=args['bam_fhand'].name,
               out_fpath=args['out_fhand'].name,
               min_mapq=args['min_mapq'],
               required_flag_tags=args['required_flags'],
               filtering_flag_tags=args['filtering_flags'],
               regions=None)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        sys.argv.append('-h')
    main()
