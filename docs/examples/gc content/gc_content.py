import pysam
from sbg import cwl


@cwl.to_tool(
    inputs=dict(
        bam_file=cwl.File(secondary_files=['.bai']),
        bed_file=cwl.File()
    ),
    outputs=dict(out=cwl.File(glob='gc_content.txt')),
    docker='images.sbgenomics.com/filip_tubic/ubuntu1604pysam'
)
def gc_content(bam_file, bed_file):
    """Calculate GC content."""

    bam_file = bam_file['path']
    bed_file = bed_file['path']
    bam = pysam.AlignmentFile(bam_file, 'rb')
    with open('gc_content.txt', 'w') as out:
        with open(bed_file) as bf:
            for line in bf:
                line_parts = line.strip().split()
                chr = line_parts[0]
                start = int(line_parts[1])
                end = int(line_parts[2])
                read_data = bam.fetch(chr, start, end)
                total_bases = 0
                gc_bases = 0
                for read in read_data:
                    seq = read.query_sequence
                    total_bases += len(seq)
                    gc_bases += len([x for x in seq if x == 'C' or x == 'G'])
                if total_bases == 0:
                    gc_percent = 'No Reads'
                else:
                    gc_percent = '{0:.2f}%'.format(
                        float(gc_bases) / total_bases * 100
                    )
                out.write('{0}\t{1}\n'.format(line.strip(), gc_percent))


gc_content().dump('gc_content.cwl')
