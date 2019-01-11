input_maf = open("maf_output.mskcc.txt", "r")
output_maf_failed = open("maf_output_failed.mskcc.txt", "w")
output_maf_success = open("maf_output_success.mskcc.txt", "w")

# found index of variant type and protein change
header_line = input_maf.readline()
headers = header_line.rstrip().split("\t")
variant_type_index = -1
hgvsp_short_index = -1
count = 0
for header_item in headers:
	if header_item.lower() == "variant_classification":
		variant_type_index = count
	elif header_item.upper() == "HGVSP_SHORT":
		hgvsp_short_index = count
	count += 1

# writing to output files
output_maf_success.write(header_line)
output_maf_failed.write(header_line)

filters = [
	"targeted_region",
	"splice_region",
	"frame_shift_del",
   	"frame_shift_ins",
   	"missense_mutation",
   	"missense",
   	"in_frame_del",
   	"inframe_del",
   	"in_frame_del",
   	"inframe_ins",
   	"nonsense",
   	"nonsense_mutation",
   	"nonstop_mutation",
   	"splice_site"
 ]

for line in input_maf:
	values = line.split("\t")
	if values[hgvsp_short_index] == "" and values[variant_type_index].lower() in filters:
		output_maf_failed.write(line)
	else:
		output_maf_success.write(line) 
