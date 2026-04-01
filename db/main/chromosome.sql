create table chromosome
(
    id       INTEGER
        primary key,
    generasi INTEGER default 0       not null,
    fitness  REAL,
    status   TEXT    default 'aktif' not null,
    check (status IN ('aktif', 'arsip'))
);

