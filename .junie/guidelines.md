# Project Guidelines: Genetic Algorithm for School Scheduling

This project implements a Genetic Algorithm (GA) to generate school schedules based on a strict mathematical model. The constraints are stored in an SQLite database.

## 1. Build/Configuration Instructions

### Prerequisites
- Python 3.8+
- SQLite3
- NumPy

### Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure the database file exists at `db/data.sqlite`.
4. DDL schema is available in `db/main/*.sql`.
5. **CRITICAL**: SQLite disables foreign keys by default. Any Python connection to the database MUST execute `PRAGMA foreign_keys = ON;` immediately after connecting.

## 2. Testing Information

### Running Tests
Tests are located in `test_fitness.py`. To run them:
```bash
python3 test_fitness.py
```

### Adding New Tests
When adding new constraints or modifying existing ones in `fitness.py`, add a corresponding test case in `test_fitness.py` by:
1. Creating a NumPy array representing a mock chromosome.
2. Calling `calculate_fitness(chromosome)`.
3. Asserting the expected fitness score (1.0 for no violations, < 1.0 for violations).

### Simple Test Example
```python
import numpy as np
from fitness import calculate_fitness

# Test if SC-3 (Guru daily limit 7) works
# Array format: [mapel_id, guru_id, kelas_id, waktu_id, hari_id]
bad_chromosome = np.array([[4, 100, 1, t, 1] for t in [2, 3, 4, 6, 7, 9, 10, 11]])
fitness = calculate_fitness(bad_chromosome)
assert fitness < 1.0
print("SC-3 violation detected correctly!")
```

## 3. Implementation Details & Code Style
- **Vectorization**: All fitness evaluations in `fitness.py` MUST use NumPy vectorized operations for performance. Avoid pure Python `for` loops over chromosome genes.
- **Chromosome Representation**: 
  - 2D NumPy integer array: `Shape (n_genes, 5)`.
  - Column indices: `0: mapel_id`, `1: guru_id`, `2: kelas_id`, `3: waktu_id`, `4: hari_id`.
  - `guru_id = -1` indicates no teacher (replaces `NULL`).
  - `mapel_id = -1` indicates an empty slot / no subject (replaces `NULL`).
- **Naming Convention**: Strictly use the `_id` suffix (e.g., `mapel_id`, `guru_id`).

---

## 4. Mathematical Model (Full Context)

### Himpunan: 
$$  
\begin{aligned}  
M &: \text{semua mapel yang ada termasuk Upacara, Bersih\text{-}bersih, dan Istirahat}, \\ 
G &: \text{semua guru yang ada}, \\
K &: \text{semua kelas yang ada}, \\
T &: \text{semua slot waktu, urutan 1 sampai 11}, \\
H &: {\text{Senin(1), Selasa(2), Rabu(3), Kamis(4), Jumat(5)}}, \quad |H| = 5.  
\end{aligned}
$$

**Gen** adalah satu kegiatan terjadwal, berisi lima informasi sekaligus:
$$c = (m,\ g,\ k,\ t,\ h)$$
Artinya: `mapel_id` $m$, diajarkan oleh `guru_id` $g$, untuk `kelas_id` $k$, di `waktu_id` $t$, pada `hari_id` $h$. Jika kegiatan tidak memiliki guru, maka $g = -1$. Jika slot dibiarkan kosong, maka $m = -1$ dan $g = -1$.

**Kromosom** adalah satu jadwal mingguan penuh:
$$C = \{c_1,\ c_2,\ \dots,\ c_n\}$$

**Fungsi beban mengajar $B$**: 
$$B : M \times K \rightarrow \mathbb{Z}_{\ge 0}$$
Nilai $B$ adalah input dari database, kecuali untuk mapel khusus:
- $B(\text{Upacara},\ k) = 1$
- $B(\text{Bersih-bersih},\ k) = 1$
- $B(\text{Istirahat},\ k) = 9$

---
### Hard Constraint (Weight $w_n = 1000$)

**1. Kendala Slot Waktu Tetap (Fixed Time Slots)**
Beberapa slot waktu sudah ditentukan isinya sejak awal, termasuk jam kepulangan hari Jumat.
- $h = 1 \wedge t = 1 \implies m = \text{Upacara}, g = -1$
- $h = 4 \wedge t = 1 \implies m = \text{Bersih-bersih}, g = -1$
- $t = 5 \implies m = \text{Istirahat}, g = -1$
- $h \in \{1, 2, 3, 4\} \wedge t = 8 \implies m = \text{Istirahat}, g = -1$
- $h = 5 \wedge t \ge 7 \implies m = -1, g = -1$ (Kosong/Pulang awal)

Setiap satu gen yang menempati slot tersebut tapi berisi nilai yang salah dihitung 1 pelanggaran.

*(Pre-computation rule: The total reguler teaching load $B(m,k)$ assigned by a human MUST NOT exceed 39 slots per week per class. The system should reject the input and throw an error before running the GA if it exceeds this capacity).*

