import numpy as np

# Gene column indices
MAPEL_IDX = 0
GURU_IDX = 1
KELAS_IDX = 2
WAKTU_IDX = 3
HARI_IDX = 4

def calculate_fitness(chromosome, special_ids=None):
    """
    chromosome: 2D NumPy array [gen, attributes]
    special_ids: (Optional) dict from database.get_special_ids()
    """
    if special_ids is None:
        try:
            from database import get_special_ids
            special_ids = get_special_ids()
        except ImportError:
            # Fallback for testing environments where database might not be available
            special_ids = {
                'upacara': 1,
                'bersih': 2,
                'istirahat': 3,
                'co_teaching': {1, 2},
                'pns_p3k': set()
            }

    upacara_id = special_ids.get('upacara')
    bersih_id = special_ids.get('bersih')
    istirahat_id = special_ids.get('istirahat')
    co_teaching_ids = special_ids.get('co_teaching', set())
    pns_p3k_ids = special_ids.get('pns_p3k', set())

    p_total = 0
    
    # Weights
    W_HARD = 1000
    W_SOFT = 500

    # HC-1: Fixed Time Slots
    hc1_v = 0
    # Senin (1) Jam 1: Upacara
    mask_senin_1 = (chromosome[:, HARI_IDX] == 1) & (chromosome[:, WAKTU_IDX] == 1)
    if np.any(mask_senin_1):
        hc1_v += np.sum((chromosome[mask_senin_1, MAPEL_IDX] != upacara_id) | (chromosome[mask_senin_1, GURU_IDX] != -1))
    
    # Kamis (4) Jam 1: Bersih-bersih
    mask_kamis_1 = (chromosome[:, HARI_IDX] == 4) & (chromosome[:, WAKTU_IDX] == 1)
    if np.any(mask_kamis_1):
        hc1_v += np.sum((chromosome[mask_kamis_1, MAPEL_IDX] != bersih_id) | (chromosome[mask_kamis_1, GURU_IDX] != -1))
    
    # Jam 5 Every Day: Istirahat
    mask_istirahat_5 = (chromosome[:, WAKTU_IDX] == 5)
    if np.any(mask_istirahat_5):
        hc1_v += np.sum((chromosome[mask_istirahat_5, MAPEL_IDX] != istirahat_id) | (chromosome[mask_istirahat_5, GURU_IDX] != -1))
    
    # Jam 8 Monday-Thursday: Istirahat
    mask_istirahat_8 = (chromosome[:, WAKTU_IDX] == 8) & (chromosome[:, HARI_IDX] != 5)
    if np.any(mask_istirahat_8):
        hc1_v += np.sum((chromosome[mask_istirahat_8, MAPEL_IDX] != istirahat_id) | (chromosome[mask_istirahat_8, GURU_IDX] != -1))
    
    # Friday Jam 7-11: Empty (m=-1, g=-1)
    mask_jumat_pulang = (chromosome[:, HARI_IDX] == 5) & (chromosome[:, WAKTU_IDX] >= 7)
    if np.any(mask_jumat_pulang):
        # Violation if ANY mapel or guru is NOT -1
        hc1_v += np.sum((chromosome[mask_jumat_pulang, MAPEL_IDX] != -1) | (chromosome[mask_jumat_pulang, GURU_IDX] != -1))
    
    p_total += hc1_v * W_HARD

    # HC-3: Kelas Conflict (Exclude Co-Teaching)
    # v3 = |{(k,t,h) | exists ci, cj, i!=j, ki=kj, ti=tj, hi=hj AND (mi not in Mco OR mj not in Mco)}|
    kth_combos, kth_inverse, kth_counts = np.unique(chromosome[:, [KELAS_IDX, WAKTU_IDX, HARI_IDX]], axis=0, return_inverse=True, return_counts=True)
    
    hc3_v = 0
    # Slots with more than one gene
    multi_gene_slots = np.where(kth_counts > 1)[0]
    
    for slot_idx in multi_gene_slots:
        # Get all genes in this slot
        slot_genes_mask = kth_inverse == slot_idx
        slot_mapels = chromosome[slot_genes_mask, MAPEL_IDX]
        
        # Check if ANY mapel in this slot is NOT co-teaching
        has_non_co = any(m not in co_teaching_ids for m in slot_mapels)
        
        if has_non_co:
            # Violation if there's a non-co-teaching mapel and count > 1
            # RENCANA PERUBAHAN: Gunakan (counts - 1) untuk penalti lebih berat
            hc3_v += (kth_counts[slot_idx] - 1)
        else:
            # ALL are co-teaching. Check if they have same mapel_id.
            unique_mapels = np.unique(slot_mapels)
            if len(unique_mapels) > 1:
                # Different co-teaching mapels in same slot
                hc3_v += (kth_counts[slot_idx] - 1)
    
    p_total += hc3_v * W_HARD

    # HC-4: Guru Conflict (Exclude g = -1)
    mask_with_guru = chromosome[:, GURU_IDX] != -1
    guru_genes = chromosome[mask_with_guru]
    if len(guru_genes) > 0:
        _, counts = np.unique(guru_genes[:, [GURU_IDX, WAKTU_IDX, HARI_IDX]], axis=0, return_counts=True)
        hc4_v = np.sum(counts - 1)
        p_total += hc4_v * W_HARD

    # SC-1: Mapel Distribution
    sc1_v = 0
    mask_regular = ~np.isin(chromosome[:, MAPEL_IDX], [upacara_id, bersih_id, istirahat_id])
    reg_genes = chromosome[mask_regular]
    
    if len(reg_genes) > 0:
        _, counts_mkh = np.unique(reg_genes[:, [MAPEL_IDX, KELAS_IDX, HARI_IDX]], axis=0, return_counts=True)
        sc1_v += np.sum(np.maximum(0, counts_mkh - 5))
        
        unique_mk, inverse_mk = np.unique(reg_genes[:, [MAPEL_IDX, KELAS_IDX]], axis=0, return_inverse=True)
        total_slots_mk = np.bincount(inverse_mk)
        mk_day = np.unique(np.column_stack((inverse_mk, reg_genes[:, HARI_IDX])), axis=0)
        actual_days_mk = np.bincount(mk_day[:, 0], minlength=len(unique_mk))
        
        min_days_mk = np.ceil(total_slots_mk / 5.0).astype(int)
        sc1_v += np.sum(np.maximum(0, min_days_mk - actual_days_mk))
    
    p_total += sc1_v * W_SOFT

    # SC-2: Subject Continuity (E - 1 logic)
    sc2_v = 0
    if len(reg_genes) > 0:
        # Map waktu to skip 5 and 8
        mapped_waktu = reg_genes[:, WAKTU_IDX].copy()
        mapped_waktu[reg_genes[:, WAKTU_IDX] > 5] -= 1
        mapped_waktu[reg_genes[:, WAKTU_IDX] > 8] -= 1
        
        sorted_indices = np.lexsort((mapped_waktu, reg_genes[:, HARI_IDX], reg_genes[:, MAPEL_IDX], reg_genes[:, KELAS_IDX]))
        sorted_genes = reg_genes[sorted_indices]
        sorted_mapped_waktu = mapped_waktu[sorted_indices]
        
        if len(sorted_genes) > 1:
            curr_mkh = sorted_genes[:-1, [MAPEL_IDX, KELAS_IDX, HARI_IDX]]
            nxt_mkh = sorted_genes[1:, [MAPEL_IDX, KELAS_IDX, HARI_IDX]]
            
            same_mkh = np.all(curr_mkh == nxt_mkh, axis=1)
            waktu_gap = (sorted_mapped_waktu[1:] - sorted_mapped_waktu[:-1]) > 1
            
            sc2_v = np.sum(same_mkh & waktu_gap)
        
    p_total += sc2_v * W_SOFT

    # SC-3a: Guru Daily Limit (max 7 slots)
    if np.any(mask_with_guru):
        guru_day_genes = chromosome[mask_with_guru][:, [GURU_IDX, HARI_IDX]]
        _, counts = np.unique(guru_day_genes, axis=0, return_counts=True)
        sc3a_v = np.sum(np.maximum(0, counts - 7))
        p_total += sc3a_v * W_SOFT

    # SC-3b: PNS/P3K Min Weekly (min 24 slots)
    if len(pns_p3k_ids) > 0:
        pns_list = list(pns_p3k_ids)
        mask_pns_present = np.isin(chromosome[:, GURU_IDX], pns_list)
        pns_assigned = chromosome[mask_pns_present, GURU_IDX]
        
        if len(pns_assigned) > 0:
            unique_pns, counts_pns = np.unique(pns_assigned, return_counts=True)
            pns_counts_dict = dict(zip(unique_pns, counts_pns))
        else:
            pns_counts_dict = {}
            
        sc3b_v = 0
        for g_id in pns_list:
            sc3b_v += max(0, 24 - pns_counts_dict.get(g_id, 0))
        p_total += sc3b_v * W_SOFT

    return 1.0 / (1.0 + p_total)
