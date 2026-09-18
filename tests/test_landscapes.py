import numpy as np

from sim.config import LandscapeClass, SimConfig
from sim.landscapes import generate_library, generate_triplet, load_landscape, sha256_file


def test_triplet_shares_exact_value_multiset(small_config: SimConfig) -> None:
    maps = generate_triplet(1, small_config)
    smooth = np.sort(maps[LandscapeClass.smooth].ravel())
    rough = np.sort(maps[LandscapeClass.rough].ravel())
    random = np.sort(maps[LandscapeClass.random].ravel())
    np.testing.assert_allclose(smooth, rough)
    np.testing.assert_allclose(smooth, random)
    assert maps[LandscapeClass.smooth].min() >= 0.0
    assert maps[LandscapeClass.smooth].max() <= 1.0


def test_triplet_means_follow_density_targets(small_config: SimConfig) -> None:
    for triplet_id in range(small_config.n_triplets):
        maps = generate_triplet(triplet_id, small_config)
        mean = float(maps[LandscapeClass.smooth].mean())
        assert abs(mean - small_config.density_means[triplet_id]) < 0.08


def test_generation_is_seeded(small_config: SimConfig) -> None:
    a = generate_triplet(0, small_config)[LandscapeClass.smooth]
    b = generate_triplet(0, small_config)[LandscapeClass.smooth]
    np.testing.assert_array_equal(a, b)


def test_library_checksums_stable(small_config: SimConfig) -> None:
    first = generate_library(small_config, force=True)
    second = generate_library(small_config, force=True)
    assert first["files"] == second["files"]
    path = small_config.data_dir / "triplet0_smooth.npz"
    assert sha256_file(path) == first["files"]["triplet0_smooth.npz"]
    loaded = load_landscape(0, LandscapeClass.smooth, small_config)
    assert loaded.shape == (small_config.grid, small_config.grid)