**2. Kendala Konflik Kelas (dengan Pengecualian Co-Teaching)**
Satu kelas tidak boleh dijadwalkan melakukan dua kegiatan sekaligus pada hari dan jam yang sama. Beberapa mata pelajaran seperti PABP dan Pilihan dapat diajarkan oleh lebih dari satu guru secara bersamaan kepada kelompok siswa yang berbeda dalam kelas yang sama (*Co-Teaching*). Untuk mata pelajaran ini, kondisi yang biasanya dianggap konflik kelas justru diizinkan jika mata pelajarannya sama.

Violation dihitung dengan mencari kombinasi $(k, t, h)$ yang ditempati lebih dari satu gen di luar pengecualian co-teaching.
$$v_2 = \bigl|\{(k,t,h) \mid \exists\, c_i, c_j \in C,\ i \neq j,\ k_i = k_j \wedge t_i = t_j \wedge h_i = h_j \wedge (m_i \notin M_{\text{co}} \vee m_j \notin M_{\text{co}} \vee m_i \neq m_j)\}\bigr|$$

**3. Kendala Konflik Guru**
Seorang guru tidak boleh mengajar di lebih dari satu kelas pada hari dan jam yang sama ($g \neq -1$).
$$v_3 = \bigl|\{(g,t,h) \mid g \neq -1 \wedge \exists\, c_i, c_j \in C,\ i \neq j,\ g_i = g_j \wedge t_i = t_j \wedge h_i = h_j\}\bigr|$$

**4. Kendala Beban Mengajar (Teaching Load - Implicit)**
*Note for Agent: This is already perfectly satisfied during Step 3 (Initial Population Generation) because genes are created strictly based on the `beban_mengajar` table and mutation only affects time/day. You can skip calculating $v_4$ in `fitness.py`.*

---
### Soft Constraint (Weight $w_n = 500$)

**SC-1. Penyebaran Mata Pelajaran yang Merata**
Mata pelajaran $m$ (selain `NULL`) pada kelas $k$ sebaiknya dijadwalkan minimal pada $\lceil B(m,k)/5 \rceil$ hari yang berbeda. Maksimal 5 slot per hari untuk satu mata pelajaran yang sama.
$$v_{\text{sc1}} = \sum_{m \in M \setminus \{-1\}}\sum_{k \in K} \max\!\left(0,\ \left\lceil\frac{B(m,k)}{5}\right\rceil - \bigl|\{ h \mid \exists\, c \in C,\ c.m=m \wedge c.k=k \wedge c.h=h \}\bigr|\right)$$
$$+\ \sum_{m \in M \setminus \{-1\}}\sum_{k \in K}\sum_{h \in H} \max\!\left(0,\ \bigl|\{ c \in C \mid c.m=m \wedge c.k=k \wedge c.h=h \}\bigr| - 5\right)$$

**SC-2. Kendala Kontiguitas Harian (Blok Pertemuan Mapel)**
Mata pelajaran $m$ (reguler, non-NULL) pada kelas $k$ sebaiknya dijadwalkan dalam satu blok waktu yang berurutan (kontigu/tandem) per harinya. Mapel tersebut tidak boleh terpecah menjadi beberapa segmen yang disela oleh mapel lain pada hari itu. Mengabaikan slot "Istirahat" sebagai penyela. 
Biarkan $E(m,k,h)$ menjadi jumlah kelompok kontigu (segmen terpisah) untuk mapel $m$, kelas $k$, hari $h$.
$$v_{\text{sc2}} = \sum_{m \notin \{\text{Upacara, Bersih-bersih, Istirahat, -1}\}} \sum_{k \in K} \sum_{h \in H} \max\!\left(0,\ E(m,k,h) - 1\right)$$

**SC-3. Kendala Beban Kerja Guru**
Menggabungkan dua aturan beban kerja guru:
- **Batas Harian (max 7 slot)**: $v_{\text{sc3a}} = \sum_{g \in G \setminus \{-1\}}\sum_{h \in H} \max\!\left(0,\ \bigl|\{ c \in C \mid c.g = g \wedge c.h = h \}\bigr| - 7\right)$
- **Min Mingguan PNS (min 24 slot)**: $v_{\text{sc3b}} = \sum_{g \in G_{\text{pns}}} \max\!\left(0,\ 24 - \bigl|\{ c \in C \mid c.g = g \}\bigr|\right)$
$$v_{\text{sc3}} = v_{\text{sc3a}} + v_{\text{sc3b}}$$

---
### Fungsi Penalti

- **Violation $v_n$** = jumlah kejadian pelanggaran pada constraint ke-$n$.
- **Penalti per constraint:** $p_n = v_n \times w_n$ ($w_n = 1000$ untuk HC, $500$ untuk SC).
- **Total penalti:** $p_{\text{total}} = \sum_{n} p_n$
- **Fungsi fitness:** $f(C) = \frac{1}{1 + p_{\text{total}}}$
