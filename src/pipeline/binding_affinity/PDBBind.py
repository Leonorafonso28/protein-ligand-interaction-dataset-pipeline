import re
import pandas as pd

#Directories
pdbbind_index = "/Users/leonorafonso/Downloads/index/INDEX_general_PL.2020R1.lst"
filtered_df = pd.read_excel("/Users/leonorafonso/Documents/Work/MoreiraLab/Project/Files/filtered_df.xlsx")

#Regular expression pattern used to parse each valid line from the PDBBind index file. The PDBBind file does not have a fixed column delimiter.
#Splitting by spaces alone would not correctly extract each field.
#This regex captures five key parts of each line: 1:PDB ID, 2:Resolution, 3:Year, 4:Binding Data, 5:Referance or ligand inf
#Without this pattern all affinity and ligand information to be misaligned or lost

records = []
pattern = re.compile(r'^(?P<pdb>\S+)\s+(?P<res>\S+)\s+(?P<year>\d{4})\s+(?P<data>[Kk][id]=[^\s]+)\s+//\s+(?P<ref>.+)$')

for line in open(pdbbind_index, encoding='utf-8'):
    line = line.strip()
    #Skipt empty lines and comment lines 
    if not line or line.startswith("#"):
        continue

    #Try to match the line against the predefined regular expression pattern
    m = pattern.match(line)
    if not m:
        continue

    #Extract fields from regex capture groups
    pdb_id = m.group("pdb")
    resolution = m.group("res")
    year = m.group("year")
    binding_data = m.group("data")
    reference = m.group("ref")

    #Split binding data into type and value
    aff_type, aff_value = binding_data.split("=")
    match_val = re.match(r"([<>=]*)([\d\.]+)([munp]?M)", aff_value)

    if match_val:
        sign, num, unit = match_val.groups()
        try:
            value = float(num)
            #Convert the unit to molar (M)
            unit = unit.lower()
            factor = {"mm": 1e-3, "um": 1e-6, "nm": 1e-9, "pm": 1e-12, "m": 1}[unit]
            value_m = value * factor
        except Exception:
            value_m = None
    else:
        value_m = None

    #Store extracted and converted data into a structured record
    records.append({
        "PDB_ID": pdb_id,
        "Resolution": resolution,
        "Year": year,
        "Type": aff_type,
        "Affinity_M": value_m,
        "Reference_Ligand": reference
    })

df = pd.DataFrame(records)
print(f"{len(df)} valid data from PDBBind")

#Convert to nM
df["Affinity_nM"] = df["Affinity_M"] * 1e9

print(df.head(10))
print("Affiniy values (nm):", df["Affinity_nM"].describe())

#Merge com filtered_df.xlsx
merged = filtered_df.merge(df, left_on="PDB ID", right_on="PDB_ID", how="left")
print(f"\n Matches find: {merged['Affinity_M'].notna().sum()} com afinidades")
print(merged.head())

merged.to_csv("filtered_df_with_PDBbind.csv", index=False)
print("File saved as filtered_df_with_PDBbind.csv'")
