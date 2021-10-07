import sys

def header(h1, h2, f1_att, f2_att):

	h1h2 = ""

	if(f2_att==1):
		h1h2 = h1.replace("\n","\t") + h2.partition("\t")[2]
	elif(f2_att==2):
		h1h2 = h1.replace("\n","\t") + h2.partition("\t")[2].partition("\t")[2]

	return h1h2


def blank(token, att):

	fr_blank = ""
	for i in range(token-att+1):
		if (i==token-att):
			fr_blank += "NA"
		else:
			fr_blank += "NA\t"

	return fr_blank	
	
def main():

	f1_att = int(raw_input("How many column header in file 1: "))
	f2_att = int(raw_input("How many column header in file 2: "))

	if(f1_att<f2_att):
		f1_att, f2_att = f2_att, f1_att
		fr2 = open (sys.argv[1], "r")	
		fr1 = open (sys.argv[2], "r")		
	else:
		fr1 = open (sys.argv[1], "r")
		fr2 = open (sys.argv[2], "r")

	fw  = open ("output2.txt", "w") 

	fw.write(fr1.readline().replace('\n','\t')+fr2.readline().partition("\t")[2])

	cna_f1 = [] # Declares an empty list for cna of each gene
	cna_f2 = [] # Declares an empty list for cna of each gene
	cna_f1f2 = []
	token1 = 0 # count how many "\t" in a row in f1
	token2 =0 # count how many "\t" in a row in f2

	for line1 in fr1.readlines():
		token1 = line1.count("\t")

		if(line1.endswith("\n")):
			cna_f1.append(line1)
		else:
			cna_f1.append(line1+"\n")

	for line2 in fr2.readlines():
		
		token2 = line2.count("\t")
		cna_f2.append(line2)	

	for x in cna_f1:
		for y in cna_f2:
			if x.partition("\t")[0] == y.partition("\t")[0]:
				cna_f1f2.append(x.replace('\n','\t') + y.partition("\t")[2].replace("\n","")) # put the common gene cna data in array list
				cna_f2.remove(y)
				break
		else:
			cna_f1f2.append(x.replace("\n","\t") + blank(token2, f2_att)) # put the exclusive gene cna data of data1 in array list

	for z in cna_f2:

		gene = ""
		temp = z.split("\t")

		for x in xrange(f2_att):
			if(f2_att < f1_att):
				gene = str(temp[x])+"\t"+"\t"
			elif(f2_att == f1_att):
				gene += str(temp[x])+"\t"

		cna_f1f2.append( gene + blank(token1, f1_att) + "\t"+ z.partition("\t")[2].replace("\n","")) # put the exclusive gene cna data of data2 in array list

	for w in cna_f1f2:
		fw.write(w + "\n")			

	fr1.close()
	fr2.close()
	fw.close()


if __name__ == "__main__":
	main()



