import subprocess
import sys
import tempfile
import os
import csv
import time
import multiprocessing
from collections import Counter
from pathlib import Path

from Bio import SeqIO, SeqUtils
from Bio.SeqRecord import SeqRecord
from simplesam import Reader as samReader

from bowtie import find_offtargets
from advanced_parameters import PAM_SEQ, INTEGRATION_SITE_DISTANCE, SPACER_LENGTH, flex_base, flex_spacing, offset

def candidates_for_seq(seq, descriptor, GC_requirement=[0,100]):
	candidates = []
	i=0
	while i < len(seq):
		nextPAM = seq[i:].find(PAM_SEQ)
		if nextPAM == -1 or (i+nextPAM+len(PAM_SEQ)+SPACER_LENGTH) > len(seq):
			i += 10000000
			break

		targetSeq = seq[i+nextPAM+len(PAM_SEQ):i+nextPAM+len(PAM_SEQ)+SPACER_LENGTH]
		GC_content = SeqUtils.GC(targetSeq)
		if GC_content < GC_requirement[0] or GC_content > GC_requirement[1]:
			i += nextPAM + 1
			continue
		name = descriptor + str(i+nextPAM+len(PAM_SEQ))

		target = SeqRecord(targetSeq, id=name, name=name, description=name)
		candidate = {'name': target.id, 'seqrec': target, 'location': i+nextPAM+len(PAM_SEQ)}
		candidates.append(candidate)
		i += nextPAM + 1
	return candidates

def get_target_region_for_gene(gene, start_pct, end_pct):
	# Calculate the target region of a gene by pct of the coding region, from N to C
	gene_length = gene['end'] - gene['start']

	fifty_pct_mark = gene['start'] + int(gene_length/2)
	if gene['direction'] == 'fw':
		start_mark = gene['start'] + int(gene_length*start_pct/100)
		end_mark = gene['start'] + int(gene_length*end_pct/100)
	else:
		start_mark = gene['start'] + int(gene_length*(100-end_pct)/100)
		end_mark = gene['start'] + int(gene_length*(100-start_pct)/100)
	return [start_mark, end_mark]

def get_candidates_for_region(genome, start_mark, end_mark, name, GC_requirement):
	genome_seq = genome

	if offset:
		search_offset = len(PAM_SEQ) + SPACER_LENGTH + INTEGRATION_SITE_DISTANCE
	else:
		search_offset = len(PAM_SEQ) + SPACER_LENGTH

	fw_search_seq = genome_seq[max(0,start_mark-search_offset):end_mark-search_offset + len(PAM_SEQ) + SPACER_LENGTH]
	rv_search_seq = genome_seq[start_mark+INTEGRATION_SITE_DISTANCE:end_mark+search_offset].reverse_complement()
	candidates = candidates_for_seq(fw_search_seq, name+'--fw', GC_requirement)
	for c in candidates:
		# the initial "location" here is the location in the search sequence, needs to be
		# placed in the genome location
		c['location'] = start_mark - search_offset + c['location'] + 1
	rv_candidates = candidates_for_seq(rv_search_seq, name+'--rv', GC_requirement)
	for c in rv_candidates:
		# move back additional spacer length for the reverse oriented spacers
		c['location'] = end_mark + search_offset - c['location'] +1
	candidates.extend(rv_candidates)

	for candidate in candidates:
		if 'fw' in candidate['name']:
			# for fw strand inserts, the fingerprint is downstream
			fp_start = candidate['location'] + SPACER_LENGTH + INTEGRATION_SITE_DISTANCE - 20
			fp_end = candidate['location'] + SPACER_LENGTH + INTEGRATION_SITE_DISTANCE
			fp_seq = genome_seq[fp_start:fp_end]
		else:
			# for rv strand inserts, the fingerprint is upstream
			fp_start = candidate['location'] - SPACER_LENGTH - INTEGRATION_SITE_DISTANCE
			fp_end = candidate['location'] - SPACER_LENGTH - INTEGRATION_SITE_DISTANCE + 20
			fp_seq = genome_seq[fp_start:fp_end].reverse_complement()
		name = candidate['name']
		candidate['fp_seq'] = SeqRecord(fp_seq, id=name, name=name, description=name)
	genome_both_ways = genome.upper()+genome.reverse_complement().upper()
	unique_candidates = [c for c in candidates if genome_both_ways.count(c["seqrec"].seq) == 1]
	return unique_candidates


