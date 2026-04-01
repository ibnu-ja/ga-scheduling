create table chromosome_gene
(
    id            INTEGER
        primary key,
    chromosome_id INTEGER not null
        references chromosome
            on delete cascade,
    mapel_id      INTEGER not null
        references mapel,
    guru_id       INTEGER
        references guru,
    kelas_id      INTEGER not null
        references kelas,
    waktu_id      INTEGER not null
        references waktu,
    hari_id       INTEGER not null
        references hari
);

create index idx_guru_no_conflict
    on chromosome_gene (chromosome_id, guru_id, waktu_id, hari_id)
    where guru_id IS NOT NULL;

create index idx_kelas_no_conflict
    on chromosome_gene (chromosome_id, kelas_id, waktu_id, hari_id);

