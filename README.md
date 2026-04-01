# GA SCHEDULING

this project is vibe coded using perplexity and junie

## Model Matematika

Himpunan: 

- $M$: semua mapel termasuk Upacara, Bersih-bersih, dan Istirahat
- $G$: semua guru
- $K$: semua kelas
- $T$: jam pelajaran, $\{1,2,\dots,11\}$
- $H$: $\{\text{Senin, Selasa, Rabu, Kamis, Jumat}\}, \quad |H| = 5.$

Gen adalah satu kegiatan terjadwal, berisi lima informasi sekaligus:
$$c = (m,\ g,\ k,\ t,\ h)$$
Artinya: mapel $m$, diajarkan oleh guru $g$, untuk kelas $k$, di slot waktu $t$, pada hari $h$. Jika kegiatan tidak memiliki guru (seperti Upacara), maka $g$ diisi kosong atau `NULL`.

Kromosom adalah satu jadwal mingguan penuh, yaitu kumpulan semua gen:
$$C = \{c_1,\ c_2,\ \dots,\ c_n\}$$

Fungsi beban mengajar $B$ adalah tabel jatah pertemuan. Untuk setiap pasangan mapel dan kelas, $B$ menyimpan berapa kali mapel tersebut harus muncul dalam satu minggu. Contoh: $B(\text{Matematika},\ \text{kelas XII PPLG}) = 4$ artinya Matematika harus muncul 4 kali seminggu di kelas XII PPLG. Secara formal:
$$B : M \times K \rightarrow \mathbb{Z}_{\ge 0}$$
Dibaca: fungsi $B$ menerima input pasangan $(m, k)$ dan menghasilkan bilangan bulat nol atau lebih. Nilai $B$ adalah input dari manusia, kecuali untuk mapel khusus yang sudah ditetapkan:

| Mapel | Nilai $B$ untuk semua kelas |
|---|---|
| Upacara | $B(\text{Upacara},\ k) = 1$ |
| Bersih-bersih | $B(\text{Bersih-bersih},\ k) = 1$ |
| Istirahat | $B(\text{Istirahat},\ k) = 2 \times 5 = 10$ |

Istirahat bernilai 10 karena terjadi 2 kali setiap hari (slot ke-5 dan ke-8) selama 5 hari.

---

# Hard Constraint

### 1. Kendala Slot Waktu Tetap (Fixed Time Slots)

Beberapa slot waktu sudah ditentukan isinya sejak awal dan tidak boleh diubah oleh GA. Senin jam pertama selalu Upacara, Kamis jam pertama selalu Bersih-bersih, dan jam ke-5 serta ke-8 di hari mana pun selalu Istirahat — semuanya tanpa guru, untuk semua kelas.

Violation dihitung dengan mencari gen yang menempati slot-slot tersebut tetapi berisi mata pelajaran yang salah. Setiap satu gen yang salah dihitung satu pelanggaran.

Jika hari $h$ adalah Senin dan waktu $t =1$, maka gen harus memiliki mata pelajaran $m = \text{Upacara}$ dan guru $g = \text{NULL}$, untuk semua kelas $k$.
Jika hari $h$ adalah Kamis dan waktu $t = 1$, maka gen harus memiliki mata pelajaran $m = \text{Bersih-bersih}$ dan guru $g = \text{NULL}$, untuk semua kelas $k$.
Jika waktu $t \in \{5,8\}$ pada hari apa pun $h$, maka gen harus memiliki mata pelajaran
$$m = \text{Istirahat}, \quad g = \text{NULL}$$
untuk semua kelas $k$.

$$v_1 = \bigl|\{ c \in C \mid h = \text{Senin} \wedge t = 1 \wedge m \neq \text{Upacara} \}\bigr|$$
$$+\ \bigl|\{ c \in C \mid h = \text{Kamis} \wedge t = 1 \wedge m \neq \text{Bersih-bersih} \}\bigr|$$
$$+\ \bigl|\{ c \in C \mid t \in \{5, 8\} \wedge m \neq \text{Istirahat} \}\bigr|$$

