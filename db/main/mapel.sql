create table mapel
(
    id            INTEGER
        primary key,
    kode          TEXT              not null
        unique,
    nama          TEXT,
    is_coteaching BOOLEAN default 0 not null
);

