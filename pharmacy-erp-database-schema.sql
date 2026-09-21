-- ===================================================================
-- PHARMSECURE ERP - COMPLETE DATABASE SCHEMA
-- Production-Grade Multi-Branch Pharmacy Management System
-- ===================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Companies
CREATE TABLE companies (
    company_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(255) NOT NULL UNIQUE,
    registration_number VARCHAR(50),
    tax_id VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    physical_address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    currency_code VARCHAR(3) DEFAULT 'GHS',
    financial_year_start INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Branches
CREATE TABLE branches (
    branch_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    branch_code VARCHAR(10) NOT NULL UNIQUE,
    branch_name VARCHAR(255) NOT NULL,
    branch_type VARCHAR(50),
    manager_name VARCHAR(255),
    email VARCHAR(100),
    phone VARCHAR(20),
    physical_address TEXT,
    city VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Roles
CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    role_name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    branch_id UUID REFERENCES branches(branch_id),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(100),
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role_id UUID REFERENCES roles(role_id),
    staff_id UUID,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories
CREATE TABLE categories (
    category_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    category_code VARCHAR(20) NOT NULL,
    category_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products
CREATE TABLE products (
    product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    sku VARCHAR(50) NOT NULL UNIQUE,
    product_name VARCHAR(255) NOT NULL,
    generic_name VARCHAR(255),
    category_id UUID REFERENCES categories(category_id),
    manufacturer VARCHAR(255),
    strength VARCHAR(100),
    unit_type VARCHAR(50),
    units_per_pack INT DEFAULT 1,
    description TEXT,
    cost_price DECIMAL(10,2),
    retail_price DECIMAL(10,2),
    wholesale_price DECIMAL(10,2),
    vat_rate DECIMAL(5,2) DEFAULT 0,
    wht_rate DECIMAL(5,2) DEFAULT 0,
    registration_number VARCHAR(50),
    expiry_date DATE,
    requires_prescription BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_counterfeit_prone BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory Batches
CREATE TABLE inventory_batches (
    batch_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(product_id),
    branch_id UUID NOT NULL REFERENCES branches(branch_id),
    batch_number VARCHAR(100) NOT NULL,
    serial_number VARCHAR(255) UNIQUE,
    manufacturing_date DATE,
    expiry_date DATE NOT NULL,
    quantity_received INT DEFAULT 0,
    quantity_on_hand INT DEFAULT 0,
    quantity_reserved INT DEFAULT 0,
    quantity_expired INT DEFAULT 0,
    cost_price_per_unit DECIMAL(10,2),
    is_verified BOOLEAN DEFAULT FALSE,
    verification_timestamp TIMESTAMP,
    verification_result VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, branch_id, batch_number)
);

-- Stock Transfers
CREATE TABLE stock_transfers (
    transfer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    from_branch_id UUID NOT NULL REFERENCES branches(branch_id),
    to_branch_id UUID NOT NULL REFERENCES branches(branch_id),
    transfer_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(50) DEFAULT 'PENDING',
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock Transfer Details
CREATE TABLE stock_transfer_details (
    transfer_detail_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transfer_id UUID NOT NULL REFERENCES stock_transfers(transfer_id),
    batch_id UUID NOT NULL REFERENCES inventory_batches(batch_id),
    quantity_sent INT NOT NULL,
    quantity_received INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock Takes
CREATE TABLE stock_takes (
    stock_take_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    branch_id UUID NOT NULL REFERENCES branches(branch_id),
    stock_take_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(50) DEFAULT 'IN_PROGRESS',
    counted_by UUID REFERENCES users(user_id),
    verified_by UUID REFERENCES users(user_id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Stock Take Details
CREATE TABLE stock_take_details (
    stock_take_detail_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_take_id UUID NOT NULL REFERENCES stock_takes(stock_take_id),
    batch_id UUID NOT NULL REFERENCES inventory_batches(batch_id),
    system_quantity INT,
    physical_quantity INT,
    variance INT,
    variance_reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers
CREATE TABLE suppliers (
    supplier_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    supplier_code VARCHAR(20) NOT NULL UNIQUE,
    supplier_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(100),
    phone VARCHAR(20),
    physical_address TEXT,
    city VARCHAR(100),
    tax_id VARCHAR(50),
    payment_terms VARCHAR(50),
    credit_limit DECIMAL(15,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Purchase Orders
CREATE TABLE purchase_orders (
    po_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    branch_id UUID NOT NULL REFERENCES branches(branch_id),
    supplier_id UUID NOT NULL REFERENCES suppliers(supplier_id),
    po_number VARCHAR(50) NOT NULL UNIQUE,
    po_date DATE DEFAULT CURRENT_DATE,
    expected_delivery_date DATE,
    status VARCHAR(50) DEFAULT 'DRAFT',
    subtotal DECIMAL(15,2) DEFAULT 0,
    vat_amount DECIMAL(15,2) DEFAULT 0,
    wht_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    created_by UUID REFERENCES users(user_id),
    approved_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PO Details
CREATE TABLE po_details (
    po_detail_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    po_id UUID NOT NULL REFERENCES purchase_orders(po_id),
    product_id UUID NOT NULL REFERENCES products(product_id),
    quantity_ordered INT NOT NULL,
    quantity_received INT DEFAULT 0,
    unit_cost DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers
CREATE TABLE customers (
    customer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    branch_id UUID NOT NULL REFERENCES branches(branch_id),
    customer_code VARCHAR(20),
    customer_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    customer_type VARCHAR(50),
    credit_limit DECIMAL(15,2) DEFAULT 0,
    credit_balance DECIMAL(15,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sales (POS)
CREATE TABLE sales (
    sale_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    branch_id UUID NOT NULL REFERENCES branches(branch_id),
    transaction_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id UUID REFERENCES customers(customer_id),
    sale_date DATE DEFAULT CURRENT_DATE,
    sale_time TIME DEFAULT CURRENT_TIME,
    sold_by UUID REFERENCES users(user_id),
    subtotal DECIMAL(15,2) DEFAULT 0,
    vat_amount DECIMAL(15,2) DEFAULT 0,
    wht_amount DECIMAL(15,2) DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,
    payment_method VARCHAR(50),
    payment_status VARCHAR(50) DEFAULT 'PAID',
    notes TEXT,
    is_voided BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sale Details
CREATE TABLE sale_details (
    sale_detail_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sale_id UUID NOT NULL REFERENCES sales(sale_id),
    batch_id UUID NOT NULL REFERENCES inventory_batches(batch_id),
    product_id UUID NOT NULL REFERENCES products(product_id),
    quantity_sold INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    vat_rate DECIMAL(5,2),
    line_total DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Invoices
CREATE TABLE customer_invoices (
    invoice_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sale_id UUID REFERENCES sales(sale_id),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    invoice_date DATE DEFAULT CURRENT_DATE,
    due_date DATE,
    total_amount DECIMAL(15,2) NOT NULL,
    amount_paid DECIMAL(15,2) DEFAULT 0,
    amount_due DECIMAL(15,2),
    status VARCHAR(50) DEFAULT 'OUTSTANDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Credit Payments
CREATE TABLE credit_payments (
    payment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES customer_invoices(invoice_id),
    payment_date DATE DEFAULT CURRENT_DATE,
    payment_amount DECIMAL(15,2) NOT NULL,
    payment_method VARCHAR(50),
    reference_number VARCHAR(100),
    notes TEXT,
    recorded_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Staff
CREATE TABLE staff (
    staff_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    branch_id UUID REFERENCES branches(branch_id),
    staff_code VARCHAR(20) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    position VARCHAR(100),
    employment_type VARCHAR(50),
    start_date DATE,
    end_date DATE,
    base_salary DECIMAL(10,2),
    allowances DECIMAL(10,2) DEFAULT 0,
    deductions DECIMAL(10,2) DEFAULT 0,
    commission_rate DECIMAL(5,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payroll
CREATE TABLE payroll (
    payroll_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    staff_id UUID NOT NULL REFERENCES staff(staff_id),
    payroll_month DATE,
    pay_date DATE,
    status VARCHAR(50) DEFAULT 'DRAFT',
    base_salary DECIMAL(10,2) DEFAULT 0,
    allowances DECIMAL(10,2) DEFAULT 0,
    commission_earned DECIMAL(10,2) DEFAULT 0,
    gross_salary DECIMAL(15,2),
    tax_deduction DECIMAL(10,2) DEFAULT 0,
    ssnit_employee DECIMAL(10,2) DEFAULT 0,
    other_deductions DECIMAL(10,2) DEFAULT 0,
    total_deductions DECIMAL(15,2),
    net_salary DECIMAL(15,2),
    approved_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Staff Commission
CREATE TABLE staff_commissions (
    commission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    staff_id UUID NOT NULL REFERENCES staff(staff_id),
    payroll_id UUID REFERENCES payroll(payroll_id),
    sale_id UUID REFERENCES sales(sale_id),
    commission_date DATE DEFAULT CURRENT_DATE,
    sale_amount DECIMAL(15,2),
    commission_rate DECIMAL(5,2),
    commission_amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chart of Accounts
CREATE TABLE accounts (
    account_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    account_code VARCHAR(20) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Journal Entries
CREATE TABLE journal_entries (
    journal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    entry_date DATE DEFAULT CURRENT_DATE,
    description TEXT,
    created_by UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Journal Details
CREATE TABLE journal_details (
    detail_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    journal_id UUID NOT NULL REFERENCES journal_entries(journal_id),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily Sales Summary
CREATE TABLE daily_sales_summary (
    summary_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    branch_id UUID NOT NULL REFERENCES branches(branch_id),
    summary_date DATE DEFAULT CURRENT_DATE,
    total_sales_count INT DEFAULT 0,
    total_sales_amount DECIMAL(15,2) DEFAULT 0,
    cash_sales DECIMAL(15,2) DEFAULT 0,
    credit_sales DECIMAL(15,2) DEFAULT 0,
    standard_rate_sales DECIMAL(15,2) DEFAULT 0,
    reduced_rate_sales DECIMAL(15,2) DEFAULT 0,
    exempt_sales DECIMAL(15,2) DEFAULT 0,
    total_vat DECIMAL(15,2) DEFAULT 0,
    total_wht DECIMAL(15,2) DEFAULT 0,
    net_sales DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Monthly Summary
CREATE TABLE monthly_summary (
    summary_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    branch_id UUID REFERENCES branches(branch_id),
    summary_month DATE,
    total_revenue DECIMAL(15,2) DEFAULT 0,
    cost_of_goods_sold DECIMAL(15,2) DEFAULT 0,
    gross_profit DECIMAL(15,2),
    staff_salaries DECIMAL(15,2) DEFAULT 0,
    operating_expenses DECIMAL(15,2) DEFAULT 0,
    total_expenses DECIMAL(15,2),
    vat_collected DECIMAL(15,2) DEFAULT 0,
    wht_paid DECIMAL(15,2) DEFAULT 0,
    tax_payable DECIMAL(15,2),
    net_profit DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Logs
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(company_id),
    user_id UUID REFERENCES users(user_id),
    entity_type VARCHAR(100),
    entity_id UUID,
    action VARCHAR(50),
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_branches_company ON branches(company_id);
CREATE INDEX idx_products_company ON products(company_id);
CREATE INDEX idx_inventory_batches_branch ON inventory_batches(branch_id);
CREATE INDEX idx_inventory_batches_product ON inventory_batches(product_id);
CREATE INDEX idx_inventory_batches_expiry ON inventory_batches(expiry_date);
CREATE INDEX idx_sales_branch ON sales(branch_id);
CREATE INDEX idx_sales_date ON sales(sale_date);
CREATE INDEX idx_sales_customer ON sales(customer_id);
CREATE INDEX idx_sale_details_sale ON sale_details(sale_id);
CREATE INDEX idx_po_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_po_status ON purchase_orders(status);
CREATE INDEX idx_payroll_staff ON payroll(staff_id);
CREATE INDEX idx_payroll_month ON payroll(payroll_month);
CREATE INDEX idx_daily_summary_date ON daily_sales_summary(summary_date);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);

