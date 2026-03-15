import pandas as pd
import numpy as np

#Directories
filtered_df = pd.read_excel("data/interim/filtered_df.xlsx")
uniprot_map = pd.read_csv("data/interim/UniProt/uniprot_mappings.csv")

#Reading BindingPDB file
bindingdb = pd.read_csv("data/binding_affinity/BindingDB_All.tsv", sep="\t", low_memory=False)
print(f"BindingDB: {len(bindingdb)} linhas")
print(bindingdb.columns)

#Exploring types of measurements, units, proteins and ligands
print("Measurements for binding affinity:", bindingdb["Measure"].value_counts())

print("\n--- Units of Measurement ---")
print("Units of measurement:", bindingdb["Units"].value_counts())

cols_protein = [c for c in bindingdb.columns if "Protein" in c or "Target" in c or "UniProt" in c]
print("Identifiers of proteins", cols_protein)

cols_ligand = [c for c in bindingdb.columns if "Ligand" in c or "SMILES" in c or "InChI" in c]
print("Identifiers of ligands", cols_ligand)

print("Measurements in Ki (nM):")
ki_df = bindingdb[
    (bindingdb["Measure"] == "Ki") &
    (bindingdb["Units"] == "nM")
]
print(f"Regists in Ki(nm): {len(ki_df)}")

#Functions to normalize the values of the measurements
def to_nM(value, unit):
    if pd.isna(value) or pd.isna(unit):
        return np.nan
    unit = str(unit).strip().lower()
    try:
        value = float(value)
    except:
        return np.nan
    #Every measure that could appear 
    factors = {
        "m": 1e9,      
        "mm": 1e6,     
        "um": 1e3,     
        "nm": 1,      
        "pm": 1e-3,    
    }
    for k, v in factors.items():
        if unit.endswith(k):
            return value * v
    return np.nan

def to_pChEMBL(affinity_nM):
    if pd.isna(affinity_nM) or affinity_nM <= 0:
        return np.nan
    molar = affinity_nM * 1e-9 #(-log10(M))
    return -np.log10(molar)

#Cleaning and normalizing BindingPDB file
bindingdb = bindingdb[bindingdb["Relation"] == "="]          
bindingdb = bindingdb[bindingdb["Value"] > 0]                
bindingdb["Affinity_nM"] = bindingdb.apply(lambda x: to_nM(x["Value"], x["Units"]), axis=1)

#Filtering measurements of interest
measures_of_interest = ["Ki", "Kd", "IC50", "EC50", "pKi", "pKd", "pIC50", "pChEMBL"]
bindingdb = bindingdb[bindingdb["Measure"].isin(measures_of_interest)].copy()

#Normalizing values of measurements 
bindingdb["Affinity_nM"] = bindingdb.apply(lambda x: to_nM(x["Value"], x["Units"]), axis=1)
bindingdb["pChEMBL_calc"] = bindingdb["Affinity_nM"].apply(to_pChEMBL)
print("Affinity values:", bindingdb["Affinity_nM"].describe())

#Merging results with filtered_df
#Try first with PDB ID
merged = filtered_df.merge(bindingdb, left_on="PDB ID", right_on="PDB ID(s) of Target Chain", how="left")

#Try second with UniProt 
if merged["Affinity_nM"].isna().all() and "UniProt ID" in filtered_df.columns:
    merged = filtered_df.merge(
        uniprot_map.merge(bindingdb, left_on="UniProt ID", right_on="UniProt (SwissProt) Primary ID of Target Chain", how="left"),
        on="UniProt ID",
        how="left"
    )

print(f"Matches find: {merged['Affinity_nM'].notna().sum()}")
print(merged.head())

#Save results
merged.to_csv("data/binding_affinity/filtered_df_with_BindingDB.csv", index=False)
print("File saved as data/binding_affinity/filtered_df_with_BindingDB.csv'")