def order_candidates_for_region(candidates, region, coding_spacer_direction):
	is_fwd_strand_and_NtoC = coding_spacer_direction == 'N_to_C' and region['direction'] == 'fw'
	is_rv_strand_and_CtoN = coding_spacer_direction == 'C_to_N' and region['direction'] == 'rv'

	if is_fwd_strand_and_NtoC or is_rv_strand_and_CtoN:
		reverse = False
	else:
		reverse = True
	# The lambda sort functions is to sort by the target site location instead of the spacer location
	return sorted(candidates,key=(lambda c: c['location'] + INTEGRATION_SITE_DISTANCE if 'fw' in c['name'] else (c['location'] - INTEGRATION_SITE_DISTANCE)), reverse=reverse)

def candidate_overlaps(candidate, overlap_regions):
	loc = candidate['location']
	end_loc = loc+SPACER_LENGTH
	start_overlaps_matches = any([loc > m[0] and loc < m[1] for m in overlap_regions])
	end_overlaps_matches = any([end_loc > m[0] and end_loc < m[1] for m in overlap_regions])
	return start_overlaps_matches or end_overlaps_matches

def choose_next_offtarget_batch(remaining_candidates, matches, overlapping_spacers, batch_size):
	if overlapping_spacers == 'allowed':
		return remaining_candidates[:batch_size]

	# Return a batch of up to 10 candidates to test for off-target activity
	existing_spacer_areas = [[m['location'], m['location']+SPACER_LENGTH] for m in matches]

	# First try and search for spacers that also wouldn't overlap with each other, to minimize
	# unnecessary slow offtarget searches
	to_check = []
	optimistically_avoid = []
	for c in remaining_candidates:
		overlaps = candidate_overlaps(c, existing_spacer_areas.copy() + optimistically_avoid)
		if not overlaps:
			to_check.append(c)
			optimistically_avoid.append([c['location'], c['location']+SPACER_LENGTH])
		if len(to_check) >= batch_size:
			return to_check[:batch_size]

	# Search for other potentially non-overlapping spacers that could still conflict with each other
	# These will be filtered aftwards if necessary
	for c in remaining_candidates:
		if c not in to_check:
			overlaps = candidate_overlaps(c, existing_spacer_areas.copy() + optimistically_avoid)
			if overlaps:
				to_check.append(c)
			if len(to_check) >= batch_size:
				return to_check[:batch_size]

	# If still not enough and overlapping isn't forbidden, start using overlapping candidates
	if len(to_check) < batch_size and overlapping_spacers != 'forbidden':
		to_check.extend([c for c in remaining_candidates if c not in to_check])

	return to_check[:batch_size]


def remove_offtarget_matches(genbank_id, name, candidates, minMatches, overlapping_spacers, check_all=False):
	no_offtargets = []
	untested = candidates.copy()
	while len(no_offtargets) < minMatches and len(untested) > 0:
		print(f"Testing candidates for off-target activity against {genbank_id}... {len(untested)} candidates remain")
		# Use 10 as the batch size to check for bowtie off-target matches
		test_candidates = choose_next_offtarget_batch(untested, no_offtargets, overlapping_spacers, len(untested) if check_all else 10)
		# Get the candidate sequences to use, and
		# make every 6th bp an N to allow for ambiguous matches
		match_seqs = [c['seqrec'].upper() for c in test_candidates]
		if flex_base:
			for seq in match_seqs:
				flexible_seq = seq.seq[:]
				for i in range(flex_spacing-1, SPACER_LENGTH, flex_spacing):
					flexible_seq = flexible_seq[:i] + 'N' + flexible_seq[i+1:]
				seq.seq = flexible_seq

		# Write the batch of candidate sequences to a fasta for bowtie2 to use
		fasta_name = name+'-candidates.fasta'
		root_dir = Path(__file__).parent.parent
		fasta_name = os.path.join(root_dir, 'assets', 'bowtie', genbank_id, fasta_name)

		os.makedirs( os.path.join(root_dir, 'assets', 'bowtie', genbank_id), exist_ok=True)

		with open(fasta_name, 'w') as targets_file:
			SeqIO.write(match_seqs, targets_file, 'fasta')

		output_location = find_offtargets(genbank_id, fasta_name)

		filtered_candidates = []
		sam_reads = []
		with open(output_location, 'r') as sam_file:
			reader = samReader(sam_file)
			sam_reads = [r for r in reader]

		for c in test_candidates:
			reads = [r for r in sam_reads if r.safename == c['name']]
			if len(reads) <= 1:
				no_offtargets.append(c)
			untested.remove(c)

		os.remove(fasta_name)
		os.remove(output_location)
		# return once at least minMatches are found without off-targets
		if len(no_offtargets) >= minMatches and not check_all:
			return no_offtargets[:minMatches]
	return no_offtargets
