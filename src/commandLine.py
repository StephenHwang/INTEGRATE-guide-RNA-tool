import argparse


'''
code adapted from program.py provided by David Bernick created on 08/20/2011
'''

class CommandLine() :
    '''
    Handle the command line, usage and help requests.

    if inCL is None:
        myCli = CommandLine()
    else :
        myCli = CommandLine(inCL)

    '''

    def __init__(self, inOpts=None) :
        '''
        Implement a parser to interpret the command line argv string using argparse.
        '''
        self.parser = argparse.ArgumentParser(description = 'Program prolog - a brief description of what this thing does',
                                             epilog = 'Program epilog - some other stuff you feel compelled to say',
                                             add_help = True,
                                             prefix_chars = '-',
                                             usage = '%(prog)s [options] -option1[default] <input >output'
                                             )

        # example from lab 5
        self.parser.add_argument('-lG', '--longestGene', action = 'store', nargs='?', const=True, default=False, help='longest Gene in an ORF')
        self.parser.add_argument('-mG', '--minGene', type=int, choices= (0,100,200,300,500,1000), default=100, action = 'store', help='minimum Gene length')
        self.parser.add_argument('-s', '--start', action = 'append', default = ['ATG'],nargs='?', help='start Codon') #allows multiple list options
        self.parser.add_argument('-t', '--stop', action = 'append', default = ['TAG','TGA','TAA'],nargs='?', help='stop Codon') #allows multiple list options


        # basic parameters

        # output_path  # TODO: make output stdout
        self.parser.add_argument('-mG', '--spacers_per_region', type=int, default=100, action = 'store', help='TODO')
        self.parser.add_argument('-t', '--GC_requirement', action = 'append', default = [35, 65], nargs='?', help='Sequences will be filtered against this list of restriction enzymes.')
        self.parser.add_argument('-mG', '--overlap_regions', type=str, choices= ('avoid', 'allowed', 'forbidden'), default='avoid', action = 'store', help='minimum Gene length')


        self.parser.add_argument('-mG', '--genmark_ids', type=str, default='CP001509.3', action = 'store', help='Default is Escherichia coli BL21(DE3)') # TODO make required

        # required
        self.parser.add_argument('-mG', '--email', type=str, action = 'store', help='Default is Escherichia coli BL21(DE3)') # TODO make required
        self.parser.add_argument('-t', '--genbank_files', action = 'append', default = [], nargs='?', help='Sequences will be filtered against this list of restriction enzymes.')
        self.parser.add_argument('-t', '--genome_fasta_files', action = 'append', default = [], nargs='?', help='Sequences will be filtered against this list of restriction enzymes.')

        self.parser.add_argument('-mG', '--region_type', type=str, choices= ('coding', 'noncoding', 'custom'), default='coding', action = 'store', help='minimum Gene length')
        self.parser.add_argument('-mG', '--start_pct', type=int, default=10, action = 'store', help='TODO')
        self.parser.add_argument('-mG', '--end_pct', type=int, default=50, action = 'store', help='TODO')

        # TODO: change this to a flag
        self.parser.add_argument('-mG', '--coding_spacer_direction', type=str, choices= ('N_to_C', 'C_to_N'), default='N_to_C', action = 'store', help='minimum Gene length')

        target_locus_tag_ids
        noncoding_boundary
        nonessential_only

        # if
        custom_regions_csv = ''
        custom_sequences = []


        # requried


        # advanced parameters
        self.parser.add_argument('-mG', '--mismatch_threshold', type=int, default=4, action = 'store', help='TODO')
        self.parser.add_argument('-mG', '--minimum_intergenic_region_length', type=int, default=50, action = 'store', help='TODO')
        self.parser.add_argument('-mG', '--spacer_length', type=int, default=32, action = 'store', help='length of spacers')
        self.parser.add_argument('-mG', '--PAM_SEQ', type=str, default='CC', action = 'store', help='PAM sequence used to identify candidates') # TODO not currently tolerate 'N'
        self.parser.add_argument('-mG', '--INTEGRATION_SITE_DISTANCE', type=int, default=49, action = 'store', help='Distance from the spacer at which transposition occurs. Roughly 49bp downstream for INTEGRATE. This is used to identify spacers that target specific genomic regions.')
        self.parser.add_argument('-lG', '--offset', action = 'store', nargs='?', const=False, default=True, help="Controls taking into account INTEGRATION_SITE_DISTANCE when searching for candidates. True limits spacer candidates to spacers that will direct integration into the target search window. False will return spacers whose 3' ends are within the target search window")

        self.parser.add_argument('-lG', '--flex_base', action = 'store', nargs='?', const=False, default=True, help='True to convert flexible bases to N for bowtie elements. Change to false to turn off.')
        self.parser.add_argument('-mG', '--flex_spacing', type=int, default=6, action = 'store', help='Number of bases per 1 flexible base. Default 6')
        self.parser.add_argument('-lG', '--allow_gaps', action = 'store', nargs='?', const=True, default=False, help='True to allow gaps for bowtie alignment between spacer and off-targets')
        self.parser.add_argument('-t', '--restriction_enzymes', action = 'append', default = [], nargs='?', help='Sequences will be filtered against this list of restriction enzymes.')
        # Ex. restriction_enzymes = ['SalI', 'BsaI', 'BamHI', 'AvrII', 'HindIII']
        self.parser.add_argument('-mG', '--homopolymer_length', type=int, default=5, action = 'store', help='length of consecutive bp to count as a homopolymer for filtering.')

        # assorted
        self.parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')



        if inOpts is None :
            self.args = self.parser.parse_args()
        else :
            self.args = self.parser.parse_args(inOpts)







