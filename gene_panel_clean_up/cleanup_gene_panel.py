#! /usr/bin/env python

#
# Copyright (c) 2018 Memorial Sloan Kettering Cancer Center.
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, WITHOUT EVEN THE IMPLIED WARRANTY OF
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.  The software and
# documentation provided hereunder is on an "as is" basis, and
# Memorial Sloan Kettering Cancer Center
# has no obligations to provide maintenance, support,
# updates, enhancements or modifications.  In no event shall
# Memorial Sloan Kettering Cancer Center
# be liable to any party for direct, indirect, special,
# incidental or consequential damages, including lost profits, arising
# out of the use of this software and its documentation, even if
# Memorial Sloan Kettering Cancer Center
# has been advised of the possibility of such damage.
#
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import division
import sys
import os
import argparse
import math

PANEL_FILE_GENE_LIST_FIELD_NAME = "gene_list:"

def main():

	parser = argparse.ArgumentParser()
	parser.add_argument('-p','--input-gene-panel-folder', action = 'store', dest = 'input_gene_panel_folder', required = True, help = 'Gene Panel folder')	
	parser.add_argument('-m','--input-gene-mapping-file', action = 'store', dest = 'input_gene_mapping_file', required = True, help = 'Gene Mapping')		
	parser.add_argument('-o','--output-gene-panel-folder', action = 'store', dest = 'output_gene_panel_folder', required = True, help = 'Output Folder for Updated Panels')		
	args = parser.parse_args()

	_genePanelFolder = args.input_gene_panel_folder
	_geneMappingFile = args.input_gene_mapping_file
	_outputPanelFolder = args.output_gene_panel_folder

	_geneMapping = {}
	# convert gene mapping file into a dictionary
	with open(_geneMappingFile, 'r') as _geneMappingFile:
		for _line in _geneMappingFile:
			_items = _line.rstrip("\n").rstrip('\r').split('\t')
			_geneMapping[_items[0]] = _items[1]

	for _panelFileName in os.listdir(_genePanelFolder):
		_outputPanelFile = open(_outputPanelFolder + "/" + _panelFileName,'w')
		with open(_genePanelFolder + "/" + _panelFileName ,'r') as _panelFile:
			for _line in _panelFile:
				if _line.startswith(PANEL_FILE_GENE_LIST_FIELD_NAME):
					_geneStr = _line.split(":")[1].strip()
					_panelGenes = _geneStr.split('\t')
					_updatedPanelGenes = []
					for _panelGene in _panelGenes:
						if _geneMapping.has_key(_panelGene):
							_updatedPanelGenes.append(_geneMapping[_panelGene])
						else: 
							_updatedPanelGenes.append(_panelGene)
					_outputPanelFile.write(PANEL_FILE_GENE_LIST_FIELD_NAME + " " + '\t'.join(_updatedPanelGenes))
				else:
					_outputPanelFile.write(_line)

		

if __name__ == '__main__':
	main()