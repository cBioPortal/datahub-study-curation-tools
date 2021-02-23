from __future__ import division
import sys
import os
import argparse

def main():

	_ensembl_dict = {}
	_gene_info_dict = {}
	_main_dict = {}

	_outputF = open("complete-supp-main.txt", "w")

	with open("bare-main-supp.txt", "r") as _input_main_supp:
		_header = _input_main_supp.readline()
		for _line in _input_main_supp:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')
			_main_dict[_items[0]] = {
				"entrez_id": _items[0],
				"symbol": _items[1],
				"chromosome": "-",
				"cytoband": "-",
				"type": _items[2],
				"ensembl_gene_id": ""
			}
	_input_main_supp.close()

	# add locations
	with open("ncbi-download/gene_info.txt", "r") as _geneInfo:
		_header = _geneInfo.readline()
		for _line in _geneInfo:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')
			if _main_dict.has_key(_items[1]):
				_gene_info_dict[_items[1]] = {
					"entrez_id": _items[1],
					"chr": _items[6],
					"map_location": _items[7],
					"locus_tag": _items[3]
				}
	_geneInfo.close()

	# add ensembl ID
	with open("ncbi-download/gene2ensembl.txt", "r") as _gene2ensembl:
		_header = _gene2ensembl.readline()
		for _line in _gene2ensembl:
			_items = _line.rstrip("\r").rstrip("\n").split('\t')
			_ensembl_dict[_items[1]] = _items[2]
	_gene2ensembl.close()

	_outputF.write("entrez_id\tsymbol\tchromosome\tcytoband\ttype\tensembl_gene_id\n")
	for _main_gene_obj in _main_dict.values():
		_entrezID = _main_gene_obj["entrez_id"]
		if _gene_info_dict.has_key(_entrezID):
			if _gene_info_dict[_entrezID]["chr"] == "Un":
				_main_gene_obj["chromosome"] = "-" #handle speical chr value case
			else:
				_main_gene_obj["chromosome"] = _gene_info_dict[_entrezID]["chr"]
			_main_gene_obj["cytoband"] = _gene_info_dict[_entrezID]["map_location"]
		if _ensembl_dict.has_key(_entrezID):
			_main_gene_obj["ensembl_gene_id"] = _ensembl_dict[_entrezID]
		_outputF.write(
				_main_gene_obj["entrez_id"] + "\t" +
				_main_gene_obj["symbol"] + "\t" +
				_main_gene_obj["chromosome"] + "\t" +
				_main_gene_obj["cytoband"] + "\t" +
				_main_gene_obj["type"] + "\t" +
				_main_gene_obj["ensembl_gene_id"] + "\n"
			)


if __name__ == '__main__':
	main()