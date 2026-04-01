import numpy as np
from fitness import calculate_fitness


def test_hc1_violations():
    # Gene column indices: [mapel_id, guru_id, kelas_id, waktu_id, hari_id]
    # HC-1: Senin (1) jam 1 (1) -> Upacara (1), Guru -1
    # HC-1: Kamis (4) jam 1 (1) -> Bersih-bersih (2), Guru -1
    # HC-1: Jam 5 & 8 -> Istirahat (3), Guru -1

    # Correct genes (0 violations)
    correct_genes = np.array([
        [1, -1, 1, 1, 1],  # Senin jam 1
        [2, -1, 1, 1, 4],  # Kamis jam 1
        [3, -1, 1, 5, 2],  # Selasa jam 5
        [3, -1, 1, 8, 3],  # Rabu jam 8
    ])

    # Wrong genes (4 violations)
    wrong_genes = np.array([
        [4, -1, 1, 1, 1],  # Senin jam 1, not Upacara
        [2, 10, 1, 1, 4],  # Kamis jam 1, has guru
        [4, -1, 1, 5, 2],  # Selasa jam 5, not Istirahat
        [3, 11, 1, 8, 3],  # Rabu jam 8, has guru
    ])

    fitness_correct = calculate_fitness(correct_genes)
    fitness_wrong = calculate_fitness(wrong_genes)

    print(f"Fitness Correct: {fitness_correct}")
    print(f"Fitness Wrong: {fitness_wrong}")

    # p_total = v * 1000
    # for wrong_genes, p_total = 4 * 1000 = 4000
    # fitness = 1 / (1 + 4000) = 0.000249875...

    assert fitness_correct == 1.0, f"Expected 1.0, got {fitness_correct}"
    assert fitness_wrong < 0.001, f"Expected low fitness, got {fitness_wrong}"
    print("HC-1 Test Passed!")


def test_hc3_hc4_violations():
    # HC-3: Kelas Conflict (Exclude Co-Teaching 1, 2)
    # HC-4: Guru Conflict (Exclude g = -1)

    # Kelas 1 has two non-coteaching mapels (4, 5) at same time
    hc3_viol = np.array([
        [4, 1, 1, 2, 2],
        [5, 2, 1, 2, 2],
    ])

    # Guru 1 teaches two classes at same time
    hc4_viol = np.array([
        [4, 1, 1, 3, 3],
        [4, 1, 2, 3, 3],
    ])

    # Co-teaching: mapel 1, 2 allowed to be multiple in same class/time
    # Use gurus that are NOT PNS/P3K to avoid SC-2b penalty for this test
    coteaching_ok = np.array([
        [1, -1, 1, 4, 4],
        [1, -1, 1, 4, 4],
    ])

    f3 = calculate_fitness(hc3_viol)
    f4 = calculate_fitness(hc4_viol)
    f_ok = calculate_fitness(coteaching_ok)

    print(f"Fitness HC3 Viol: {f3}")
    print(f"Fitness HC4 Viol: {f4}")
    print(f"Fitness Co-teaching OK: {f_ok}")
    print(f"Coteaching OK matrix:\n{coteaching_ok}")

    # Let's see why f_ok is not 1.0.
    # Maybe because of SC-2b: PNS/P3K min hours penalty (each g_id counts as 24-1 = 23 penalty)
    # PNS ids 1 and 2 are in GURU_PNS_P3K_IDS.
    # Each will have 1 slot, so each has 23 penalty.
    # 2 * 23 * 500 = 23000.
    # 1 / (1 + 23000) = 4.347e-05.

    assert f3 < 1.0
    assert f4 < 1.0
    assert f_ok == 1.0
    print("HC-3/HC-4 Test Passed!")


if __name__ == "__main__":
    test_hc1_violations()
    test_hc3_hc4_violations()
