
-- 1. WARDS
CREATE TABLE wards (
    ward_id       SERIAL PRIMARY KEY,
    ward_name     VARCHAR(100),
    zone          VARCHAR(50),
    area_sqkm     DECIMAL(6,2),
    population    INTEGER,
    households    INTEGER,
    population_category VARCHAR(20)        -- ← added by KNIME
);

-- 2. SMART CITY PROJECTS
CREATE TABLE smart_city_projects (
    project_id       SERIAL PRIMARY KEY,
    project_name     VARCHAR(200),
    category         VARCHAR(100),
    zone             VARCHAR(50),
    budget_cr        DECIMAL(10,2),
    spent_cr         DECIMAL(10,2),
    start_date       DATE,
    expected_end     DATE,
    actual_end       DATE,
    status           VARCHAR(50),
    budget_utilization DECIMAL(6,4),       -- ← added by KNIME
    budget_flag      VARCHAR(50),          -- ← added by KNIME
    project_health   VARCHAR(50)           -- ← added by KNIME
);

-- 3. HEALTHCARE
CREATE TABLE healthcare (
    facility_id        SERIAL PRIMARY KEY,
    ward_id            INTEGER REFERENCES wards(ward_id),
    facility_name      VARCHAR(200),
    facility_type      VARCHAR(50),
    beds               INTEGER,
    latitude           DECIMAL(9,6),
    longitude          DECIMAL(9,6),
    facility_size      VARCHAR(20),        -- ← added by KNIME
    facility_importance VARCHAR(20)        -- ← added by KNIME
);

-- 4. AIR QUALITY
CREATE TABLE air_quality (
    aqi_id         SERIAL PRIMARY KEY,
    station_name   VARCHAR(100),
    reading_date   DATE,
    pm25           DECIMAL(6,2),
    pm10           DECIMAL(6,2),
    no2            DECIMAL(6,2),
    so2            DECIMAL(6,2),
    aqi_value      INTEGER,
    aqi_category   VARCHAR(50),
    season         VARCHAR(20),            -- ← added by KNIME
    health_flag    VARCHAR(20),            -- ← added by KNIME
    month_num      INTEGER,                -- ← added by KNIME
    year_num       INTEGER                 -- ← added by KNIME
);

-- 5. LAKE QUALITY
CREATE TABLE lake_quality (
    lake_id            SERIAL PRIMARY KEY,
    lake_name          VARCHAR(100),
    sample_date        DATE,
    ph_value           DECIMAL(4,2),
    dissolved_oxygen   DECIMAL(5,2),
    bod                DECIMAL(5,2),
    turbidity          DECIMAL(6,2),
    coliform           INTEGER,
    quality_grade      VARCHAR(20),
    pollution_flag     VARCHAR(30),        -- ← added by KNIME
    season             VARCHAR(20),        -- ← added by KNIME
    month_num          INTEGER,            -- ← added by KNIME
    year_num           INTEGER             -- ← added by KNIME
);

-- 6. COMPLAINTS
CREATE TABLE complaints (
    complaint_id       SERIAL PRIMARY KEY,
    ward_id            INTEGER REFERENCES wards(ward_id),
    ward_name          VARCHAR(100),
    zone               VARCHAR(50),
    complaint_date     DATE,
    category           VARCHAR(100),
    status             VARCHAR(50),
    days_to_resolve    INTEGER,
    year               INTEGER,
    month              INTEGER,
    resolution_speed   VARCHAR(20),        -- ← added by KNIME
    complaint_priority VARCHAR(20)         -- ← added by KNIME
);