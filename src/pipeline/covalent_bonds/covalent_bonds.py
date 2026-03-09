import os
import pandas as pd

# Directories
cif_folder = "cif"
filtered_excel = "filtered_df.xlsx"
output_csv = "covalent_links.csv"

# Helper: is the mmCIF seq id numeric?
def _is_numeric_seq_id(val: str) -> bool:
    if val is None:
        return False
    val = val.strip()
    if val in (".", "?"):
        return False
    try:
        int(val)
        return True
    except ValueError:
        return False

def extract_covalent_protein_ligand_links(cif_path):
    """
    Parse _struct_conn entries from mmCIF, supporting:
      1) loop_ tables (many rows)
      2) single-record key–value blocks (no loop_)
    Keep only covalent (conn_type_id == 'covale') *protein–ligand* links,
    using label fields (ptnr*_label_*).
    """
    def _is_numeric_seq_id(val: str) -> bool:
        if val is None:
            return False
        val = val.strip()
        if val in (".", "?"):
            return False
        try:
            int(val)
            return True
        except ValueError:
            return False

    with open(cif_path, "r") as f:
        lines = [ln.rstrip("\n") for ln in f]

    results = []

    # handle loop_ form
    in_loop = False
    in_struct_conn_loop = False
    headers = []

    for ln in lines:
        s = ln.strip()
        if s.startswith("loop_"):
            in_loop = True
            in_struct_conn_loop = False
            headers = []
            continue

        if in_loop and s.startswith("_"):
            headers.append(s)
            if s.startswith("_struct_conn."):
                in_struct_conn_loop = True
            continue

        if in_loop and s and not s.startswith("_"):
            if in_struct_conn_loop and headers:
                parts = s.split()
                if len(parts) == len(headers):
                    rec = {h: v for h, v in zip(headers, parts)}
                    if rec.get("_struct_conn.conn_type_id", "").lower() == "covale":
                        p1_seq = rec.get("_struct_conn.ptnr1_label_seq_id", "")
                        p2_seq = rec.get("_struct_conn.ptnr2_label_seq_id", "")
                        p1_is_prot = _is_numeric_seq_id(p1_seq)
                        p2_is_prot = _is_numeric_seq_id(p2_seq)
                        if p1_is_prot != p2_is_prot:
                            if p1_is_prot:
                                prot = ("_struct_conn.ptnr1_label_asym_id",
                                        "_struct_conn.ptnr1_label_comp_id",
                                        "_struct_conn.ptnr1_label_seq_id",
                                        "_struct_conn.ptnr1_label_atom_id")
                                lig  = ("_struct_conn.ptnr2_label_asym_id",
                                        "_struct_conn.ptnr2_label_comp_id",
                                        "_struct_conn.ptnr2_label_seq_id",
                                        "_struct_conn.ptnr2_label_atom_id")
                            else:
                                prot = ("_struct_conn.ptnr2_label_asym_id",
                                        "_struct_conn.ptnr2_label_comp_id",
                                        "_struct_conn.ptnr2_label_seq_id",
                                        "_struct_conn.ptnr2_label_atom_id")
                                lig  = ("_struct_conn.ptnr1_label_asym_id",
                                        "_struct_conn.ptnr1_label_comp_id",
                                        "_struct_conn.ptnr1_label_seq_id",
                                        "_struct_conn.ptnr1_label_atom_id")

                            results.append({
                                "Prot_chain_label": rec.get(prot[0], ""),
                                "Prot_res_label_comp": rec.get(prot[1], ""),
                                "Prot_label_seq_id": rec.get(prot[2], ""),
                                "Prot_label_atom": rec.get(prot[3], ""),
                                "Lig_chain_label": rec.get(lig[0], ""),
                                "Lig_id_label_comp": rec.get(lig[1], ""),
                                "Lig_label_seq_id": rec.get(lig[2], ""),
                                "Lig_label_atom": rec.get(lig[3], ""),
                            })
            # keep reading until next loop_/headers reset

        # end of a loop when a new loop_ starts (handled above) or file ends

    # handle single-record key–value blocks (non-loop)
    # We scan contiguous runs of lines that start with "_struct_conn."
    rec = {}
    in_kv_block = False

    def flush_kv_record():
        nonlocal rec
        if not rec:
            return
        if rec.get("_struct_conn.conn_type_id", "").lower() != "covale":
            rec = {}
            return
        p1_seq = rec.get("_struct_conn.ptnr1_label_seq_id", "")
        p2_seq = rec.get("_struct_conn.ptnr2_label_seq_id", "")
        p1_is_prot = _is_numeric_seq_id(p1_seq)
        p2_is_prot = _is_numeric_seq_id(p2_seq)
        if p1_is_prot == p2_is_prot:
            rec = {}
            return

        if p1_is_prot:
            prot = ("_struct_conn.ptnr1_label_asym_id",
                    "_struct_conn.ptnr1_label_comp_id",
                    "_struct_conn.ptnr1_label_seq_id",
                    "_struct_conn.ptnr1_label_atom_id")
            lig  = ("_struct_conn.ptnr2_label_asym_id",
                    "_struct_conn.ptnr2_label_comp_id",
                    "_struct_conn.ptnr2_label_seq_id",
                    "_struct_conn.ptnr2_label_atom_id")
        else:
            prot = ("_struct_conn.ptnr2_label_asym_id",
                    "_struct_conn.ptnr2_label_comp_id",
                    "_struct_conn.ptnr2_label_seq_id",
                    "_struct_conn.ptnr2_label_atom_id")
            lig  = ("_struct_conn.ptnr1_label_asym_id",
                    "_struct_conn.ptnr1_label_comp_id",
                    "_struct_conn.ptnr1_label_seq_id",
                    "_struct_conn.ptnr1_label_atom_id")

        results.append({
            "Prot_chain_label": rec.get(prot[0], ""),
            "Prot_res_label_comp": rec.get(prot[1], ""),
            "Prot_label_seq_id": rec.get(prot[2], ""),
            "Prot_label_atom": rec.get(prot[3], ""),
            "Lig_chain_label": rec.get(lig[0], ""),
            "Lig_id_label_comp": rec.get(lig[1], ""),
            "Lig_label_seq_id": rec.get(lig[2], ""),
            "Lig_label_atom": rec.get(lig[3], ""),
        })
        rec = {}

    for ln in lines:
        s = ln.strip()
        if s.startswith("_struct_conn."):
            in_kv_block = True
            # split on whitespace: "_struct_conn.key   value"
            parts = s.split(maxsplit=1)
            key = parts[0]
            val = parts[1] if len(parts) > 1 else ""
            rec[key] = val
            continue

        # end of a kv block if we hit a blank, '#', 'loop_', or a different category
        if in_kv_block and (s == "" or s == "#" or s.startswith("loop_") or (s.startswith("_") and not s.startswith("_struct_conn."))):
            flush_kv_record()
            in_kv_block = False

    if in_kv_block:
        flush_kv_record()

    return results


# Collect all protein–ligand covalent links across CIFs
all_rows = []
for file in os.listdir(cif_folder):
    if not file.endswith(".cif"):
        continue
    cif_path = os.path.join(cif_folder, file)
    pdb_id = os.path.splitext(file)[0]

    bonds = extract_covalent_protein_ligand_links(cif_path)
    for b in bonds:
        all_rows.append({
            "PDB_ID": pdb_id,
            "Prot_chain": b["Prot_chain_label"],
            "Prot_res": b["Prot_res_label_comp"],
            "Prot_position": b["Prot_label_seq_id"],
            "Prot_atom": b["Prot_label_atom"],
            "Lig_id": b["Lig_id_label_comp"],
            "Lig_chain": b["Lig_chain_label"],
            "Lig_position": b["Lig_label_seq_id"],
            "Lig_atom": b["Lig_label_atom"],
        })

# Save CSV
df = pd.DataFrame(all_rows)
if not df.empty:
    df.to_csv(output_csv, index=False)
    print(f"CSV file saved in: {output_csv}")
else:
    print("No protein–ligand covalent links found.")