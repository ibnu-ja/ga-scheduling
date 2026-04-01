import numpy as np
from fitness import calculate_fitness
from database import get_special_ids

def test_hc1_violations():
    special_ids = get_special_ids()
    upacara_id = special_ids['upacara'] if special_ids['upacara'] is not None else 1
    bersih_id = special_ids['bersih'] if special_ids['bersih'] is not None else 2
    istirahat_id = special_ids['istirahat'] if special_ids['istirahat'] is not None else 3
    
    # Correct genes
    correct_genes = np.array([
        [upacara_id, -1, 1, 1, 1], # Senin jam 1
        [bersih_id, -1, 1, 1, 4], # Kamis jam 1
        [istirahat_id, -1, 1, 5, 2], # Selasa jam 5
        [istirahat_id, -1, 1, 8, 3], # Rabu jam 8
    ], dtype=int)
    
    # Wrong genes
    wrong_genes = np.array([
        [999, -1, 1, 1, 1], # Senin jam 1, not Upacara
        [bersih_id, 10, 1, 1, 4], # Kamis jam 1, has guru
        [999, -1, 1, 5, 2], # Selasa jam 5, not Istirahat
        [istirahat_id, 11, 1, 8, 3], # Rabu jam 8, has guru
    ], dtype=int)
    
    # Bypass SC-2b for test
    special_ids_no_pns = special_ids.copy()
    special_ids_no_pns['pns_p3k'] = set()

    fitness_correct = calculate_fitness(correct_genes, special_ids_no_pns)
    fitness_wrong = calculate_fitness(wrong_genes, special_ids_no_pns)
    
    print(f"Fitness Correct: {fitness_correct}")
    print(f"Fitness Wrong: {fitness_wrong}")
    
    assert fitness_correct == 1.0, f"Expected 1.0, got {fitness_correct}"
    assert fitness_wrong < 1.0, f"Expected < 1.0, got {fitness_wrong}"
    print("HC-1 Test Passed!")

def test_hc3_hc4_violations():
    special_ids = get_special_ids()
    co_teaching_ids = list(special_ids['co_teaching'])
    pns_ids = list(special_ids['pns_p3k'])
    
    # Find a non-coteaching mapel_id
    non_ct_id = 999
    while non_ct_id in co_teaching_ids or non_ct_id in [special_ids['upacara'], special_ids['bersih'], special_ids['istirahat']]:
        non_ct_id -= 1

    # HC-3: Kelas Conflict
    hc3_viol = np.array([
        [non_ct_id, -1, 1, 2, 2],
        [non_ct_id, -1, 1, 2, 2],
    ], dtype=int)
    
    # HC-4: Guru Conflict
    hc4_viol = np.array([
        [non_ct_id, 1, 1, 3, 3],
        [non_ct_id, 1, 2, 3, 3],
    ], dtype=int)
    
    # Co-teaching: OK
    if co_teaching_ids:
        ct_id = co_teaching_ids[0]
        coteaching_ok = np.array([
            [ct_id, -1, 1, 4, 4],
            [ct_id, -1, 1, 4, 4],
        ], dtype=int)
        f_ct_ok = calculate_fitness(coteaching_ok, special_ids)
        # Note: f_ct_ok might be < 1.0 due to SC-2b (PNS hours)
        # But it should be higher than a hard violation if it was one.
    else:
        f_ct_ok = 1.0

    # Bypass SC-2b for test
    special_ids_no_pns = special_ids.copy()
    special_ids_no_pns['pns_p3k'] = set()

    f3 = calculate_fitness(hc3_viol, special_ids_no_pns)
    f4 = calculate_fitness(hc4_viol, special_ids_no_pns)
    
    print(f"Fitness HC3 Viol: {f3}")
    print(f"Fitness HC4 Viol: {f4}")
    
    assert f3 < 1.0
    assert f4 < 1.0
    print("HC-3/HC-4 Test Passed!")

if __name__ == "__main__":
    test_hc1_violations()
    test_hc3_hc4_violations()
