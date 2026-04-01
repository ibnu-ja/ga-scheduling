create table beban_mengajar
(
    id           INTEGER
        primary key,
    mapel_id     INTEGER not null
        references mapel,
    kelas_id     INTEGER not null
        references kelas,
    jumlah_waktu INTEGER not null,
    unique (mapel_id, kelas_id)
);

