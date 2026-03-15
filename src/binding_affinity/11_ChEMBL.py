import pandas as pd
from chembl_webresource_client.new_client import new_client
from collections import defaultdict

bioactivities_api = new_client.activity

#Directories
filtered_df = pd.read_excel("data/interim/filtered_df.xlsx")
uniprot_data = pd.read_csv("data/interim/UniProt/uniprot_mappings.csv")

#Concatenate uniprot data
# Normalizing colunas
uniprot_data.rename(columns={"pdb_id": "PDB ID", "label_chain": "Chain ID", "uniprot_id": "UniProt_ID"}, inplace=True)

filtered_df["PDB ID"] = filtered_df["PDB ID"].str.strip().str.upper()
uniprot_data["PDB ID"] = uniprot_data["PDB ID"].str.strip().str.upper()

filtered_df["Chain ID"] = filtered_df["Chain ID"].str.strip().str.upper()
uniprot_data["Chain ID"] = uniprot_data["Chain ID"].str.strip().str.upper()

merged_data = pd.merge(uniprot_data, filtered_df, on=["PDB ID", "Chain ID"], how="inner")
merged_data = merged_data.drop_duplicates()

merged_data = pd.merge(uniprot_data, filtered_df, on=["PDB ID", "Chain ID"], how="inner")
merged_data = merged_data.drop_duplicates()

# Ligand_mapping with ChEMBL
def get_molecule_chembl_ids(row):
    inchikey = row.get("InChIKey")
    smiles = row.get("SMILES")

    try:
        if pd.notna(inchikey):
            results = list(new_client.molecule.filter(molecule_structures__standard_inchi_key=inchikey))
            if results:
                return [r["molecule_chembl_id"] for r in results]
    except Exception as e:
        print(f"Error retrieving by InChIKey {inchikey}: {e}")

    try:
        if pd.notna(smiles):
            results = list(new_client.molecule.filter(molecule_structures__canonical_smiles=smiles))
            if results:
                return [r["molecule_chembl_id"] for r in results]
    except Exception as e:
        print(f"Error retrieving by SMILES {smiles}: {e}")

    return []

merged_data["molecule_chembl_id"] = merged_data.apply(get_molecule_chembl_ids, axis=1)
merged_data = merged_data.explode("molecule_chembl_id")

merged_data.to_csv("data/binding_affinity/merged_data_filtered_ChEMBL_ID.csv", index=False)
print(uniprot_data.columns.tolist())

uniprot_data.columns = [c.lower() for c in uniprot_data.columns]
merged_data.columns = [c.lower() for c in merged_data.columns]

#UniProt accession to get targets in ChEMBL
merged_data["uniprot_acc"] = merged_data["uniprot_id"].map(
    dict(zip(uniprot_data["uniprot_id"], uniprot_data["uniprot_acc"]))
)

#Use 'UniProt_acc' to get target_chembl_id
uniprot_accs = merged_data["uniprot_acc"].dropna().unique().tolist()

target_data = new_client.target.filter(
    target_components__accession__in=uniprot_accs
).only("target_chembl_id", "target_components")

# Mapping UniProt_acc → target_chembl_id
target_dict = defaultdict(list)
for entry in target_data:
    for component in entry['target_components']:
        acc = component.get('accession')
        if acc:
            target_dict[acc].append(entry['target_chembl_id'])

# Map to merged_data
merged_data["target_chembl_ids"] = merged_data["uniprot_acc"].map(target_dict)
merged_data = merged_data.explode("target_chembl_ids")
merged_data = merged_data.rename(columns={"target_chembl_ids": "target_chembl_id"})

print({k: v for k, v in list(target_dict.items())[:10]})

# Get activities from ChEMBL
act=[]

# Loop in each UniProt_ID and molecule_chembl_id
for index, row in merged_data.iterrows():
    target_id = row['target_chembl_id']
    molecule_id = row['molecule_chembl_id']
    
    if pd.notna(target_id) and pd.notna(molecule_id):
        try:
            res = bioactivities_api.filter(
                target_chembl_id=target_id,
                molecule_chembl_id=molecule_id
            ).only(
                'target_type', 'molecule_chembl_id', 'target_chembl_id',
                'type', 'pchembl_value', 'standard_value',
                'standard_units', 'standard_relation',
                'target_organism', 'assay_type'
            )
            act.extend(res)
        except Exception as e:
            print(f"Error in target {target_id} and molecule {molecule_id}: {e}")

# Saving the data
act_df = pd.DataFrame(act)
act_df = act_df.drop_duplicates()
act_df.to_csv("data/binding_affinity/activities_data.csv", index=False)

# Get target_type for each target_chembl_id
target_ids = act_df["target_chembl_id"].dropna().unique().tolist()

target_types = new_client.target.filter(target_chembl_id__in=target_ids).only(
    "target_chembl_id", "target_type"
)

target_type_map = {entry["target_chembl_id"]: entry["target_type"] for entry in target_types}

# Map to act_df
act_df["target_type"] = act_df["target_chembl_id"].map(target_type_map)

ChEMBL_activities = pd.merge(
    act_df,
    merged_data,
    left_on=['molecule_chembl_id', 'target_chembl_id'],
    right_on=['molecule_chembl_id', 'target_chembl_id'],
    how='inner'
)

merged_cols = merged_data.columns.tolist()

new_cols = [col for col in ChEMBL_activities.columns if col not in merged_cols]
ChEMBL_activities = ChEMBL_activities[merged_cols + new_cols]
ChEMBL_activities = ChEMBL_activities.drop_duplicates()
ChEMBL_activities.to_csv("data/binding_affinity/ChEMBL_activities.csv", index=False)

# Check which uniprots did not match any target chembl id
uniprot_with_chembl = set(target_dict.keys())
uniprot_in_df = set(merged_data["UniProt_ID"].dropna().unique())
uniprot_missing = uniprot_in_df - uniprot_with_chembl
print("UniProt IDs with no target_chembl_id:", uniprot_missing)

# Check which INCHIKEYs did not have matches
inchikeys_with_chembl = merged_data.groupby("INCHIKEY")["molecule_chembl_id"].apply(lambda x: all(pd.isna(x)))
missing_ligands = inchikeys_with_chembl[inchikeys_with_chembl].index.tolist()
print("INCHIKEYs with no molecule_chembl_id:", missing_ligands)