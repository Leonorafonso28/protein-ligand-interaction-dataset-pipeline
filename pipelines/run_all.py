import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

#Order of pipelines to run - can be modified to run specific pipelines or change order
PIPELINE_SCRIPTS = [
    "pipelines/run_pipeline.py",            #Dataset preparation
    "pipelines/run_interactions.py",        #Protein-ligand interactions
    "pipelines/run_features.py",            #Embeddings/descriptors
    "pipelines/run_binding_affinity.py",    #Binding affinity datasets
]

def run_script(script_path: str):
    script_full_path = PROJECT_ROOT / script_path
    logger.info(f"Running {script_full_path}")
    try:
        subprocess.run(
            ["python", str(script_full_path)],
            check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Script failed: {script_path}")
        raise e

def run_all():
    logger.info("Starting FULL pipeline (run_all.py)")
    for script in PIPELINE_SCRIPTS:
        run_script(script)
    logger.info("All pipelines completed successfully")

if __name__ == "__main__":
    run_all()