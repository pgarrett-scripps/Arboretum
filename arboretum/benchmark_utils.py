import random
import numpy as np
from psm import PSM

AMINOACIDS = 'ARNDCEQGHILKMFPSTWYV'


def generate_random_psm(rng=None, np_rng=None):
    """Generate a single random PSM with realistic mass-spec parameters."""
    if rng is None:
        rng = random
    if np_rng is None:
        np_rng = np.random

    peptide_string = ''.join(rng.choice(AMINOACIDS) for _ in range(rng.randint(6, 30)))
    mz = float(np_rng.normal(1000, 250))
    return PSM(
        charge=rng.randint(1, 5),
        mz=mz,
        rt=rng.uniform(0, 5000),
        ook0=mz / 1000 + rng.uniform(-0.2, 0.2),
        data={'sequence': peptide_string}
    )


def generate_psm_dataset(n, seed=42):
    """Generate a reproducible list of n random PSMs."""
    rng = random.Random(seed)
    np_rng = np.random.RandomState(seed)
    return [generate_random_psm(rng=rng, np_rng=np_rng) for _ in range(n)]
