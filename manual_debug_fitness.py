import numpy as np
import pandas as pd
import argparse
import random
import sys
from fitness import calculate_fitness, MAPEL_IDX, GURU_IDX, KELAS_IDX, WAKTU_IDX, HARI_IDX
from database import get_special_ids
from population import generate_population
import main  # Untuk mengakses fungsi selection, crossover, mutate

class MarkdownReporter:
    def __init__(self, output_file):
        self.output_file = output_file
        self.file = open(output_file, "w")

    def write(self, text):
        self.file.write(text + "\n")

    def heading(self, text, level=1):
        self.file.write("\n" + "#" * level + " " + text + "\n\n")

    def math_inline(self, text):
        return f"${text}$"

    def math_block(self, text):
        self.write(f"$$\n{text}\n$$\n")

    def table_dual(self, df, title):
        self.heading(f"{title}", level=4)
        # Markdown Table
        self.write(df.to_markdown(index=False) + "\n")

    def close(self):
        self.file.close()

def format_fitness_scientific(value):
    if value == 0: return "0"
    mantissa, exponent = f"{value:.15e}".split("e")
    return f"{mantissa} \\times 10^{{{int(exponent)}}}"

def get_gene_violations_details(chromosome, special_ids):
    n = len(chromosome)
    violations = [[] for _ in range(n)]
    
    up_id = special_ids.get('upacara')
    be_id = special_ids.get('bersih')
    is_id = special_ids.get('istirahat')
    co_ids = special_ids.get('co_teaching', set())

    # HC1: Fixed Slot
    for i in range(n):
        m, g, k, t, h = chromosome[i]
        v = ""
        if h == 1 and t == 1:
            if m != up_id or g != -1: v = "HC1: Bukan Upacara"
        elif h == 4 and t == 1:
            if m != be_id or g != -1: v = "HC1: Bukan Bersih-bersih"
        elif t == 5 or (h < 5 and t == 8):
            if m != is_id or g != -1: v = "HC1: Bukan Istirahat"
        elif h == 5 and t >= 7:
            if m != -1 or g != -1: v = "HC1: Harus Kosong (Jumat)"
        if v: violations[i].append(v)

    # HC2: Bentrok Kelas
    kth_combos, kth_inverse, kth_counts = np.unique(chromosome[:, [KELAS_IDX, WAKTU_IDX, HARI_IDX]], axis=0, return_inverse=True, return_counts=True)
    multi_slots = np.where(kth_counts > 1)[0]
    for slot_idx in multi_slots:
        indices = np.where(kth_inverse == slot_idx)[0]
        mapels = chromosome[indices, MAPEL_IDX]
        has_non_co = any(m not in co_ids for m in mapels)
        is_conflict = False
        if has_non_co: is_conflict = True
        else:
            if len(np.unique(mapels)) > 1: is_conflict = True
        
        if is_conflict:
            for idx in indices:
                violations[idx].append("HC2: Bentrok Kelas")

    # HC3: Bentrok Guru
    mask_guru = chromosome[:, GURU_IDX] != -1
    if np.any(mask_guru):
        g_data = chromosome[mask_guru][:, [GURU_IDX, WAKTU_IDX, HARI_IDX]]
        gth_combos, gth_inverse, gth_counts = np.unique(g_data, axis=0, return_inverse=True, return_counts=True)
        multi_g_slots = np.where(gth_counts > 1)[0]
        guru_indices = np.where(mask_guru)[0]
        for g_slot_idx in multi_g_slots:
            indices_in_subset = np.where(gth_inverse == g_slot_idx)[0]
            original_indices = guru_indices[indices_in_subset]
            for idx in original_indices:
                violations[idx].append("HC3: Bentrok Guru")

    return [", ".join(sorted(list(set(v)))) if v else "-" for v in violations]

