import numpy as np
import random
from database import get_beban_mengajar, get_mapel_guru_mapping

# Konstanta Ruang Waktu
HARI_IDS = list(range(1, 6))  # Senin (1) s/d Jumat (5)
WAKTU_IDS = list(range(1, 12))  # Slot 1 s/d 11


def generate_chromosome(beban_data, guru_mapping, special_ids):
    """
    Membuat 1 kromosom kandidat.
    Format gen (baris): [id_mapel, id_guru, id_kelas, id_waktu, id_hari]
    """
    genes = []
    
    upacara_id = special_ids.get('upacara')
    bersih_id = special_ids.get('bersih')
    istirahat_id = special_ids.get('istirahat')

    # 1. Fetch all class IDs
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM kelas")
    kelas_ids = [row['id'] for row in cursor.fetchall()]
    conn.close()

    # 2. Add Fixed Special Mapels for EVERY class (HC-1 & HC-5)
    # B(Upacara, k) = 1, B(Bersih, k) = 1, B(Istirahat, k) = 9
    for k_id in kelas_ids:
        # Senin Jam 1: Upacara
        if upacara_id is not None:
            genes.append([upacara_id, -1, k_id, 1, 1])
        # Kamis Jam 1: Bersih-bersih
        if bersih_id is not None:
            genes.append([bersih_id, -1, k_id, 1, 4])
        # Jam 5 Every day: Istirahat
        if istirahat_id is not None:
            for h_id in HARI_IDS:
                genes.append([istirahat_id, -1, k_id, 5, h_id])
                # Jam 8 only for Monday-Thursday
                if h_id != 5:
                    genes.append([istirahat_id, -1, k_id, 8, h_id])

    # 3. Add Regular Mapels from beban_mengajar
    special_ids_set = {upacara_id, bersih_id, istirahat_id}
    for beban in beban_data:
        id_mapel = beban['id_mapel']
        id_kelas = beban['id_kelas']
        jumlah_waktu = beban['jumlah_waktu']
        
        # Skip if it's a special mapel (already handled)
        if id_mapel in special_ids_set:
            continue

        daftar_guru_tersedia = guru_mapping.get(id_mapel, [-1])

        for _ in range(jumlah_waktu):
            id_guru = random.choice(daftar_guru_tersedia)
            
            # Smart initialization: avoid already occupied slots in the same class
            # to reduce initial conflicts
            # Get current slots occupied by this class
            occupied_slots = set()
            for g in genes:
                if g[2] == id_kelas:
                    occupied_slots.add((g[4], g[3])) # (hari, waktu)

            # Avoid fixed slots during initialization
            attempts = 0
            while True:
                id_hari = random.choice(HARI_IDS)
                id_waktu = random.choice(WAKTU_IDS)
                
                is_fixed_slot = (
                    (id_hari == 1 and id_waktu == 1) or
                    (id_hari == 4 and id_waktu == 1) or
                    (id_waktu == 5) or
                    (id_waktu == 8 and id_hari != 5) or
                    (id_hari == 5 and id_waktu >= 7)
                )
                
                # Check if slot is occupied in this class
                is_occupied = (id_hari, id_waktu) in occupied_slots
                
                if not is_fixed_slot:
                    if not is_occupied or attempts > 20:
                        break
                attempts += 1

            gen = [id_mapel, id_guru, id_kelas, id_waktu, id_hari]
            genes.append(gen)
            occupied_slots.add((id_hari, id_waktu))

    return np.array(genes, dtype=int)


def generate_population(pop_size=100):
    """
    Membuat populasi awal (Langkah 3).
    Mengembalikan list berisi Numpy Array 2D.
    """
    print("Mengambil data dari database...")
    beban_data = get_beban_mengajar()
    
    # Pre-computation rule: Total regular teaching load must not exceed 39 slots per week per class
    from database import get_special_ids
    special_ids = get_special_ids()
    special_ids_set = {special_ids.get('upacara'), special_ids.get('bersih'), special_ids.get('istirahat')}
    
    kelas_total_beban = {}
    for beban in beban_data:
        if beban['id_mapel'] not in special_ids_set:
            k_id = beban['id_kelas']
            kelas_total_beban[k_id] = kelas_total_beban.get(k_id, 0) + beban['jumlah_waktu']
    
    for k_id, total in kelas_total_beban.items():
        if total > 39:
            raise ValueError(f"CRITICAL: Kelas ID {k_id} memiliki total beban mengajar reguler {total} (Maksimal 39).")

    guru_mapping = get_mapel_guru_mapping()

    print(f"Membangun {pop_size} kromosom awal...")
    population = []
    for _ in range(pop_size):
        chromosome = generate_chromosome(beban_data, guru_mapping, special_ids)
        population.append(chromosome)

    print(f"Selesai! Dimensi 1 kromosom: {population[0].shape} (Gen x Atribut)")
    return population


# Untuk test run langsung dari file ini
if __name__ == "__main__":
    pop = generate_population(pop_size=5)  # Test dengan 5 kromosom dulu
    print("\nContoh 5 Gen Pertama dari Kromosom ke-1:")
    print("Kolom: [Mapel, Guru, Kelas, Waktu, Hari]")
    print(pop[0][:5])
