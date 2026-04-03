import numpy as np
import pandas as pd
from fitness import calculate_fitness, MAPEL_IDX, GURU_IDX, KELAS_IDX, WAKTU_IDX, HARI_IDX
from database import get_special_ids
from population import generate_population

def format_fitness_scientific(value):
    if value == 0: return "0"
    mantissa, exponent = f"{value:.15e}".split("e")
    return f"{mantissa} * 10^{int(exponent)}"

def run_manual_debug():
    # 1. Persiapan Data & ID Spesial
    special_ids = get_special_ids()
    upacara_id = special_ids.get('upacara')
    
    # 2. Inisialisasi Populasi (Sesuai Request: Pop = {C1, C2, C3, C4, C5, C6})
    print("Inisialisasi Populasi (n=6)...")
    population = generate_population(pop_size=6)
    
    print("\n" + "="*70)
    print("DEBUGGING KROMOSOM: PERHITUNGAN MANUAL FITNESS")
    print("="*70)

    for i, chromosome in enumerate(population):
        # --- LOGIKA FILTER SESUAI INSTRUKSI BARU ---
        # Kromosom 0-2 (C1-C3) -> Filter: Selasa (Hari 2), Jam 07.00 (Waktu 1)
        if i < 3:
            h_target, w_target = 2, 1 
            label = f"Kromosom {i+1} (Filter: Hari 2, Waktu 1)"
        # Kromosom 3-5 (C4-C6) -> Filter: Rabu (Hari 3), Jam 07.00 (Waktu 1)
        else:
            h_target, w_target = 3, 1
            label = f"Kromosom {i+1} (Filter: Hari 3, Waktu 1)"

        # 3. Slicing/Filtering Gen (Menampilkan sampel terbatas untuk mata manusia)
        mask = (chromosome[:, HARI_IDX] == h_target) & (chromosome[:, WAKTU_IDX] == w_target)
        mini_chrom = chromosome[mask]
        
        # 4. Hitung Fitness dengan Detail
        score, details = calculate_fitness(chromosome, special_ids, return_details=True)
        
        print(f"\n>>> {label}")
        
        # 5. Visualisasi Tabel dalam format TSV untuk Excel
        print("DATA GEN (TSV Format - Copy to Excel):")
        cols = ['mapel_id', 'guru_id', 'kelas_id', 'waktu_id', 'hari_id']
        print("\t".join(cols))
        for row in mini_chrom:
            print("\t".join(map(str, row)))
        
        # 6. Print Semua Kalkulasi dan Nilai
        print("\nRINCIAN PERHITUNGAN FITNESS (TSV Format - Copy to Excel):")
        cols_fitness = ['Constraint', 'Violation', 'Penalty']
        print("\t".join(cols_fitness))
        for key in ['hc1', 'hc3', 'hc4', 'sc1', 'sc2', 'sc3a', 'sc3b']:
            v = details[key]['v']
            p = details[key]['p']
            print(f"{key.upper()}\t{v}\t{p}")
        
        print(f"TOTAL PENALTY\t-\t{details['p_total']}")
        print(f"FITNESS SCORE\t-\t{format_fitness_scientific(score)}")
        
        # --- INFORMASI TRACKING UNTUK AUDIT ---
        print("-" * 30)
        # Audit HC-3: Cek ID Kelas yang sama (Bentrok Kelas)
        classes, counts = np.unique(mini_chrom[:, KELAS_IDX], return_counts=True)
        v3_slot = np.sum(counts - 1)
        print(f"[Audit HC-3] Pelanggaran Bentrok Kelas di tabel atas: {v3_slot}")
        
        # Audit HC-4: Cek Guru != -1 yang mengajar di > 1 kelas
        mask_g = mini_chrom[:, GURU_IDX] != -1
        if np.any(mask_g):
            gurus, g_counts = np.unique(mini_chrom[mask_g, GURU_IDX], return_counts=True)
            v4_slot = np.sum(g_counts - 1)
            print(f"[Audit HC-4] Pelanggaran Bentrok Guru di tabel atas: {v4_slot}")

    # Menampilkan Ringkasan Rencana Utama (Context Retention)
    print("\n" + "="*70)
    print("RINGKASAN TRACKING & BREAKPOINT (UNTUK MAIN.PY)")
    print("="*70)
    print("1. Flow GA: Init (pop.py:131) -> Fitness (fit.py:174) -> Select (main.py:145) -> Repro (main.py:150).")
    print("2. Struktur Data: Ci (2D NumPy Array), Kolom: 0:mapel, 1:guru, 2:kelas, 3:waktu, 4:hari.")
    print("3. Variabel Kunci: fitness_scores, p_total (akumulasi penalti), selected (induk), c1 (anak).")

if __name__ == "__main__":
    run_manual_debug()
