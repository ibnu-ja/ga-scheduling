create table slot_tetap
(
    id       INTEGER
        primary key,
    hari_id  INTEGER
        references hari,
    waktu_id INTEGER not null
        references waktu,
    mapel_id INTEGER not null
        references mapel
);

