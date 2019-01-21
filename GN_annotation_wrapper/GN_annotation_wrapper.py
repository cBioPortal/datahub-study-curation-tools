import os
import sys
import subprocess
import filecmp
import csv
import shutil
import argparse

def split(infile,anfile,unanfile):
	comment_lines = str()
	ann_data = str()
	unann_data = str()

	with open(infile,'r') as file:
		for line in file:
			if line.startswith('#'):
				comment_lines += line
			elif line.upper().startswith('HUGO_SYMBOL'):
				header = line
				cols = line.split("\t")
				hgvsp_index = cols.index("HGVSp_Short")
			else:
				data = line.split("\t")
				if data[hgvsp_index] == "":
					unann_data += line
				else:
					ann_data += line
						
	if unann_data != "":
		ann_file = open(anfile,"w")
		ann_file.write(comment_lines)
		ann_file.write(header)
		ann_file.write(ann_data)
		ann_file.close()
		unann_file = open(unanfile,"w")
		unann_file.write(comment_lines)
		unann_file.write(header)
		unann_file.write(unann_data)
		unann_file.close()

def get_header(file):
	with open(file, "r") as header_source:
		for line in header_source:
			if not line.startswith("#"):
				header = line
				break
	return header
		
def merge(file1,output_file):
	out_file = open(output_file,"a+")
	if os.path.getsize(output_file) == 0:
		with open(file1,'r') as file:
			for line in file:
				out_file.write(line)
	else:				
		header1 = get_header(file1)
		header2 = get_header(output_file)
	
		if header1 != header2:
			print("Can't merge the files since the MAF columns are not the same")
			sys.exit()

		else:
			with open(file1,'r') as file:
				for line in file:
					if line.startswith('#') or line.upper().startswith('HUGO_SYMBOL') :
						continue
					else:
						out_file.write(line)
	out_file.close()

def rearrange_mafcols(ref_file,unan_file):
	ref_header = get_header(ref_file)
	unan_header = get_header(unan_file)

	if ref_header != unan_header:
		file_name = unan_file[0:-4]
		outfile = open(file_name+"_rearranged.txt",'w')
		with open(unan_file,'r') as infile:
			fieldnames = ref_header.split('\t')
			writer = csv.DictWriter(outfile,fieldnames = fieldnames, delimiter = '\t')
			writer.writeheader()
			file_reader = csv.DictReader(filter(lambda row: row[0]!='#',infile), delimiter = '\t')
			for row in file_reader:
				writer.writerow(row)
		outfile.close()
		os.remove(unan_file)
		shutil.copyfile(file_name+"_rearranged.txt",unan_file)
		os.remove(file_name+"_rearranged.txt")

def call_gn(annotator_jar,infile,GNout,isoform):
	subprocess.call(['java','-jar',annotator_jarpath,'--filename',infile,'--output-filename',GNout,'--isoform-override',isoform])

def annotation_wrapper(annotator_jar,infile,outfile,GNout,isoform):
	anfile = "an.txt"
	unanfile = "unan.txt"
	split(infile,anfile,unanfile)
	
	if os.path.exists(anfile):
		os.remove(infile)
		merge(anfile,outfile)
		os.remove(anfile)
		call_gn(annotator_jar,unanfile,GNout,isoform)
		#rearrange_mafcols(outfile,GNout)
	else:
		merge(GNout,outfile)
		os.remove(GNout)
	
def main():
	# get command line arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', '--input_maf', required = True, help = 'Input maf file name',type = str)
	parser.add_argument('-a', '--annotator_jar_path', required = True, help = 'Path to the annotator jar file.  An example can be found in "/data/curation/annotation/annotator/annotationPipeline-1.0.0.jar" on dashi-dev',type = str)
	parser.add_argument('-i', '--isoform', required = True, help = 'uniprot/mskcc annotation isoform.',type = str)
	parser.add_argument('-o', '--output_filename', required = True, help = 'Output maf file name',type = str)
	args = parser.parse_args()

	infile = args.input_maf
	outfile = args.output_filename
	isoform = args.isoform
	annotator_jar = args.annotator_jar_path
	GNout = "GN_unannotated_"+isoform+".txt"
	unan_file = "unan.txt"
	
	#STEP1: Call GN
	print("Annotation Round : 1")
	call_gn(annotator_jar,infile,GNout,isoform)
	
	if os.path.exists(GNout):
		#STEP2: Read the GN annotated file and split and re annotate the unannotated part
		print("Annotation Round : 2")
		annotation_wrapper(annotator_jar,GNout,outfile,GNout,isoform)
	
		#STEP3: Check if re annotation improves the annotation status of the maf
		for i in range(10): 
			if os.path.exists(unan_file):
				if filecmp.cmp(GNout,unan_file):
					os.remove(unan_file)
					break
				else:
					os.remove(unan_file)
					print("Annotation Round : "+str(i+3))
					annotation_wrapper(annotator_jar,GNout,outfile,GNout,isoform)
					
		merge(GNout,outfile)
		os.remove(GNout)
	else:
		print("The input file could not be annotated.")
		
if __name__ == '__main__':
	main()
	

	