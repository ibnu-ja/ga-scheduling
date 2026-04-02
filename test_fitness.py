import numpy as np
from fitness import calculate_fitness
from database import get_special_ids

def get_test_special_ids():
    """Provides a safe set of special IDs for testing, fetching from DB if available."""
    try:
        special_ids = get_special_ids()
        # Ensure mandatory fields exist for tests
        if special_ids.get('upacara') is None: special_ids['upacara'] = 1
        if special_ids.get('bersih') is None: special_ids['bersih'] = 2
        if special_ids.get('istirahat') is None: special_ids['istirahat'] = 3
        if not special_ids.get('co_teaching'): special_ids['co_teaching'] = {101, 102}
        return special_ids
    except:
        return {
            'upacara': 1,
            'bersih': 2,
            'istirahat': 3,
            'co_teaching': {101, 102},
            'pns_p3k': set()
        }

def test_hc1_violations():
    print("Running HC-1 Test...")
    special_ids = get_test_special_ids()
    upacara_id = special_ids['upacara']
    bersih_id = special_ids['bersih']
    istirahat_id = special_ids['istirahat']
    
    # Correct genes (0 violations)
    correct_genes = np.array([
        [upacara_id, -1, 1, 1, 1], # Senin jam 1
        [bersih_id, -1, 1, 1, 4],  # Kamis jam 1
        [istirahat_id, -1, 1, 5, 2], # Selasa jam 5
        [istirahat_id, -1, 1, 8, 3], # Rabu jam 8
        [-1, -1, 1, 7, 5],           # Jumat jam 7 (empty)
        [-1, -1, 1, 8, 5],           # Jumat jam 8 (empty)
    ], dtype=int)
    
    # Wrong genes (6 violations)
    wrong_genes = np.array([
        [999, -1, 1, 1, 1], # Senin jam 1, not Upacara
        [bersih_id, 10, 1, 1, 4], # Kamis jam 1, has guru
        [999, -1, 1, 5, 2], # Selasa jam 5, not Istirahat
        [istirahat_id, 11, 1, 8, 3], # Rabu jam 8, has guru
        [istirahat_id, -1, 1, 8, 5], # Jumat jam 8, NO Istirahat allowed here now
        [999, -1, 1, 7, 5], # Jumat jam 7, must be empty
    ], dtype=int)
    
    # Bypass other constraints for pure HC-1 test
    clean_ids = special_ids.copy()
    clean_ids['pns_p3k'] = set()

    fitness_correct = calculate_fitness(correct_genes, clean_ids)
    fitness_wrong = calculate_fitness(wrong_genes, clean_ids)
    
    assert fitness_correct == 1.0, f"Expected 1.0, got {fitness_correct}"
    assert fitness_wrong < 1.0, f"Expected < 1.0, got {fitness_wrong}"
    print("HC-1 Test Passed!")

def test_hc3_co_teaching():
    print("Running HC-3 Co-teaching Test...")
    special_ids = get_test_special_ids()
    co_ids = list(special_ids['co_teaching'])
    ct_id = co_ids[0]
    
    # Non-co-teaching ID
    reg_id = 999
    while reg_id in special_ids['co_teaching'] or reg_id in [special_ids['upacara'], special_ids['bersih'], special_ids['istirahat']]:
        reg_id -= 1

    # 1. OK: Same co-teaching subject, different teachers
    ok_genes = np.array([
        [ct_id, 1, 1, 2, 2],
        [ct_id, 2, 1, 2, 2],
    ], dtype=int)
    
    # 2. VIOLATION: Different co-teaching subjects
    if len(co_ids) > 1:
        ct_id2 = co_ids[1]
        viol_diff_ct = np.array([
            [ct_id, 1, 1, 2, 2],
            [ct_id2, 2, 1, 2, 2],
        ], dtype=int)
    else:
        viol_diff_ct = None

    # 3. VIOLATION: One regular, one co-teaching
    viol_mixed = np.array([
        [reg_id, 1, 1, 2, 2],
        [ct_id, 2, 1, 2, 2],
    ], dtype=int)

    clean_ids = special_ids.copy()
    clean_ids['pns_p3k'] = set()

    assert calculate_fitness(ok_genes, clean_ids) == 1.0
    if viol_diff_ct is not None:
        assert calculate_fitness(viol_diff_ct, clean_ids) < 1.0
    assert calculate_fitness(viol_mixed, clean_ids) < 1.0
    print("HC-3 Test Passed!")

def test_sc2_continuity():
    print("Running SC-2 Continuity Test...")
    special_ids = get_test_special_ids()
    reg_id = 50
    
    # 1. OK: Contiguous block
    ok_block = np.array([
        [reg_id, 1, 1, 2, 1],
        [reg_id, 1, 1, 3, 1],
        [reg_id, 1, 1, 4, 1],
    ], dtype=int)
    
    # 2. OK: Split by Istirahat (slot 5)
    ok_istirahat = np.array([
        [reg_id, 1, 1, 4, 1],
        [reg_id, 1, 1, 6, 1],
    ], dtype=int)
    
    # 3. VIOLATION: Split by gap
    viol_gap = np.array([
        [reg_id, 1, 1, 2, 1],
        [reg_id, 1, 1, 4, 1],
    ], dtype=int)

    clean_ids = special_ids.copy()
    clean_ids['pns_p3k'] = set()

    assert calculate_fitness(ok_block, clean_ids) == 1.0
    assert calculate_fitness(ok_istirahat, clean_ids) == 1.0
    assert calculate_fitness(viol_gap, clean_ids) < 1.0
    print("SC-2 Test Passed!")

def test_sc3_guru_limits():
    print("Running SC-3 Guru Limits Test...")
    special_ids = get_test_special_ids()
    
    # 8 hours in a day (violation)
    bad_guru = np.array([[10, 100, 1, t, 1] for t in [2, 3, 4, 6, 7, 9, 10, 11]], dtype=int)
    
    clean_ids = special_ids.copy()
    clean_ids['pns_p3k'] = set()
    
    assert calculate_fitness(bad_guru, clean_ids) < 1.0
    print("SC-3 Test Passed!")

if __name__ == "__main__":
    test_hc1_violations()
    test_hc3_co_teaching()
    test_sc2_continuity()
    test_sc3_guru_limits()
    print("\nAll consolidated tests passed!")
