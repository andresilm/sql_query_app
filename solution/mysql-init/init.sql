CREATE DATABASE IF NOT EXISTS product_sales;

USE product_sales;

CREATE TABLE IF NOT EXISTS product (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    week_day VARCHAR(20) NOT NULL,
    hour TIME NOT NULL,
    ticket_number INT NOT NULL,
    waiter VARCHAR(100) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    unitary_price DECIMAL(10, 2) NOT NULL,
    total DECIMAL(10, 2) NOT NULL
);
