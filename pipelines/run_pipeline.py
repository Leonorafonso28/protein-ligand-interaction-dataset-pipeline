import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PIPELINE_STEPS = [
    "src/pipeline/01_pdb_download",
    "src/pipeline/02_cif_protein_chain_and_ligand_extraction",
    "src/pipeline/03_filtering",
    "src/pipeline/04_covalent_bonds",
    "src/pipeline/05_expand_filter_merge_ligand_dataset",
    "src/pipeline/06_filter_cif_fasta_by_ligands",
    "src/pipeline/07_uniprot_mappings",
]

def run_step(step_path: str):

    step_dir = PROJECT_ROOT / step_path
    scripts = sorted(step_dir.glob("*.py"))

    if not scripts:
        logger.warning(f"No scripts found in {step_dir}")
        return

    for script in scripts:
        logger.info(f"Running {script}")

        subprocess.run(
            ["python", str(script)],
            check=True
        )

def run_pipeline():

    logger.info("Starting full dataset pipeline")

    for step in PIPELINE_STEPS:
        run_step(step)

    logger.info("Pipeline completed successfully")


if __name__ == "__main__":
    run_pipeline()