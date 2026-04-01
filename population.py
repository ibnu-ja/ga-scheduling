import numpy as np
import random
from database import get_beban_mengajar, get_mapel_guru_mapping

# Konstanta Ruang Waktu
HARI_IDS = list(range(1, 6))  # Senin (1) s/d Jumat (5)
WAKTU_IDS = list(range(1, 12))  # Slot 1 s/d 11


# IDs constants (Strict Identifiers)
UPACARA_ID = 1
BERSIH_ID = 2
ISTIRAHAT_ID = 3

def generate_chromosome(beban_data, guru_mapping, special_ids):
    """
    Membuat 1 kromosom kandidat.
    Format gen (baris): [id_mapel, id_guru, id_kelas, id_waktu, id_hari]
    """
    genes = []
    
    # 1. Fetch all class IDs
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM kelas")
    kelas_ids = [row['id'] for row in cursor.fetchall()]
    conn.close()

    # 2. Add Fixed Special Mapels for EVERY class (HC-1 & HC-5)
    # B(Upacara, k) = 1, B(Bersih, k) = 1, B(Istirahat, k) = 10
    for k_id in kelas_ids:
        # Senin Jam 1: Upacara
        genes.append([UPACARA_ID, -1, k_id, 1, 1])
        # Kamis Jam 1: Bersih-bersih
        genes.append([BERSIH_ID, -1, k_id, 1, 4])
        # Jam 5 & 8 Every day: Istirahat
        for h_id in HARI_IDS:
            genes.append([ISTIRAHAT_ID, -1, k_id, 5, h_id])
            genes.append([ISTIRAHAT_ID, -1, k_id, 8, h_id])

    # 3. Add Regular Mapels from beban_mengajar
    for beban in beban_data:
        id_mapel = beban['id_mapel']
        id_kelas = beban['id_kelas']
        jumlah_waktu = beban['jumlah_waktu']
        
        # Skip if it's a special mapel (already handled)
        if id_mapel in [UPACARA_ID, BERSIH_ID, ISTIRAHAT_ID]:
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
                    (id_waktu == 8)
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
    guru_mapping = get_mapel_guru_mapping()
    from database import get_special_ids
    special_ids = get_special_ids()

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