def get_hc_details(chromosome, special_ids):
    up_id = special_ids.get('upacara')
    be_id = special_ids.get('bersih')
    is_id = special_ids.get('istirahat')
    co_ids = special_ids.get('co_teaching', set())
    
    hc_details = {'hc1': [], 'hc2': [], 'hc3': []}
    n = len(chromosome)
    
    # HC1 Detail
    for i in range(n):
        m, g, k, t, h = chromosome[i]
        msg = ""
        if h == 1 and t == 1:
            if m != up_id or g != -1: msg = f"Harus Upacara (ID {up_id}), ditemukan Mapel {m} Guru {g}"
        elif h == 4 and t == 1:
            if m != be_id or g != -1: msg = f"Harus Bersih-bersih (ID {be_id}), ditemukan Mapel {m} Guru {g}"
        elif t == 5:
            if m != is_id or g != -1: msg = f"Harus Istirahat (ID {is_id}), ditemukan Mapel {m} Guru {g}"
        elif h < 5 and t == 8:
            if m != is_id or g != -1: msg = f"Harus Istirahat (ID {is_id}), ditemukan Mapel {m} Guru {g}"
        elif h == 5 and t >= 7:
            if m != -1 or g != -1: msg = "Harus Kosong (Jumat Jam 7+), ditemukan isi"
        
        if msg:
            hc_details['hc1'].append({
                'Item': f"Gen {i} (H:{h}, T:{t}, K:{k})",
                'Keterangan': msg,
                'Violation': 1
            })

    # HC2 Detail
    kth_combos, kth_inverse, kth_counts = np.unique(chromosome[:, [KELAS_IDX, WAKTU_IDX, HARI_IDX]], axis=0, return_inverse=True, return_counts=True)
    multi_slots = np.where(kth_counts > 1)[0]
    for slot_idx in multi_slots:
        indices = np.where(kth_inverse == slot_idx)[0]
        mapels = chromosome[indices, MAPEL_IDX]
        has_non_co = any(m not in co_ids for m in mapels)
        is_conflict = False
        if has_non_co: is_conflict = True
        else:
            if len(np.unique(mapels)) > 1: is_conflict = True
        
        if is_conflict:
            k, t, h = kth_combos[slot_idx]
            mapel_list = ", ".join(map(str, mapels))
            hc_details['hc2'].append({
                'Item': f"Kelas {k} (H:{h}, T:{t})",
                'Keterangan': f"Bentrok {kth_counts[slot_idx]} gen: Mapel ID [{mapel_list}]",
                'Violation': kth_counts[slot_idx] - 1
            })

    # HC3 Detail
    mask_guru = chromosome[:, GURU_IDX] != -1
    if np.any(mask_guru):
        g_data = chromosome[mask_guru]
        gth_combos, gth_inverse, gth_counts = np.unique(g_data[:, [GURU_IDX, WAKTU_IDX, HARI_IDX]], axis=0, return_inverse=True, return_counts=True)
        multi_g_slots = np.where(gth_counts > 1)[0]
        for g_slot_idx in multi_g_slots:
            g, t, h = gth_combos[g_slot_idx]
            indices_in_subset = np.where(gth_inverse == g_slot_idx)[0]
            kelas_list = ", ".join(map(str, g_data[indices_in_subset, KELAS_IDX]))
            hc_details['hc3'].append({
                'Item': f"Guru {g} (H:{h}, T:{t})",
                'Keterangan': f"Mengajar di {gth_counts[g_slot_idx]} kelas: Kelas ID [{kelas_list}]",
                'Violation': gth_counts[g_slot_idx] - 1
            })
            
    return hc_details

