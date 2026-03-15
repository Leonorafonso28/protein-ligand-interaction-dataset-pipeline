import glob
import os

#Directories
file_input="data/raw/pdb_ids/pdb/ids"
file_output="data/raw/pdb_ids/rcsb_pdb_ids_03_09.txt"
archives=glob.glob(os.path.join(file_input, "*.txt"))

pdb_ids=[]

#Read every file 
for archive in archives:
    with open (archive, "r", encoding="utf-8") as f:
        cont=f.read()
        
        #Line break with each comma 
        ids=[x.strip() for x in cont.split(",")]
        pdb_ids.extend(ids)

#Saving PDB IDs in one document
with open(file_output, "w", encoding="utf-8") as f:
    f.write("\n".join(pdb_ids))

with open(file_output, "r", encoding="utf-8") as f:
    all_ids=f.read()

print(f"Number of entries of the final document: {len(all_ids)}")