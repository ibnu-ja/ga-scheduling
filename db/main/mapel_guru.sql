create table mapel_guru
(
    id       INTEGER
        primary key,
    guru_id  INTEGER not null
        references guru,
    mapel_id INTEGER not null
        references mapel,
    unique (guru_id, mapel_id)
);

