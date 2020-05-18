import json
import time
import os
from pathlib import Path

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import SeqIO

from src.genbank import retrieve_annotation, get_genes
from src.finder import get_target_region_for_gene, get_candidates_for_region, remove_offtarget_matches
from src.outputs import make_spacer_gen_output, make_eval_outputs
from src.bowtie import find_offtargets


def spacer_gen(args):
	print("Starting spacer search...")
	email = args['email']
	outputPath = args['outputPath']
	genbankId = args['genbankId']
	startPct = args['startPct']
	endPct = args['endPct']
	spacersPerRegion = args['spacersPerRegion']
	target_gene_names = args['target_gene_names']

	target_gene_names = [s.lower() for s in args['coding']['genesList']]
	genbank_info = retrieve_annotation(genbankId, email)
	all_genes = get_genes(genbank_info)
	target_genes = [gene for gene in all_genes if gene['name'].lower() in target_gene_names]
	genome = Seq(genbank_info['GBSeq_sequence'])

	for gene in target_genes:
		start = time.perf_counter()
		print(gene['name'])
		print(f"Finding crRNA for \"{gene['name']}\"")
		[start_mark, end_mark] = get_target_region_for_gene(gene, startPct, endPct)
		
		candidates = get_candidates_for_region(genome, start_mark, end_mark, gene['name'])
		# print("{} candidates with a valid PAM targeting the gene".format(len(candidates)))
		# candidates = filter_non_unique_fingerprints(candidates)
		# print("{} candidates with a unique fingerprint".format(len(candidates)))
		
		candidates = remove_offtarget_matches(genbankId, gene['name'], candidates, spacersPerRegion)
		gene['candidates'] = candidates
		if len(candidates) > spacersPerRegion:
			gene['candidates'] = candidates[:spacersPerRegion]

		elapsed_time = round(time.perf_counter() - start, 2)
		print(f"Identified {len(candidates)} spacers for {gene['name']} in {elapsed_time}")
	make_spacer_gen_output(target_genes, os.path.join(outputPath, 'spacer_gen_output'))
	print("done")

def spacer_eval(args):
	genbankId = args['genbankId']
	outputPath = args['outputPath']
	email = args['email']
	user_spacers = args['spacers']

	genbank_info = retrieve_annotation(genbankId, email)
	all_genes = get_genes(genbank_info)
	genome = Seq(genbank_info['GBSeq_sequence'])
	
	spacers = [s for s in user_spacers if len(s) == 32]
	print(f"Starting evaluation for {len(spacers)} valid spacers...")
	spacer_batch = []
	for (index, spacer) in enumerate(spacers):
		flexible_seq = spacer[:]
		for i in range(5, 32, 6):
			flexible_seq = flexible_seq[:i] + 'N' + flexible_seq[i+1:]
		spacer_record = SeqRecord(Seq(flexible_seq), id=f'spacer_{index+1}', description=genbankId)  # use 'description' to store ref_genome info
		spacer_batch.append(spacer_record)

	# Write the batch of candidate sequences to a fasta for bowtie2 to use
	fasta_name = 'offtarget-check.fasta'
	root_dir = Path(__file__).parent.parent
	fasta_name = os.path.join(root_dir, 'assets', 'bowtie', genbankId, fasta_name)
	with open(fasta_name, 'w') as targets_file:
		SeqIO.write(spacer_batch, targets_file, 'fasta')

	output_location = find_offtargets(genbankId, fasta_name)
	make_eval_outputs(spacer_batch, output_location, genome, outputPath)

	os.remove(fasta_name)
	os.remove(output_location)