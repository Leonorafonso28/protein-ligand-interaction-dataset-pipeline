# **Protein-Ligand Interaction Dataset Pipeline**
Comprehensive pipeline for curating and integrating protein-ligand structural and bioactivity data from PDB, PDBe, UniProt, BindingDB, PDBBind, and ChEMBL. Processes CIF/FASTA files, filters ligands, computes atomic interactions, generates embeddings (ESM-2 for proteins, Mordred for ligands), and produces a unified dataset suitable for machine learning modeling of protein-ligand interactions.

## **Folder structure**

```text
protein-ligand-interaction-dataset-pipeline
│
├── README.md                     # Project overview
├── LICENSE                       # License file
├── .gitignore                    # Files/folders to ignore in git
├── requirements.txt              # Python dependencies
├── environment.yml               # Conda environment (optional)
├── Dockerfile                    # Docker configuration for reproducibility
│
├── configs/                      # Configuration files
│
├── data/                         # Project data
│   ├── raw/                      # Original, unmodified data
│   │   ├── pdb_ids/              # PDB ID list files
│   │   ├── cif_structures/       # Original CIF files
│   │   ├── ligand_databases/     # Components CIF files, ligand info
│   │   ├── excluded_ligands_datasets/ # Lists of ligands to exclude
│   │   └── binding_affinity_external_dataset/ # External datasets like PDBBind
│   │
│   ├── interim/                  # Intermediate outputs from pipeline steps
│   │   ├── split_cif_chains/
│   │   ├── fasta_sequences/
│   │   ├── filtered_datasets/    # Filtered CSV/XLSX outputs
│   │   └── interaction_details_csv_cif/
│   │
│   └── processed/
│       ├── binary_interactions_csv/
│       ├── esm_embeddings/                # Final ML-ready datasets
│       └── mordred_descriptors/
│
├── src/                          # Source code
│   ├── pipeline/                 # Stepwise scripts organized by pipeline steps
│   │   ├── 01_pdb_download/
│   │   ├── 02_cif_protein_chain_and_ligand_extraction/
│   │   ├── 03_filtering/
│   │   ├── 04_expand_filter_merge_ligand_data/
│   │   ├── 05_filter_cif_fasta_by_ligands/
│   │   ├── 06_interaction/
│   │   ├── 07_embeddings_ESM2/
│   │   ├── uniprot_mappings/
│   │   ├── covalent_bonds/
│   │   └── binding_affinity/
│   │
│   ├── features/                    # Code for embeddings/descriptors
│   │   ├── esm_embeddings.py
│   │   └── mordred_descriptors.py                 
│   │
│   └── config.py                 # Global configuration and parameters
│
├── pipelines/                    # Scripts to run full or partial pipelines
│   ├── run_dataset_pipeline.py
│   ├── run_embedding_pipeline.py
│   └── run_full_pipeline.py                  
│
├── models/                       # Saved ML models (future work)
│
├── notebooks/                     # Jupyter notebooks for EDA or visualization
│   ├── exploratory_analysis.ipynb
│   └── dataset_statistics.ipynb
│
├── results/                       # Generated results like tables and figures
│   ├── tables/
│   └── figures/
│
├── tests/                         # Unit or integration tests (optional)
│
└── docs/                          # Additional documentation
    ├── pipeline_overview.md
    ├── dataset_description.md
    └── methodology.md
```
## **Pipeline / Workflow**

![Workflow Diagram](results/figures/workflow_diagram.png)
<img src="results/figures/workflow_diagram.png" alt="Workflow Diagram" width="600"/>

### **Detailed Workflow**

- **Step 01 – PDB Download**
Input: rcsb_pdb_ids_03_09.txt
Download CIF files from RCSB PDB API
Extract metadata: experimental method, resolution, organism
Filter only proteins with experimental structures
Output files: cif/, protein_data.csv, chain_organisms.csv
- **Step 02 – CIF Protein Chains and Ligand Extraction**
Parse ATOM (protein) and HETATM (ligand) records
Convert modified residues to standard amino acids
Discard ambiguous chains (SEC, PYL, UNK)
Extract sequences, positions, chain IDs
Output files: ligands_per_chain.csv, split_cif_chains/, fasta_sequences/
- **Step 03 – Ligand & Chain Filtering**
Remove non-biological, short, or invalid chains
Remove PDB duplicates
Apply chemical and functional rules for ligands
Merge exclusion lists (BioLiP2, manual, Q-BioLip)
Deduplicate by SMILES, InChI, InChIKey
Output files: ligands_per_chain_filtered.csv, chain_organisms_filtered.csv, protein_data_filtered.csv, ligands_filtered.csv, ligands_excluded.csv, ligands_excluded_conflicts.csv
- **Step 04 – Protein-Ligand Expansion**
Expand ligands per chain
Remove covalent links using covalent_links.csv
Merge protein and ligand metadata
Output file: filtered_df.xlsx
- **Step 05 – Filter CIFs & FASTA Sequences by Ligands**
Retain only chains and ligands present in filtered_df.xlsx
Output files: split_cif_chains_filtered/, fasta_sequences_filtered/
- **Step 06 – Atomic Interaction Calculation and Binary Interaction Conversion**
Extract atom coordinates, ignore hydrogens
Separate protein and ligand atoms
Compute atom-atom distances (<4.5 Å → interacting)
Encode interactions as 1 (interacting) or 0 (non-interacting)
Output files: interaction_details_csv_cif/
Output files: binary_interactions_csv/
- **Step 07 – Protein & Ligand Embeddings**
Proteins: ESM-2 embeddings (1280-dim per residue)
Ligands: Mordred descriptors (1600 features)
Verify FASTA sequences match CSV
Output file: interaction_dataset.hdf5
- **Step 08 – Bioactivity Integration**
Merge experimental affinities from BindingDB, PDBBind, ChEMBL
Standardize units, compute pChEMBL
Output files: filtered_df_with_BindingDB.csv, filtered_df_with_PDBBind.csv, ChEMBL_activities.csv

