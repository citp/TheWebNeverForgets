PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE canvas ( 
    id            INTEGER PRIMARY KEY,
    visit_id      INTEGER,
    page_url      TEXT,
    script_url    TEXT,
    script_line   INTEGER,
    event_type    TEXT,
    event_time    INTEGER,
    event_meta_id INTEGER 
);
CREATE TABLE metadata ( 
    id         INTEGER PRIMARY KEY,
    event_type TEXT,
    value      TEXT,
    hash       TEXT 
);
ANALYZE sqlite_master;
CREATE TABLE visit (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,
    start_time TEXT,
    rank INT,
    duration INTEGER
, incomplete INTEGER   DEFAULT (1));
CREATE TABLE cookies ( 
    id           INTEGER PRIMARY KEY,
    visit_id     INTEGER,
    page_url     TEXT ,
    domain       TEXT,
    name         TEXT,
    value        TEXT,
    host         TEXT,
    path         TEXT,
    expiry       INTEGER,
    accessed     INTEGER,
    creationTime INTEGER,
    isSecure     INTEGER,
    isHttpOnly   INTEGER    
);
CREATE TABLE indexeddb (
    id INTEGER PRIMARY KEY,
    visit_id INTEGER,
    filename TEXT,
    db_name TEXT,
    object_store_id INTEGER NOT NULL,
    key_value BLOB DEFAULT ('NULL'),
    data BLOB NOT NULL,
    key_txt TEXT,
    data_txt TEXT
);
CREATE TABLE localstorage (
    id INTEGER PRIMARY KEY,
    visit_id INTEGER,
    page_url TEXT,
    scope TEXT,
    KEY TEXT,
    value TEXT
);
CREATE TABLE flash_cookies(
    id INTEGER PRIMARY KEY,
    visit_id INTEGER,
    page_url TEXT,
    domain TEXT,
    filename TEXT,
    local_path TEXT,
    key TEXT,
    content TEXT,
    mode INTEGER
);
CREATE TABLE cache (
    id            INTEGER PRIMARY KEY,
    visit_id INTEGER,
    page_url TEXT,
     body BLOB,
    hash TEXT,
    expiry TEXT,
    cache_control TEXT,
    etag TEXT,
    url TEXT NOT NULL
);
CREATE TABLE resp_headers ( 
    id           INTEGER PRIMARY KEY,    
    visit_id     INTEGER,
    msg_id INTEGER,
    name TEXT,
    value TEXT
);
CREATE TABLE req_headers ( 
    id           INTEGER PRIMARY KEY,    
    visit_id     INTEGER,
    msg_id INTEGER,
    name TEXT,
    value TEXT
);
CREATE TABLE http_msgs (
    id INTEGER PRIMARY KEY,
    visit_id INTEGER,
    page_url TEXT,
    req_url TEXT,
    method TEXT,
    referer TEXT
);
CREATE INDEX idx_canvas ON canvas ( 
    visit_id 
);
CREATE INDEX idx_metadata ON metadata ( 
    hash 
);
COMMIT;