def get_sc_details(chromosome, special_ids):
    up_id = special_ids.get('upacara')
    be_id = special_ids.get('bersih')
    is_id = special_ids.get('istirahat')
    pns_p3k_ids = special_ids.get('pns_p3k', set())
    
    sc_details = {'sc1': [], 'sc2': [], 'sc3': []}
    
    mask_reg = ~np.isin(chromosome[:, MAPEL_IDX], [up_id, be_id, is_id, -1])
    reg_genes = chromosome[mask_reg]
    
    if len(reg_genes) > 0:
        # SC1 Details
        unique_mkh, counts_mkh = np.unique(reg_genes[:, [MAPEL_IDX, KELAS_IDX, HARI_IDX]], axis=0, return_counts=True)
        for i in range(len(unique_mkh)):
            if counts_mkh[i] > 5:
                sc_details['sc1'].append({
                    'Item': f"Mapel {unique_mkh[i,0]} @ Kelas {unique_mkh[i,1]} (Hari {unique_mkh[i,2]})",
                    'Keterangan': f"Kelebihan jam: {counts_mkh[i]} slot (> 5)",
                    'Pelanggaran': counts_mkh[i] - 5
                })
        
        unique_mk, inverse_mk = np.unique(reg_genes[:, [MAPEL_IDX, KELAS_IDX]], axis=0, return_inverse=True)
        total_slots_mk = np.bincount(inverse_mk)
        mk_day = np.unique(np.column_stack((inverse_mk, reg_genes[:, HARI_IDX])), axis=0)
        actual_days_mk = np.bincount(mk_day[:, 0], minlength=len(unique_mk))
        min_days_mk = np.ceil(total_slots_mk / 5.0).astype(int)
        
        for i in range(len(unique_mk)):
            if actual_days_mk[i] < min_days_mk[i]:
                sc_details['sc1'].append({
                    'Item': f"Mapel {unique_mk[i,0]} @ Kelas {unique_mk[i,1]}",
                    'Keterangan': f"Kurang hari: {actual_days_mk[i]} hari (Min {min_days_mk[i]} hari dari {total_slots_mk[i]} slot)",
                    'Pelanggaran': min_days_mk[i] - actual_days_mk[i]
                })

        # SC2 Details
        mapped_waktu = reg_genes[:, WAKTU_IDX].copy()
        mapped_waktu[reg_genes[:, WAKTU_IDX] > 5] -= 1
        mapped_waktu[reg_genes[:, WAKTU_IDX] > 8] -= 1
        sorted_idx = np.lexsort((mapped_waktu, reg_genes[:, HARI_IDX], reg_genes[:, MAPEL_IDX], reg_genes[:, KELAS_IDX]))
        s_genes = reg_genes[sorted_idx]
        s_waktu = mapped_waktu[sorted_idx]
        
        if len(s_genes) > 1:
            for i in range(len(s_genes)-1):
                if np.all(s_genes[i, [MAPEL_IDX, KELAS_IDX, HARI_IDX]] == s_genes[i+1, [MAPEL_IDX, KELAS_IDX, HARI_IDX]]):
                    if (s_waktu[i+1] - s_waktu[i]) > 1:
                        sc_details['sc2'].append({
                            'Item': f"Mapel {s_genes[i,0]} @ Kelas {s_genes[i,2]} (Hari {s_genes[i,4]})",
                            'Keterangan': f"Terpecah antara jam {s_genes[i,3]} dan {s_genes[i+1,3]}",
                            'Pelanggaran': 1
                        })

    # SC3 Details
    mask_guru = chromosome[:, GURU_IDX] != -1
    if np.any(mask_guru):
        g_day = chromosome[mask_guru][:, [GURU_IDX, HARI_IDX]]
        unique_gh, counts_gh = np.unique(g_day, axis=0, return_counts=True)
        for i in range(len(unique_gh)):
            if counts_gh[i] > 7:
                sc_details['sc3'].append({
                    'Item': f"Guru {unique_gh[i,0]} (Hari {unique_gh[i,1]})",
                    'Keterangan': f"Beban harian: {counts_gh[i]} slot (> 7)",
                    'Pelanggaran': counts_gh[i] - 7
                })
    
    if len(pns_p3k_ids) > 0:
        mask_pns = np.isin(chromosome[:, GURU_IDX], list(pns_p3k_ids))
        pns_assigned = chromosome[mask_pns, GURU_IDX]
        u_pns, c_pns = np.unique(pns_assigned, return_counts=True)
        counts_dict = dict(zip(u_pns, c_pns))
        for g_id in pns_p3k_ids:
            c = counts_dict.get(g_id, 0)
            if c < 24:
                sc_details['sc3'].append({
                    'Item': f"Guru PNS {g_id}",
                    'Keterangan': f"Beban mingguan: {c} slot (Min 24)",
                    'Pelanggaran': 24 - c
                })
                
    return sc_details

