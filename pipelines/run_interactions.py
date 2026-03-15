import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INTERACTIONS_STEPS = [
    "src/interactions/",
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

    logger.info("Starting full interactions pipeline")

    for step in INTERACTIONS_STEPS:
        run_step(step)

    logger.info("Interactions pipeline completed successfully")


if __name__ == "__main__":
    run_pipeline()