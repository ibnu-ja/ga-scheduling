import sqlite3
from collections import defaultdict

DB_PATH = "db/data.sqlite"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row  # Agar bisa diakses seperti dictionary (nama kolom)
    return conn


def get_beban_mengajar():
    """Mengambil semua target jadwal yang harus dibuat."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT mapel_id AS id_mapel, kelas_id AS id_kelas, jumlah_waktu
                   FROM beban_mengajar
                   """)
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return data


def get_mapel_guru_mapping():
    """
    Mengambil daftar guru yang berkompeten untuk tiap mapel.
    Format output: { id_mapel: [id_guru1, id_guru2, ...] }
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT mapel_id, guru_id FROM mapel_guru")

    mapping = defaultdict(list)
    for row in cursor.fetchall():
        mapping[row['mapel_id']].append(row['guru_id'])

    conn.close()
    return mapping


def get_special_ids():
    """Mengambil ID untuk mapel khusus, co-teaching, dan guru PNS/P3K."""
    conn = get_connection()
    cursor = conn.cursor()

    # Special Mapels
    cursor.execute("SELECT id, nama FROM mapel WHERE nama IN ('Upacara', 'Kamis Bersih-besih', 'Istirahat')")
    special_mapels = {row['nama']: row['id'] for row in cursor.fetchall()}

    # Co-teaching mapels
    cursor.execute("SELECT id FROM mapel WHERE is_coteaching = 1")
    co_teaching_ids = {row['id'] for row in cursor.fetchall()}

    # PNS/P3K gurus
    cursor.execute("SELECT id FROM guru WHERE status IN ('PNS', 'P3K')")
    pns_p3k_ids = {row['id'] for row in cursor.fetchall()}

    conn.close()
    return {
        'upacara': special_mapels.get('Upacara'),
        'bersih': special_mapels.get('Kamis Bersih-besih'),
        'istirahat': special_mapels.get('Istirahat'),
        'co_teaching': co_teaching_ids,
        'pns_p3k': pns_p3k_ids
    }


def save_best_chromosome(chromosome, fitness_score, generation):
    """Menyimpan kromosom terbaik ke database."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Non-aktifkan status kromosom lama
        cursor.execute("UPDATE chromosome SET status = 'arsip' WHERE status = 'aktif'")

        # Insert record kromosom baru
        cursor.execute(
            "INSERT INTO chromosome (generasi, fitness, status) VALUES (?, ?, 'aktif')",
            (generation, fitness_score)
        )
        chromosome_id = cursor.lastrowid

        # Insert semua gen
        genes_data = []
        for gene in chromosome:
            # gene: [mapel_id, guru_id, kelas_id, waktu_id, hari_id]
            # Convert -1 back to NULL for guru_id
            g_id = int(gene[1]) if gene[1] != -1 else None
            genes_data.append((
                chromosome_id,
                int(gene[0]),
                g_id,
                int(gene[2]),
                int(gene[3]),
                int(gene[4])
            ))

        cursor.executemany(
            """
            INSERT INTO chromosome_gene (chromosome_id, mapel_id, guru_id, kelas_id, waktu_id, hari_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            genes_data
        )
        conn.commit()
        print(f"Kromosom terbaik (fitness {fitness_score:.6f}) berhasil disimpan ke database.")
    except Exception as e:
        conn.rollback()
        print(f"Gagal menyimpan kromosom: {e}")
    finally:
        conn.close()