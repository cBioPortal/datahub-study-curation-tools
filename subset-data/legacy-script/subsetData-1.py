import sys 

fr1 = open (sys.argv[1], "r") # id list 
fr2 = open (sys.argv[2], "r") # data
fw = open (sys.argv[2][:-4]+"_subset.txt", "w")

def MAF_SEG_FUSION(identifier, data, filename):
	
	id_list = data_line = data_col = []
	id_list = [line.strip()for line in identifier.readlines()]

	if filename == 'data_mutations_extended.txt' :
		firstline = data.readline()	

		if firstline.startswith('#'): # for impact data
			fw.write(data.readline())
		else:
			fw.write(firstline)

		data_line = [line for line in data.readlines()]	

		for line1 in id_list:
			for line2 in data_line:
				data_col = line2.split("\t")
				if line1 == data_col[15].strip():
					fw.write(line2)

	elif 'seg' in filename :
		fw.write(data.readline())

		data_line = [line for line in data.readlines()]	

		for line1 in id_list:
			for line2 in data_line:
				if line1.strip() in line2:
					fw.write(line2)	

	elif 'fusions' in filename :
		fw.write(data.readline())

		data_line = [line for line in data.readlines()]	

		for line1 in id_list:
			for line2 in data_line:
				data_col = line2.split("\t")
				if line1 == data_col[3].strip():
					fw.write(line2)	

	elif 'timeline' in filename :
		fw.write(data.readline())

		data_line = [line for line in data.readlines()]	

		for line1 in id_list:
			for line2 in data_line:
				data_col = line2.split("\t")
				if line1[:9] == data_col[0]:
					fw.write(line2)	
			
def CNA(identifier, data):

	id_list = query_id_list = subset_num = temp = []
	
	new_header = "Hugo_symbol"+"\t" 

	id_list = data.readline().split("\t")
	query_id_list = [line for line in identifier.readlines()]

	for i, j in enumerate(id_list):
		for line in query_id_list:
			if j.strip()==line.strip():
				subset_num.append(i)
				new_header=new_header+j.strip()+"\t"

	fw.write(new_header+"\n")
				
	for x in data.readlines():
		temp = x.split("\t")
		fw.write(temp[0]+"\t"+'\t'.join(map(lambda x:  temp[x], subset_num))+"\n")

def clinical(identifier, data):

	id_list = clin_line = []
	fw.write(data.readline())

	id_list = [x.strip() for x in identifier.readlines()]

	clin_line = [y for y in data.readlines()]

	for line1 in id_list:
		for line2 in clin_line:
			if line1 in line2:
				fw.write(line2)

def main():

	if "mutations" in sys.argv[2] or  "seg" in sys.argv[2] or "fusions" in sys.argv[2] or 'data_timeline' in sys.argv[2]:
		MAF_SEG_FUSION(identifier=fr1, data=fr2, filename = sys.argv[2])

	elif sys.argv[2] == "data_CNA.txt":
		CNA(identifier=fr1, data=fr2)

	elif 'data_clinical' in sys.argv[2]:
		clinical(identifier=fr1, data=fr2)	

if __name__ == "__main__":
	main()


fr1.close()
fr2.close()
fw.close()  