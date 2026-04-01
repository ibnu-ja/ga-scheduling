create table guru
(
    id     INTEGER
        primary key,
    kode   TEXT not null
        unique,
    nama   TEXT not null,
    status TEXT not null,
    check (status IN ('PNS', 'P3K', 'honorer'))
);