---

### 2. Pengecualian Co-Teaching

Beberapa mata pelajaran seperti PABP dan Pilihan dapat diajarkan oleh lebih dari satu guru secara bersamaan kepada kelompok siswa yang berbeda dalam kelas yang sama. Untuk mata pelajaran ini, kondisi yang biasanya dianggap konflik kelas justru diizinkan.

Hard constrain ke-2 ini tidak menghasilkan penalti sendiri. Ia hanya mendefinisikan himpunan pengecualian yang dipakai oleh hard constrain ke-3. Seluruh mata pelajaran yang masuk ke dalam himpunan ini dikecualikan dari pengecekan konflik kelas.

Jika mata pelajaran $m$ termasuk dalam
$$M_{\text{co}} = \{\text{PABP},\ \text{Pilihan}\}$$
maka beberapa gen dengan guru $g$ yang berbeda diperbolehkan memiliki kombinasi $(m, k, t, h)$ yang sama. Dengan demikian, kendala konflik kelas pada hard constrain ke-3 tidak berlaku untuk mata pelajaran tersebut.

---

### 3. Kendala Konflik Kelas

Satu kelas tidak boleh dijadwalkan melakukan dua kegiatan sekaligus pada hari dan jam yang sama. Pengecualian berlaku untuk mata pelajaran co-teaching yang sudah didefinisikan di hard constrain ke-2.

Violation dihitung dengan mencari kombinasi $(k, t, h)$ yang ditempati lebih dari satu gen di luar pengecualian co-teaching. Setiap kombinasi yang berisi lebih dari satu gen dihitung satu pelanggaran.

Pada kombinasi hari $h$, waktu $t$, dan kelas $k$ yang sama, hanya diperbolehkan terdapat satu gen, kecuali jika mata pelajaran $m \in M_{\text{co}}$.

$$v_3 = \bigl|\{(k,t,h) \mid \exists\, c_i, c_j \in C,\ i \neq j,\ k_i = k_j \wedge t_i = t_j \wedge h_i = h_j \wedge (m_i \notin M_{\text{co}} \vee m_j \notin M_{\text{co}})\}\bigr|$$

---

### 4. Kendala Konflik Guru

Seorang guru tidak boleh mengajar di lebih dari satu kelas pada hari dan jam yang sama. Kendala ini hanya berlaku untuk kegiatan yang memiliki guru — kegiatan tanpa guru seperti Upacara, Bersih-bersih, dan Istirahat sudah ditangani oleh hard constrain ke-1 dan tidak dihitung di sini.

Violation dihitung dengan mencari kombinasi $(g, t, h)$ yang muncul lebih dari satu kali dalam kromosom. Setiap kombinasi yang muncul lebih dari satu kali dihitung satu pelanggaran.

Seorang guru tidak boleh mengajar di lebih dari satu kelas pada kombinasi hari $h$ dan waktu $t$ yang sama. Kendala ini hanya dievaluasi jika $g \neq \text{NULL}$.

$$v_4 = \bigl|\{(g,t,h) \mid g \neq \text{NULL} \wedge \exists\, c_i, c_j \in C,\ i \neq j,\ g_i = g_j \wedge t_i = t_j \wedge h_i = h_j\}\bigr|$$

---

### 5. Kendala Beban Mengajar (Teaching Load)

Setiap mata pelajaran pada setiap kelas memiliki jatah kemunculan per minggu. Jumlah kemunculan aktual dalam kromosom harus tepat sama dengan jatah tersebut, tidak lebih dan tidak kurang. Berlaku untuk semua mata pelajaran termasuk Upacara, Bersih-bersih, dan Istirahat.

