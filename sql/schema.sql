-- Core schema for Global Patent Intelligence pipeline

DROP TABLE IF EXISTS relationships;
DROP TABLE IF EXISTS patents;
DROP TABLE IF EXISTS inventors;
DROP TABLE IF EXISTS companies;

CREATE TABLE patents (
    patent_id TEXT PRIMARY KEY,
    title TEXT,
    abstract TEXT,
    filing_date TEXT,
    year INTEGER
);

CREATE TABLE inventors (
    inventor_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT
);

CREATE TABLE companies (
    company_id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE relationships (
    patent_id TEXT NOT NULL,
    inventor_id TEXT NOT NULL,
    company_id TEXT NOT NULL,
    PRIMARY KEY (patent_id, inventor_id, company_id),
    FOREIGN KEY (patent_id) REFERENCES patents (patent_id),
    FOREIGN KEY (inventor_id) REFERENCES inventors (inventor_id),
    FOREIGN KEY (company_id) REFERENCES companies (company_id)
);

CREATE INDEX idx_patents_year ON patents(year);
CREATE INDEX idx_inventors_country ON inventors(country);