def run_ga_cycle(pop_name, reporter, special_ids, filter_type="slot", filter_val=None):
    if filter_type == "kelas":
        label = f"Filter: Kelas ID {filter_val} (Seminggu Penuh)"
        mask_func = lambda chrom: (chrom[:, KELAS_IDX] == filter_val)
        # hapasi, kita tetap biarkan dia di kelas tersebut tapi waktu/hari bisa apa saja (namun tetap di slicing kita)
        # Tapi karena slicing kita adalah "Seluruh Minggu", maka mutasi waktu/hari bebas di sini.
        h_target, w_target = "Semua", "Semua"
    elif filter_type == "guru":
        label = f"Filter: Guru ID {filter_val} (Seminggu Penuh)"
        mask_func = lambda chrom: (chrom[:, GURU_IDX] == filter_val)
        h_target, w_target = "Semua", "Semua"
    else:
        h_target, w_target = filter_val
        label = f"Filter: Hari {h_target}, Waktu {w_target}"
        mask_func = lambda chrom: (chrom[:, HARI_IDX] == h_target) & (chrom[:, WAKTU_IDX] == w_target)

    reporter.heading(f"{pop_name} ({label})", level=2)
    
    # Definisi Narasi Constraint
    constraint_narratives = {
        "hc1": "Aturan Slot Tetap: Upacara (Senin 1), Bersih (Kamis 1), Istirahat (Jam 5, Jam 8), Jumat Pulang Awal.",
        "hc2": "Konflik Kelas: Satu kelas tidak boleh ada > 1 mapel di jam yang sama (kecuali Co-Teaching mapel sama).",
        "hc3": "Konflik Guru: Satu guru tidak boleh mengajar di > 1 kelas pada jam yang sama.",
        "sc1": "Penyebaran Mapel: Mapel harus tersebar minimal 1 hari per 5 jam, max 5 jam per hari.",
        "sc2": "Blok Pertemuan: Mapel yang sama di hari yang sama harus berurutan (kontigu/tandem).",
        "sc3": "Beban Kerja Guru: Max 7 jam per hari, Min 24 jam per minggu (untuk PNS)."
    }

    # --- TAHAP 1: EVALUASI POPULASI AWAL ---
    reporter.heading("Tahap 1: Inisialisasi & Evaluasi Populasi (Slicing Aktif)", level=3)
    
    # Generate full population then SLICE IT to become the "mini-population"
    # Sesuai request: 3 kromosom per populasi
    pop_size = 3
    raw_population = generate_population(pop_size=pop_size)
    mini_population = []
    
    # Semua kromosom dalam populasi ini menggunakan slicing yang sama
    for i, full_chrom in enumerate(raw_population):
        mask = mask_func(full_chrom)
        mini_population.append(full_chrom[mask])

    n_mini = len(mini_population[0]) # Biasanya jumlah kelas (misal 11)
    reporter.write(f"Slicing aktif untuk {pop_name}! Nilai $n$ berubah dari 546 menjadi $n_{{slice}} = {n_mini}$.\n")
    reporter.write("Seluruh siklus GA (Fitness, Seleksi, Crossover, Mutasi) akan dijalankan hanya pada data terbatas ini.\n")
    
    fitness_scores = []
    for i, chromosome in enumerate(mini_population):
        score, details = calculate_fitness(chromosome, special_ids, return_details=True)
        fitness_scores.append(score)
        
        reporter.heading(f"Individu $C_{{{i+1}}}$ ($n = {len(chromosome)}$)", level=4)
        
        v_details = get_gene_violations_details(chromosome, special_ids)
        df_gen = pd.DataFrame(chromosome, columns=['mapel_id', 'guru_id', 'kelas_id', 'waktu_id', 'hari_id'])
        df_gen['Violation'] = v_details
        reporter.table_dual(df_gen, f"Data Gen $C_{{{i+1}}}$")
        
        # Rincian Fitness
        fit_rows = []
        for key in ["hc1", "hc2", "hc3", "sc1", "sc2", "sc3"]:
            fit_rows.append({"Constraint": key.upper(), "Violation": details[key]['v'], "Penalty": details[key]['p']})
        df_fit = pd.DataFrame(fit_rows)
        reporter.table_dual(df_fit, f"Rincian Penalti $C_{{{i+1}}}$ (Dihitung dari $n={len(chromosome)}$)")
        
        # Penjelasan Detail Constraint
        hc_details = get_hc_details(chromosome, special_ids)
        sc_details = get_sc_details(chromosome, special_ids)
        
        for key in ["hc1", "hc2", "hc3", "sc1", "sc2", "sc3"]:
            all_details = hc_details if "hc" in key else sc_details
            if details[key]['v'] > 0 and all_details[key]:
                df_detail = pd.DataFrame(all_details[key])
                if "Violation" not in df_detail.columns and "Pelanggaran" in df_detail.columns:
                    df_detail.rename(columns={"Pelanggaran": "Violation"}, inplace=True)
                
                reporter.write(f"\n> **{constraint_narratives[key]}**")
                reporter.table_dual(df_detail, f"Analisis Perhitungan {key.upper()} ($C_{{{i+1}}}$)")
        
        reporter.write(f"**Kalkulasi Akhir $C_{{{i+1}}}$:**")
        reporter.write(f"- Total Penalti ($p_{{total}}$): {details['p_total']}")
        reporter.write(f"- Fitness Score ($f$): ${format_fitness_scientific(score)}$")

    # --- TAHAP 2: SELEKSI INDUK ---
    reporter.heading("Tahap 2: Seleksi Induk (Tournament Selection)", level=3)
    reporter.write("Seleksi dilakukan dengan mengambil dua individu secara acak dan memilih yang terbaik.\n")
    
    # Simulasi manual untuk pelacakan
    idx1, idx2 = random.sample(range(pop_size), 2)
    p1_idx = idx1 if fitness_scores[idx1] > fitness_scores[idx2] else idx2
    
    reporter.write(f"**Turnamen 1:**")
    reporter.write(f"- Kandidat A: $C_{{{idx1+1}}}$ ($f = {format_fitness_scientific(fitness_scores[idx1])}$)")
    reporter.write(f"- Kandidat B: $C_{{{idx2+1}}}$ ($f = {format_fitness_scientific(fitness_scores[idx2])}$)")
    reporter.write(f"- Hasil: $C_{{{p1_idx+1}}}$ terpilih sebagai Induk 1 ($P_1$).")

    idx3, idx4 = random.sample(range(pop_size), 2)
    p2_idx = idx3 if fitness_scores[idx3] > fitness_scores[idx4] else idx4
    
    reporter.write(f"**Turnamen 2:**")
    reporter.write(f"- Kandidat A: $C_{{{idx3+1}}}$ ($f = {format_fitness_scientific(fitness_scores[idx3])}$)")
    reporter.write(f"- Kandidat B: $C_{{{idx4+1}}}$ ($f = {format_fitness_scientific(fitness_scores[idx4])}$)")
    reporter.write(f"- Hasil: $C_{{{p2_idx+1}}}$ terpilih sebagai Induk 2 ($P_2$).")
    
    parent1 = mini_population[p1_idx]
    parent2 = mini_population[p2_idx]

    # --- TAHAP 3: CROSSOVER ---
    reporter.heading("Tahap 3: Crossover (Persilangan)", level=3)
    
    n_p1 = len(parent1)
    n_p2 = len(parent2)
    # Pilih titik potong yang aman untuk kedua induk
    min_n = min(n_p1, n_p2)
    point = random.randint(1, min_n - 1)
    
    child_raw = np.vstack((parent1[:point], parent2[point:]))
    
    reporter.write(f"Menggunakan *One-Point Crossover* dengan titik potong $k = {point}$ dari Induk 1 ($n={n_p1}$) dan Induk 2 ($n={n_p2}$).")
    reporter.math_block(rf"C_{{child}} = P_1[0:{point}] \cup P_2[{point}:n_{{p2}}]")
    
    # Visualisasi perpotongan P1 dan P2
    cols = ['mapel_id', 'guru_id', 'kelas_id', 'waktu_id', 'hari_id']
    df_p1 = pd.DataFrame(parent1, columns=cols)
    df_p1['Status'] = ['**DIAMBIL**' if i < point else '-' for i in range(len(df_p1))]
    reporter.table_dual(df_p1, f"Tabel Induk 1 ($P_1$) - Titik Potong k={point}")

    df_p2 = pd.DataFrame(parent2, columns=cols)
    df_p2['Status'] = ['**DIAMBIL**' if i >= point else '-' for i in range(len(df_p2))]
    reporter.table_dual(df_p2, f"Tabel Induk 2 ($P_2$) - Titik Potong k={point}")

    reporter.write(f"Anak yang terbentuk memiliki $n = {len(child_raw)}$ gen.")
    reporter.write(f"- Gen $0$ sampai ${point-1}$ diambil dari $P_1$.")
    reporter.write(f"- Gen ${point}$ sampai akhir diambil dari $P_2$.")

    # --- TAHAP 4: MUTASI ---
    reporter.heading("Tahap 4: Mutasi (Variasi Genetik)", level=3)
    
    reporter.write("Probabilitas mutasi ($P_m$) didefinisikan sebagai:")
    reporter.math_block(r"P_m = 0.05")
    reporter.write(r"Setiap gen dalam kromosom memiliki peluang independen untuk bermutasi:")
    reporter.math_block(r"P(c_i \in \text{mutate}) = P_m")
    
    reporter.write("Mutasi dilakukan pada **semua gen reguler** (bukan slot tetap) secara acak dengan probabilitas $5\\%$. Mutasi tidak terbatas hanya pada gen yang memiliki pelanggaran (violation). Hal ini bertujuan untuk menjaga variasi genetik dalam populasi.")
    reporter.write("\n> **Catatan Slicing:** Karena simulasi ini dijalankan pada irisan data terbatas (" + label + "), maka mutasi posisi gen tetap dikunci pada filter tersebut untuk menjaga integritas sampel audit.")
    
    # Tampilkan tabel original sebelum mutasi
    cols = ['mapel_id', 'guru_id', 'kelas_id', 'waktu_id', 'hari_id']
    v_details_before = get_gene_violations_details(child_raw, special_ids)
    df_before = pd.DataFrame(child_raw, columns=cols)
    df_before['Violation'] = v_details_before
    reporter.table_dual(df_before, "Tabel Anakan Sebelum Mutasi")

    # Capture mutasi manual
    mutation_rate = 0.05
    mask = np.random.rand(len(child_raw)) < mutation_rate
    
    # Proteksi fixed slots (Upacara, Istirahat, Bersih)
    upacara_id = special_ids.get('upacara')
    bersih_id = special_ids.get('bersih')
    istirahat_id = special_ids.get('istirahat')
    fixed_mask = np.isin(child_raw[:, MAPEL_IDX], [upacara_id, bersih_id, istirahat_id])
    
    actual_mutation_mask = mask & ~fixed_mask
    indices_to_mutate = np.where(actual_mutation_mask)[0]
    
    reporter.write(f"**Hasil Scan Mutasi:**")
    reporter.write(f"- Total Gen ($n_{{child}}$): {len(child_raw)}")
    reporter.write(f"- Gen Terkena Mask Mutasi: {np.sum(mask)}")
    reporter.write(f"- Gen Terproteksi (Fixed Slot): {np.sum(fixed_mask)}")
    reporter.write(f"- Gen yang Benar-benar Bermutasi: {len(indices_to_mutate)}")
    
    child_mutated = child_raw.copy()
    if len(indices_to_mutate) > 0:
        mut_logs = []
        for idx in indices_to_mutate:
            old_w, old_h = child_raw[idx, WAKTU_IDX], child_raw[idx, HARI_IDX]
            # Jalankan mutate versi simpel untuk logging
            if filter_type == "slot":
                new_w = w_target
                new_h = h_target
            else:
                # Untuk filter kelas/guru seminggu penuh, mutasi bisa ke waktu/hari mana saja (1-11, 1-5)
                new_w = random.randint(1, 11)
                new_h = random.randint(1, 5)
            
            child_mutated[idx, WAKTU_IDX] = new_w
            child_mutated[idx, HARI_IDX] = new_h
            
            mut_logs.append({
                "Gen Index": idx,
                "Mapel ID": child_raw[idx, MAPEL_IDX],
                "Kelas ID": child_raw[idx, KELAS_IDX],
                "Violation (Sebelum)": v_details_before[idx],
                "Waktu (Lama)": old_w,
                "Hari (Lama)": old_h,
                "Waktu (Baru)": new_w,
                "Hari (Baru)": new_h
            })
        
        df_mut = pd.DataFrame(mut_logs)
        reporter.table_dual(df_mut, "Log Perubahan Mutasi")
        
        # Tampilkan tabel setelah mutasi
        v_details_after = get_gene_violations_details(child_mutated, special_ids)
        df_after = pd.DataFrame(child_mutated, columns=cols)
        df_after['Violation'] = v_details_after
        reporter.table_dual(df_after, "Tabel Anakan Setelah Mutasi")
    else:
        reporter.write("Tidak ada gen yang bermutasi pada percobaan ini.\n")

    # Final Fitness for Child
    child_final = child_mutated
    score_child, details_child = calculate_fitness(child_final, special_ids, return_details=True)
    
    reporter.heading("Hasil Akhir Anakan", level=3)
    reporter.write(f"Setelah proses crossover dan mutasi, anakan ($C_{{child}}$) memiliki fitness sebagai berikut:\n")
    
    # Penjelasan Detail Constraint untuk Anakan
    hc_c = get_hc_details(child_final, special_ids)
    sc_c = get_sc_details(child_final, special_ids)
    for key in ["hc1", "hc2", "hc3", "sc1", "sc2", "sc3"]:
        all_c = hc_c if "hc" in key else sc_c
        if details_child[key]['v'] > 0 and all_c[key]:
            df_c = pd.DataFrame(all_c[key])
            if "Violation" not in df_c.columns and "Pelanggaran" in df_c.columns:
                df_c.rename(columns={"Pelanggaran": "Violation"}, inplace=True)
            reporter.write(f"\n> **{constraint_narratives[key]}**")
            reporter.table_dual(df_c, f"Analisis Perhitungan {key.upper()} ($C_{{child}}$)")

    reporter.write(f"- Fitness Score: ${format_fitness_scientific(score_child)}$")
    reporter.write(f"- Total Pelanggaran: {details_child['p_total']}")

