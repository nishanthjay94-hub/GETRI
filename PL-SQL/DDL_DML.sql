DROP TABLE departments CASCADE CONSTRAINTS;
DROP TABLE employees CASCADE CONSTRAINTS;

-- DDL 
CREATE TABLE departments (
    department_id NUMBER PRIMARY KEY,
    department_name VARCHAR2(50),
    location VARCHAR2(50)
);

-- DML for department
INSERT INTO departments
VALUES (10, 'IT', 'Chennai');

INSERT INTO departments
VALUES (20, 'HR', 'Bangalore');

INSERT INTO departments
VALUES (30, 'Finance', 'Mumbai');

INSERT INTO departments
VALUES (40, 'Sales', 'Delhi');

COMMIT;

-- DDL for Employees

CREATE TABLE employees (
    employee_id NUMBER PRIMARY KEY,
    employee_name VARCHAR2(100),
    department_id NUMBER,
    job_title VARCHAR2(50),
    salary NUMBER(10,2),
    joining_date DATE,
    email VARCHAR2(100),
    status VARCHAR2(20)
);

-- DML for employees

INSERT INTO employees
VALUES (101, 'Arun', 10, 'Developer', 60000,
        DATE '2023-01-15', 'arun@company.com', 'ACTIVE');

INSERT INTO employees
VALUES (102, 'Priya', 10, 'Senior Developer', 85000,
        DATE '2022-03-20', 'priya@company.com', 'ACTIVE');

INSERT INTO employees
VALUES (103, 'Rahul', 20, 'HR Executive', 45000,
        DATE '2024-01-10', 'rahul@company.com', 'ACTIVE');

INSERT INTO employees
VALUES (104, 'Divya', 30, 'Finance Analyst', 55000,
        DATE '2023-06-12', 'divya@company.com', 'ACTIVE');

INSERT INTO employees
VALUES (105, 'Karthik', 10, 'Tech Lead', 110000,
        DATE '2020-08-01', 'karthik@company.com', 'ACTIVE');

INSERT INTO employees
VALUES (106, 'Sneha', 40, 'Sales Executive', 50000,
        DATE '2024-02-15', 'sneha@company.com', 'ACTIVE');

INSERT INTO employees
VALUES (107, 'Vijay', 20, 'HR Manager', 90000,
        DATE '2021-04-10', 'vijay@company.com', 'ACTIVE');

COMMIT;


