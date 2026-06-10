#!/bin/bash

sudo apt-get update
sudo apt-get install -y build-essential python3-dev libpq-dev postgresql postgresql-contrib sysstat blktrace

sudo service postgresql start

pip3 install -r requirements.txt

sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '0123456789';"
sudo -u postgres psql -c "DROP DATABASE IF EXISTS mobility_sim;"
sudo -u postgres psql -c "CREATE DATABASE mobility_sim;"

sudo -u postgres psql -d mobility_sim -c "
CREATE TABLE passengers_kpi (
    passenger_id VARCHAR(255),
    scenario_info VARCHAR(255),
    psgrnum VARCHAR(255),
    dep_node VARCHAR(255),
    arr_node VARCHAR(255),
    calltime VARCHAR(255),
    boardingtime VARCHAR(255),
    shuttleid VARCHAR(255),
    arrivaltime VARCHAR(255),
    expectedwaitingtime VARCHAR(255),
    expectedarrivaltime VARCHAR(255),
    success VARCHAR(255),
    pathchanged VARCHAR(255),
    waitstarttime VARCHAR(255),
    increased_time VARCHAR(255),
    dep_node_expanded VARCHAR(255),
    PRIMARY KEY (passenger_id, scenario_info)
);

CREATE TABLE vehicle_kpi (
    id SERIAL PRIMARY KEY,
    scenario_info TEXT,
    currenttime TEXT,
    shuttle_id TEXT,
    shuttle_state TEXT,
    cur_dst TEXT,
    cur_node TEXT,
    cur_path TEXT,
    cur_psgr TEXT,
    cur_psgr_num TEXT
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
"
