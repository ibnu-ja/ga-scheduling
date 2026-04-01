import numpy as np

# IDs constants (Strict Identifiers)
UPACARA_ID = 1
BERSIH_ID = 2
ISTIRAHAT_ID = 3

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
    p_total = 0
    
    # Weights
    W_HARD = 1000
    W_SOFT = 500

    # HC-1: Fixed Time Slots
    hc1_v = 0
    # Senin (1) Jam 1: Upacara
    mask_senin_1 = (chromosome[:, HARI_IDX] == 1) & (chromosome[:, WAKTU_IDX] == 1)
    if np.any(mask_senin_1):
        hc1_v += np.sum((chromosome[mask_senin_1, MAPEL_IDX] != UPACARA_ID) | (chromosome[mask_senin_1, GURU_IDX] != -1))
    
    # Kamis (4) Jam 1: Bersih-bersih
    mask_kamis_1 = (chromosome[:, HARI_IDX] == 4) & (chromosome[:, WAKTU_IDX] == 1)
    if np.any(mask_kamis_1):
        hc1_v += np.sum((chromosome[mask_kamis_1, MAPEL_IDX] != BERSIH_ID) | (chromosome[mask_kamis_1, GURU_IDX] != -1))
    
    # Jam 5 & 8 Every Day: Istirahat
    mask_istirahat = (chromosome[:, WAKTU_IDX] == 5) | (chromosome[:, WAKTU_IDX] == 8)
    if np.any(mask_istirahat):
        hc1_v += np.sum((chromosome[mask_istirahat, MAPEL_IDX] != ISTIRAHAT_ID) | (chromosome[mask_istirahat, GURU_IDX] != -1))
    
    p_total += hc1_v * W_HARD

    # Co-teaching mapels from DB
    co_teaching_ids = special_ids['co_teaching'] if special_ids else {1, 2} # Default to some IDs if not provided
    pns_p3k_ids = special_ids['pns_p3k'] if special_ids else set()

    # HC-3: Kelas Conflict (Exclude Co-Teaching)
    mask_non_coteaching = ~np.isin(chromosome[:, MAPEL_IDX], list(co_teaching_ids))
    non_ct_genes = chromosome[mask_non_coteaching]
    if len(non_ct_genes) > 0:
        _, counts = np.unique(non_ct_genes[:, [KELAS_IDX, WAKTU_IDX, HARI_IDX]], axis=0, return_counts=True)
        hc3_v = np.sum(counts - 1) 
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
    # Group by mapel, kelas
    # Filter out special mapels first
    mask_regular = ~np.isin(chromosome[:, MAPEL_IDX], [UPACARA_ID, BERSIH_ID, ISTIRAHAT_ID])
    reg_genes = chromosome[mask_regular]
    
    if len(reg_genes) > 0:
        # 1. Daily excess > 5
        # Group by mapel, kelas, hari
        _, counts_mkh = np.unique(reg_genes[:, [MAPEL_IDX, KELAS_IDX, HARI_IDX]], axis=0, return_counts=True)
        sc1_v += np.sum(np.maximum(0, counts_mkh - 5))
        
        # 2. Lack of distribution days
        # We need total slots per (mapel, kelas)
        unique_mk, inverse_mk = np.unique(reg_genes[:, [MAPEL_IDX, KELAS_IDX]], axis=0, return_inverse=True)
        # Total slots per MK
        total_slots_mk = np.bincount(inverse_mk)
        # Unique days per MK
        mk_day = np.unique(np.column_stack((inverse_mk, reg_genes[:, HARI_IDX])), axis=0)
        actual_days_mk = np.bincount(mk_day[:, 0], minlength=len(unique_mk))
        
        min_days_mk = np.ceil(total_slots_mk / 5.0).astype(int)
        # ONLY apply penalty if total_slots_mk > 0, which is guaranteed by reg_genes
        # But we must be careful: if a mapel has 1 slot, min_days is 1. If actual_days is 1, penalty 0.
        # If a mapel has 6 slots, min_days is 2. If actual_days is 1, penalty 1.
        sc1_v += np.sum(np.maximum(0, min_days_mk - actual_days_mk))
    
    p_total += sc1_v * W_SOFT

    # SC-2a: Guru Daily Limit (max 7 slots)
    if np.any(mask_with_guru):
        guru_day_genes = chromosome[mask_with_guru][:, [GURU_IDX, HARI_IDX]]
        _, counts = np.unique(guru_day_genes, axis=0, return_counts=True)
        sc2a_v = np.sum(np.maximum(0, counts - 7))
        p_total += sc2a_v * W_SOFT

    # SC-2b: PNS/P3K Min Weekly (min 24 slots)
    # The guideline says: "Guru g in G_pns (status PNS/P3K) should have total teaching slots min 24 in one week."
    # We should use ALL PNS/P3K gurus, even if they have 0 slots in the chromosome.
    # However, my previous implementation only checked gurus present in chromosome.
    # Let's fix it to check all pns_p3k_ids.
    
    # Efficiently count all gurus in chromosome
    if len(pns_p3k_ids) > 0:
        pns_list = list(pns_p3k_ids)
        # Only count genes that have a guru in the PNS list
        mask_pns_present = np.isin(chromosome[:, GURU_IDX], pns_list)
        pns_assigned = chromosome[mask_pns_present, GURU_IDX]
        
        # Count occurrences of each PNS guru
        if len(pns_assigned) > 0:
            # Map g_id to an index for bincount
            # But g_id might be large. Better use unique with all possible pns_list.
            unique_pns, counts_pns = np.unique(pns_assigned, return_counts=True)
            pns_counts_dict = dict(zip(unique_pns, counts_pns))
        else:
            pns_counts_dict = {}
            
        sc2b_v = 0
        for g_id in pns_list:
            sc2b_v += max(0, 24 - pns_counts_dict.get(g_id, 0))
        p_total += sc2b_v * W_SOFT

    # SC-3: Subject Continuity (Clustering)
    # Penalize if the same subject (mapel, kelas) is split by other subjects on the same day.
    # Exclude breaks (Istirahat) from being "other subjects" that split.
    sc3_v = 0
    if len(reg_genes) > 0:
        # Sort by Kelas, Mapel, Hari, Waktu
        sorted_indices = np.lexsort((reg_genes[:, WAKTU_IDX], reg_genes[:, HARI_IDX], reg_genes[:, MAPEL_IDX], reg_genes[:, KELAS_IDX]))
        sorted_genes = reg_genes[sorted_indices]
        
        # Identify gaps between consecutive slots of the same (Kelas, Mapel, Hari)
        # Shifted versions to compare consecutive rows
        curr = sorted_genes[:-1]
        nxt = sorted_genes[1:]
        
        # Same group mask: same Kelas, same Mapel, same Hari
        same_group = (curr[:, KELAS_IDX] == nxt[:, KELAS_IDX]) & \
                     (curr[:, MAPEL_IDX] == nxt[:, MAPEL_IDX]) & \
                     (curr[:, HARI_IDX] == nxt[:, HARI_IDX])
        
        if np.any(same_group):
            # Check for non-consecutive slots within the same group
            # If waktu_diff > 1, it means there is a gap.
            # But wait, gap might be Istirahat (5 and 8). 
            # If curr is 4 and nxt is 6, it's a gap of 1 slot. If slot 5 is Istirahat, it's fine.
            # However, if slot 5 is ANOTHER subject, it's NOT fine.
            
            # Simplified version: if nxt_waktu - curr_waktu > 1, count it as a violation.
            # We then subtract 1 if the gap contains an Istirahat slot.
            waktu_diff = nxt[same_group, WAKTU_IDX] - curr[same_group, WAKTU_IDX]
            gaps = waktu_diff > 1
            if np.any(gaps):
                sc3_v += np.sum(waktu_diff[gaps] - 1)
                
                # Check for Istirahat in the gaps
                # If curr_waktu < 5 < nxt_waktu, then Istirahat (5) is in gap.
                # If curr_waktu < 8 < nxt_waktu, then Istirahat (8) is in gap.
                for gap_waktu in [5, 8]:
                    in_gap = (curr[same_group][gaps, WAKTU_IDX] < gap_waktu) & \
                             (nxt[same_group][gaps, WAKTU_IDX] > gap_waktu)
                    sc3_v -= np.sum(in_gap)
                
        sc3_v = max(0, sc3_v) # Ensure not negative
    
    p_total += sc3_v * W_SOFT

    return 1.0 / (1.0 + p_total)
