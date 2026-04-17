
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    roll_no VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    roll_no VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    status CHAR(1),
    check_in TIME,
    check_out TIME
);
