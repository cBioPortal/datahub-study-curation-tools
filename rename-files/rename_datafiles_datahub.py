import sys
import os

# Read the file with old to new name mapping - Save the data to data and meta dictionaries
# Update the data filename attribute inside the meta file
# Create a shell script to rename files. (we need the history to be preserved)
# Run the shell script on datahub

updated_filenames_list = open('new-data-filenames.txt', 'r')
studies_path = 'datahub/public'

#New filenames to a dictionary
data_filenames_dict = {}
meta_filenames_dict = {}
meta_data_filename_dict = {}

for line in updated_filenames_list:
    line = line.strip('\n').split('\t')
    data_filenames_dict[line[0]] = line[1]
    meta_filenames_dict[line[2]] = line[3]
    meta_data_filename_dict[line[2]] = line[1]

studies_list = os.listdir(studies_path)
if '.DS_Store' in studies_list:
    studies_list.remove('.DS_Store')

shell_commands = open('git-rename-files.sh','w')
    
for study in studies_list:
    shell_commands.write('cd '+studies_path+'/'+study+'\n')
    files_list = os.listdir(studies_path+'/'+study)
    for file in files_list:
        if file in data_filenames_dict:
            shell_commands.write('git mv '+file+' '+data_filenames_dict[file]+'\n')
        elif file in meta_filenames_dict:
            shell_commands.write('git mv '+file+' '+meta_filenames_dict[file]+'\n')
            
            if file in meta_data_filename_dict and os.path.exists(studies_path+'/'+study+'/'+file):
                updated_meta_file = ""
                with open(studies_path+'/'+study+'/'+file,'r') as meta:
                    for line in meta:
                        if line.startswith('data_filename'):
                            updated_meta_file += 'data_filename : '+meta_data_filename_dict[file]+'\n'
                        else:
                            updated_meta_file += line
                os.remove(studies_path+'/'+study+'/'+file)
                with open(studies_path+'/'+study+'/'+file,'w') as new_meta:
                    new_meta.write(updated_meta_file)
                            
    
    shell_commands.write('cd ../../../\n')
shell_commands.close()
                            
                            