import requests
import pandas as pd

API = "https://www.ebi.ac.uk/pdbe/graph-api/mappings/uniprot/{}"

def fetch_uniprot_mappings(pdb_id: str):
    url = API.format(pdb_id.lower())
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def parse_mapping_json(pdb_id: str, data):
    key = next(iter(data.keys()))
    if "UniProt" not in data[key]:
        return pd.DataFrame()

    rows = []
    for acc, payload in data[key]["UniProt"].items():
        if acc.startswith("PRO_"):  # excluir proteoforms
            continue
        uniprot_id = payload.get("identifier") or payload.get("name")
        for m in payload.get("mappings", []):
            rows.append({
                "pdb_id": pdb_id.upper(),
                "label_chain": m["struct_asym_id"], 
                "uniprot_acc": acc,
                "uniprot_id": uniprot_id,
                "unp_start": m["unp_start"],
                "unp_end": m["unp_end"],
                "pdb_start": m["pdb_start"],
                "pdb_end": m["pdb_end"],
            })
    return pd.DataFrame(rows)

with open("data/raw/pdb_ids/rcsb_pdb_ids_03_09.txt") as f:
    pdb_ids = [line.strip() for line in f if line.strip()]

all_rows = []
for pid in pdb_ids:
    try:
        data = fetch_uniprot_mappings(pid)
        df = parse_mapping_json(pid, data)
        if not df.empty:
            all_rows.append(df)
    except Exception as e:
        print(f"[WARN] {pid}: {e}")

final_df = pd.concat(all_rows, ignore_index=True).drop_duplicates()

# Guardar num CSV
final_df.to_csv("data/interim/UniProt/uniprot_mappings.csv", index=False)