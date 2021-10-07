import sys

id_filename = sys.argv[1]
data_filename = sys.argv[2]
samples = set()

with open(id_filename) as f:
	for line in f:
		samples.add(line.strip())

with open(data_filename) as f:
	first = True
	for line in f:
		if line.startswith('#'):
			print line.strip()
			continue
		if first:
			first = False
			print line.replace('\n','')
			continue
		data = line.split('\t')
		for item in data:
			if item in samples:
				print line.replace('\n','')