Violation dihitung dengan menjumlahkan selisih antara kemunculan aktual dan jatah $B(m,k)$ untuk setiap pasangan mata pelajaran dan kelas. Nilai absolut memastikan kelebihan maupun kekurangan sama-sama dihitung sebagai pelanggaran.

Setiap mata pelajaran $m$ pada kelas $k$ memiliki jatah kemunculan $B(m,k)$ per minggu. Jumlah gen dengan pasangan $(m,k)$ dalam satu kromosom harus memenuhi $|\{ c \mid (m,k) \}| = B(m,k)$, dengan nilai tetap untuk mata pelajaran khusus:
$$B(\text{Upacara},k) = 1, \quad B(\text{Bersih-bersih},k) = 1, \quad B(\text{Istirahat},k) = 10 \quad \forall\, k \in K$$

$$v_5 = \sum_{m \in M} \sum_{k \in K} \left| \left|\{ c \in C \mid c.m = m \wedge c.k = k \}\right| - B(m,k) \right|$$

---

# Soft Constraint

### 1. Penyebaran Mata Pelajaran yang Merata

Mata pelajaran dengan beban banyak sebaiknya tidak menumpuk di satu hari saja. Penyebaran ke beberapa hari membuat jadwal lebih seimbang dan tidak memberatkan siswa di hari tertentu. Batas maksimum 5 slot per hari untuk satu mata pelajaran yang sama berlaku agar tidak terlalu padat.

Violation dihitung dalam dua bagian. Bagian pertama menghitung kekurangan jumlah hari penyebaran dari minimum yang seharusnya. Bagian kedua menghitung kelebihan slot dalam satu hari yang melampaui 5.

Mata pelajaran $m$ pada kelas $k$ sebaiknya dijadwalkan minimal pada $\lceil B(m,k)/5 \rceil$ hari yang berbeda. Contoh: beban 11 → minimal $\lceil 11/5 \rceil = 3$ hari, pembagian 5,3,3 atau 4,4,3 keduanya oke. Beban 3 → cukup 1 hari.

$$v_{\text{sc1}} = \sum_{m \in M}\sum_{k \in K} \max\!\left(0,\ \left\lceil\frac{B(m,k)}{5}\right\rceil - \bigl|\{ h \mid \exists\, c \in C,\ c.m=m \wedge c.k=k \wedge c.h=h \}\bigr|\right)$$
$$+\ \sum_{m \in M}\sum_{k \in K}\sum_{h \in H} \max\!\left(0,\ \bigl|\{ c \in C \mid c.m=m \wedge c.k=k \wedge c.h=h \}\bigr| - 5\right)$$

---

### 2. Penyebaran Jam Mengajar Guru
#### a. Batas Jam Mengajar Harian Guru

Guru sebaiknya tidak mengajar terlalu banyak dalam satu hari meskipun secara total mingguan masih dalam batas wajar. Struktur slot sudah menjamin maksimal 4 slot berturut-turut secara alami karena Istirahat di jam ke-5 dan ke-8, sehingga tidak perlu constraint tambahan untuk slot berturut-turut.

Violation dihitung per slot kelebihan di atas 7 pada hari yang sama. Setiap satu slot yang melebihi batas dihitung satu pelanggaran.

Jumlah slot mengajar guru $g$ pada hari $h$ sebaiknya tidak melebihi 7 slot.

$$v_{\text{sc2a}} = \sum_{g \in G}\sum_{h \in H} \max\!\left(0,\ \bigl|\{ c \in C \mid c.g = g \wedge c.h = h \}\bigr| - 7\right)$$

---

#### b. Minimum Jam Mengajar Mingguan Guru PNS/P3K

Guru berstatus PNS atau P3K memiliki kewajiban mengajar minimal 24 jam per minggu sesuai ketentuan. Jika dari hasil penjadwalan jumlah slot yang tersedia memang tidak mencukupi 24, kendala ini boleh tidak terpenuhi dan kekurangannya digantikan dengan tugas di luar mengajar. Guru honorer tidak memiliki batas minimum ini. Penalti bersifat ringan, hanya sebagai sinyal untuk dicek manual.

