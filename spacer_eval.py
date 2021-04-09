from src.main import spacer_eval

# An existing folder to put outputs in
# Can be relative or absolute
# Ex. 'C:\\Users\\Me\\Downloads', '../../Downloads'
output_path = './'

# Genbank Accession number
# The downloaded genbank files are cached locally in the assets folder, and will only
# be downloaded from NCBI if not present
# Ex. ["CP001509.3"]
genbank_ids = []

# Email: only used for NCBI API calls, be polite!
email = ''

# List of spacers to evaluate for off-target matches
# Each must be 32 basepairs in length, invalid lengths will be filtered out
# Ex: =['AAAAATAAAAACAAAAAATAAAACAAAAAGTT', 'GGCGATAAAAACATTTAATAAAACAAAAAGTT']
spacers = []

# Do not modify, this calls the function when run with 'python spacer_eval.py'
if __name__ == "__main__":
	spacer_eval({"output_path": output_path, "genbank_ids": genbank_ids, "email": email, "spacers": spacers})
