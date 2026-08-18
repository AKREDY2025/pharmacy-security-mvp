/**
 * Pharmacy ERP Phase 3 - React Components
 * Customer Credit Management, Invoices, Payments, Financial Reports
 * 
 * Usage:
 * 1. Copy these components to: /home/claude/pharmacy_frontend/src/pages/
 * 2. Update imports in App.jsx
 * 3. npm start
 */

// ============================================================================
// 1. CUSTOMER CREDIT PAGE (CustomerCreditPage.jsx)
// ============================================================================

import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

export function CustomerCreditPage() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_code: '',
    credit_limit: 0,
    phone: '',
    email: ''
  });

  // Fetch customers on mount
  useEffect(() => {
    fetchCustomers();
  }, []);

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/customers`);
      setCustomers(Array.isArray(response.data) ? response.data : []);
      setError(null);
    } catch (err) {
      setError('Error loading customers: ' + err.message);
      setCustomers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCustomer = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/customers`, formData);
      setFormData({
        customer_name: '',
        customer_code: '',
        credit_limit: 0,
        phone: '',
        email: ''
      });
      setShowForm(false);
      fetchCustomers(); // Refresh list
    } catch (err) {
      alert('Error creating customer: ' + err.message);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  if (loading) return <div style={{ padding: '20px' }}>Loading customers...</div>;

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1>Customer Credit Management</h1>
        <button 
          onClick={() => setShowForm(!showForm)}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          {showForm ? 'Cancel' : 'Add New Customer'}
        </button>
      </div>

      {error && (
        <div style={{
          padding: '10px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleCreateCustomer} style={{
          backgroundColor: '#f5f5f5',
          padding: '15px',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          <div style={{ marginBottom: '10px' }}>
            <label>Customer Name:</label>
            <input
              type="text"
              name="customer_name"
              value={formData.customer_name}
              onChange={handleInputChange}
              required
              style={{ width: '100%', padding: '8px' }}
            />
          </div>

          <div style={{ marginBottom: '10px' }}>
            <label>Customer Code:</label>
            <input
              type="text"
              name="customer_code"
              value={formData.customer_code}
              onChange={handleInputChange}
              required
              style={{ width: '100%', padding: '8px' }}
            />
          </div>

          <div style={{ marginBottom: '10px' }}>
            <label>Credit Limit (GHS):</label>
            <input
              type="number"
              name="credit_limit"
              value={formData.credit_limit}
              onChange={handleInputChange}
              step="0.01"
              required
              style={{ width: '100%', padding: '8px' }}
            />
          </div>

          <div style={{ marginBottom: '10px' }}>
            <label>Phone:</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              style={{ width: '100%', padding: '8px' }}
            />
          </div>

          <div style={{ marginBottom: '10px' }}>
            <label>Email:</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              style={{ width: '100%', padding: '8px' }}
            />
          </div>

          <button 
            type="submit"
            style={{
              padding: '10px 20px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Create Customer
          </button>
        </form>
      )}

      <div style={{ marginTop: '20px' }}>
        <h2>Customers ({customers.length})</h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: '15px'
        }}>
          {customers.map(customer => (
            <div
              key={customer.customer_id}
              style={{
                border: '1px solid #ddd',
                borderRadius: '4px',
                padding: '15px',
                backgroundColor: '#fff'
              }}
            >
              <h3>{customer.customer_name}</h3>
              <p><strong>Code:</strong> {customer.customer_code}</p>
              <p><strong>Credit Limit:</strong> GHS {Number(customer.credit_limit || 0).toFixed(2)}</p>
              <p><strong>Balance:</strong> GHS {Number(customer.credit_balance || 0).toFixed(2)}</p>
              <p><strong>Status:</strong> <span style={{
                padding: '4px 8px',
                borderRadius: '4px',
                backgroundColor: customer.credit_status === 'ACTIVE' ? '#d4edda' : '#f8d7da',
                color: customer.credit_status === 'ACTIVE' ? '#155724' : '#721c24'
              }}>
                {customer.credit_status}
              </span></p>
              <div style={{ marginTop: '10px' }}>
                <button style={{
                  marginRight: '5px',
                  padding: '5px 10px',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}>
                  View
                </button>
                <button style={{
                  padding: '5px 10px',
                  backgroundColor: '#ffc107',
                  color: '#333',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}>
                  Edit
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// 2. CUSTOMER INVOICE PAGE (CustomerInvoicePage.jsx)
// ============================================================================

export function CustomerInvoicePage() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  
  const [formData, setFormData] = useState({
    customer_id: '',
    location_id: 1,
    invoice_date: new Date().toISOString().split('T')[0],
    due_date: '',
    items: [{ product_id: '', batch_id: '', quantity: 0, unit_price: 0, discount_percent: 0 }]
  });

  useEffect(() => {
    fetchInvoices();
    fetchCustomers();
    fetchProducts();
  }, []);

  const fetchInvoices = async () => {
    try {
      const response = await axios.get(`${API_URL}/invoices`);
      setInvoices(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      console.error('Error loading invoices:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCustomers = async () => {
    try {
      const response = await axios.get(`${API_URL}/customers`);
      setCustomers(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      console.error('Error loading customers:', err);
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API_URL}/products`);
      setProducts(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      console.error('Error loading products:', err);
    }
  };

  const handleCreateInvoice = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/invoices`, formData);
      setFormData({
        customer_id: '',
        location_id: 1,
        invoice_date: new Date().toISOString().split('T')[0],
        due_date: '',
        items: [{ product_id: '', batch_id: '', quantity: 0, unit_price: 0, discount_percent: 0 }]
      });
      setShowForm(false);
      fetchInvoices();
    } catch (err) {
      alert('Error creating invoice: ' + err.message);
    }
  };

  const handleAddLineItem = () => {
    setFormData({
      ...formData,
      items: [
        ...formData.items,
        { product_id: '', batch_id: '', quantity: 0, unit_price: 0, discount_percent: 0 }
      ]
    });
  };

  if (loading) return <div style={{ padding: '20px' }}>Loading invoices...</div>;

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1>Customer Invoices</h1>
        <button 
          onClick={() => setShowForm(!showForm)}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          {showForm ? 'Cancel' : 'Create Invoice'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreateInvoice} style={{
          backgroundColor: '#f5f5f5',
          padding: '15px',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          <div style={{ marginBottom: '10px' }}>
            <label>Customer:</label>
            <select
              value={formData.customer_id}
              onChange={(e) => setFormData({ ...formData, customer_id: parseInt(e.target.value) })}
              required
              style={{ width: '100%', padding: '8px' }}
            >
              <option value="">Select Customer</option>
              {customers.map(c => (
                <option key={c.customer_id} value={c.customer_id}>
                  {c.customer_name}
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '10px' }}>
            <label>Invoice Date:</label>
            <input
              type="date"
              value={formData.invoice_date}
              onChange={(e) => setFormData({ ...formData, invoice_date: e.target.value })}
              required
              style={{ width: '100%', padding: '8px' }}
            />
          </div>

          <div style={{ marginBottom: '10px' }}>
            <label>Due Date:</label>
            <input
              type="date"
              value={formData.due_date}
              onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
              required
              style={{ width: '100%', padding: '8px' }}
            />
          </div>

          <div style={{ marginBottom: '10px' }}>
            <h3>Line Items</h3>
            {formData.items.map((item, idx) => (
              <div key={idx} style={{ marginBottom: '10px', backgroundColor: 'white', padding: '10px', borderRadius: '4px' }}>
                <label>Product:</label>
                <select
                  value={item.product_id}
                  onChange={(e) => {
                    const newItems = [...formData.items];
                    newItems[idx].product_id = e.target.value;
                    setFormData({ ...formData, items: newItems });
                  }}
                  style={{ width: '100%', padding: '8px', marginBottom: '8px' }}
                >
                  <option value="">Select Product</option>
                  {products.map(p => (
                    <option key={p.product_id} value={p.product_id}>
                      {p.product_name} - GHS {p.unit_price}
                    </option>
                  ))}
                </select>

                <label>Quantity:</label>
                <input
                  type="number"
                  value={item.quantity}
                  onChange={(e) => {
                    const newItems = [...formData.items];
                    newItems[idx].quantity = parseInt(e.target.value);
                    setFormData({ ...formData, items: newItems });
                  }}
                  min="0"
                  step="1"
                  style={{ width: '100%', padding: '8px', marginBottom: '8px' }}
                />

                <label>Discount %:</label>
                <input
                  type="number"
                  value={item.discount_percent}
                  onChange={(e) => {
                    const newItems = [...formData.items];
                    newItems[idx].discount_percent = parseFloat(e.target.value);
                    setFormData({ ...formData, items: newItems });
                  }}
                  min="0"
                  max="100"
                  step="0.01"
                  style={{ width: '100%', padding: '8px' }}
                />
              </div>
            ))}
            <button
              type="button"
              onClick={handleAddLineItem}
              style={{
                padding: '8px 16px',
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                marginTop: '10px'
              }}
            >
              Add Another Item
            </button>
          </div>

          <button 
            type="submit"
            style={{
              padding: '10px 20px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Create Invoice
          </button>
        </form>
      )}

      <div style={{ marginTop: '20px' }}>
        <h2>Invoices ({invoices.length})</h2>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          border: '1px solid #ddd'
        }}>
          <thead>
            <tr style={{ backgroundColor: '#f5f5f5' }}>
              <th style={{ padding: '10px', border: '1px solid #ddd' }}>Invoice #</th>
              <th style={{ padding: '10px', border: '1px solid #ddd' }}>Customer</th>
              <th style={{ padding: '10px', border: '1px solid #ddd' }}>Amount (GHS)</th>
              <th style={{ padding: '10px', border: '1px solid #ddd' }}>Due Date</th>
              <th style={{ padding: '10px', border: '1px solid #ddd' }}>Status</th>
              <th style={{ padding: '10px', border: '1px solid #ddd' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map(invoice => (
              <tr key={invoice.invoice_id}>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>{invoice.invoice_number}</td>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                  {customers.find(c => c.customer_id === invoice.customer_id)?.customer_name || 'N/A'}
                </td>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                  {Number(invoice.total_amount || 0).toFixed(2)}
                </td>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>{invoice.due_date}</td>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    backgroundColor: invoice.status === 'PAID' ? '#d4edda' : '#fff3cd',
                    color: invoice.status === 'PAID' ? '#155724' : '#856404'
                  }}>
                    {invoice.status}
                  </span>
                </td>
                <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                  <button style={{
                    marginRight: '5px',
                    padding: '5px 10px',
                    backgroundColor: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}>
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============================================================================
// 3. FINANCIAL REPORTS PAGE (FinancialReportsPage.jsx)
// ============================================================================

export function FinancialReportsPage() {
  const [pnl, setPnl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);

  const fetchPnL = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/reports/income-statement`, {
        params: { start_date: startDate, end_date: endDate }
      });
      setPnl(response.data);
    } catch (err) {
      alert('Error loading report: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Financial Reports</h1>

      <div style={{
        backgroundColor: '#f5f5f5',
        padding: '15px',
        borderRadius: '4px',
        marginBottom: '20px'
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginBottom: '10px' }}>
          <div>
            <label>Start Date:</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={{ width: '100%', padding: '8px' }}
            />
          </div>
          <div>
            <label>End Date:</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              style={{ width: '100%', padding: '8px' }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button
              onClick={fetchPnL}
              disabled={loading}
              style={{
                width: '100%',
                padding: '8px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {loading ? 'Loading...' : 'Generate Report'}
            </button>
          </div>
        </div>
      </div>

      {pnl && (
        <div style={{
          border: '1px solid #ddd',
          borderRadius: '4px',
          padding: '20px',
          backgroundColor: 'white'
        }}>
          <h2>Income Statement (P&L)</h2>
          <p style={{ color: '#666' }}>
            Period: {startDate} to {endDate}
          </p>

          <table style={{ width: '100%', marginTop: '20px' }}>
            <tbody>
              <tr style={{ borderBottom: '1px solid #ddd' }}>
                <td style={{ padding: '10px' }}><strong>Total Revenue</strong></td>
                <td style={{ padding: '10px', textAlign: 'right' }}>
                  <strong>GHS {Number(pnl.total_revenue || 0).toFixed(2)}</strong>
                </td>
              </tr>
              <tr style={{ borderBottom: '1px solid #ddd' }}>
                <td style={{ padding: '10px' }}>Cost of Goods Sold</td>
                <td style={{ padding: '10px', textAlign: 'right' }}>
                  GHS {Number(pnl.cost_of_goods_sold || 0).toFixed(2)}
                </td>
              </tr>
              <tr style={{ borderBottom: '2px solid #333' }}>
                <td style={{ padding: '10px' }}><strong>Gross Profit</strong></td>
                <td style={{ padding: '10px', textAlign: 'right' }}>
                  <strong>GHS {Number(pnl.gross_profit || 0).toFixed(2)}</strong>
                </td>
              </tr>
              <tr style={{ borderBottom: '1px solid #ddd' }}>
                <td style={{ padding: '10px' }}>Operating Expenses</td>
                <td style={{ padding: '10px', textAlign: 'right' }}>
                  GHS {Number(pnl.operating_expenses || 0).toFixed(2)}
                </td>
              </tr>
              <tr style={{ borderBottom: '2px solid #333' }}>
                <td style={{ padding: '10px' }}><strong>Net Profit</strong></td>
                <td style={{ padding: '10px', textAlign: 'right' }}>
                  <strong style={{
                    color: (pnl.net_profit || 0) >= 0 ? '#28a745' : '#dc3545'
                  }}>
                    GHS {Number(pnl.net_profit || 0).toFixed(2)}
                  </strong>
                </td>
              </tr>
              <tr>
                <td style={{ padding: '10px' }}>Profit Margin</td>
                <td style={{ padding: '10px', textAlign: 'right' }}>
                  {Number(pnl.profit_margin || 0).toFixed(2)}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default {
  CustomerCreditPage,
  CustomerInvoicePage,
  FinancialReportsPage
};