Violation dihitung per slot kekurangan di bawah 24 untuk setiap guru PNS atau P3K. Setiap satu slot yang kurang dari batas minimum dihitung satu pelanggaran.

Didefinisikan terlebih dahulu himpunan guru PNS dan P3K:
$$G_{\text{pns}} = \{ g \in G \mid \text{status}(g) \in \{\text{PNS},\ \text{P3K}\} \}$$

Guru $g \in G_{\text{pns}}$ sebaiknya memiliki total slot mengajar minimal 24 dalam satu minggu.

$$v_{\text{sc2b}} = \sum_{g \in G_{\text{pns}}} \max\!\left(0,\ 24 - \bigl|\{ c \in C \mid c.g = g \}\bigr|\right)$$

---


## 3.4 Fungsi Penalti

GA mengevaluasi setiap kromosom $C$ dengan menghitung seberapa banyak aturan yang dilanggar. Semakin banyak pelanggaran, semakin buruk kromosom tersebut.

**Violation $v_n$** = jumlah pelanggaran yang ditemukan pada constraint ke-$n$ dalam kromosom $C$. Dihitung per kejadian, bukan biner — artinya jika ada 3 konflik guru, maka $v = 3$, bukan $v = 1$.

**Penalti per constraint:**
$$p_n = v_n \times w_n$$
Artinya: jumlah pelanggaran dikali bobot. Bobot $w_n = 1000$ untuk hard constraint (wajib dipenuhi), dan $w_n = 500$ untuk soft constraint (sebaiknya dipenuhi).

**Total penalti** adalah jumlah semua penalti dari semua constraint:
$$p_{\text{total}} = \sum_{n} p_n$$

**Fungsi fitness** mengubah total penalti menjadi nilai kualitas kromosom antara 0 dan 1:
$$f(C) = \frac{1}{1 + p_{\text{total}}}$$
Semakin kecil $p_{\text{total}}$, semakin mendekati 1 nilai fitness-nya. Kromosom sempurna (tidak ada pelanggaran sama sekali) menghasilkan $p_{\text{total}} = 0$ sehingga $f(C) = 1$.

---

## SQLite DDL Schema

Tersedia di `db/main/*.sql`

---

## Kardinalitas Relasi

| Relasi | Kardinalitas | Keterangan |
|---|---|---|
| `mapel` → `beban_mengajar` | 1 : N | Satu mapel punya beban di banyak kelas |
| `kelas` → `beban_mengajar` | 1 : N | Satu kelas punya beban banyak mapel |
| `mapel` + `kelas` → `beban_mengajar` | M : N via `beban_mengajar` | UNIQUE memaksa tepat satu nilai $B$ per pasangan |
| `chromosome` → `chromosome_gene` | 1 : N | Satu kromosom terdiri dari banyak gen |
| `mapel` → `chromosome_gene` | 1 : N | Satu mapel bisa muncul di banyak gen |
| `guru` → `chromosome_gene` | 1 : N nullable | Satu guru bisa mengajar di banyak gen; NULL untuk aktivitas tanpa guru |
| `kelas` → `chromosome_gene` | 1 : N | Satu kelas memiliki banyak gen dalam satu kromosom |
| `waktu` → `chromosome_gene` | 1 : N | Satu slot waktu dipakai banyak gen |
| `hari` → `chromosome_gene` | 1 : N | Satu hari dipakai banyak gen |
| `hari` → `slot_tetap` | 1 : N nullable | NULL berarti berlaku semua hari |
| `waktu` → `slot_tetap` | 1 : N | Satu slot waktu bisa punya aturan tetap |
| `mapel` → `slot_tetap` | 1 : N | Satu mapel bisa terikat ke beberapa slot tetap |