def run_manual_debug(output_path):
    reporter = MarkdownReporter(output_path)
    special_ids = get_special_ids()
    
    reporter.heading("Laporan Debugging Siklus Genetic Algorithm (GA)")
    reporter.write("Laporan ini mendokumentasikan langkah-langkah teknis dan perhitungan matematis dalam satu siklus reproduksi GA untuk dua dataset slicing berbeda (Mini Populasi 1 dan 2).\n")

    # Simulasi 1: Fokus SC1 & SC2 (Filter: Kelas ID 1, Seminggu Penuh)
    run_ga_cycle("Mini Populasi 1 (Fokus SC1 & SC2)", reporter=reporter, special_ids=special_ids, 
                 filter_type="kelas", filter_val=1)
    
    reporter.write("\n" + "---" * 10 + "\n")
    
    # Simulasi 2: Fokus SC3 (Filter: Guru ID 1, Seminggu Penuh)
    # Mencari ID Guru yang valid (bukan -1) untuk audit SC3
    run_ga_cycle("Mini Populasi 2 (Fokus SC3)", reporter=reporter, special_ids=special_ids, 
                 filter_type="guru", filter_val=1)

    reporter.heading("KESIMPULAN DEBUGGING", level=2)
    reporter.write("1. Perhitungan fitness global divalidasi dengan rincian per-constraint untuk dua skenario slicing.")
    reporter.write("2. Alur reproduksi (Seleksi, Crossover, Mutasi) telah terdokumentasi dengan transparansi data untuk masing-masing populasi.")

    reporter.close()
    print(f"Laporan debugging berhasil dibuat di: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Manual Debugging GA with Markdown Output')
    parser.add_argument('-o', '--output', type=str, default='output.md', help='Path ke file output markdown (default: output.md)')
    args = parser.parse_args()
    
    run_manual_debug(args.output)
