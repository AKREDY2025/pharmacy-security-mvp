import React, { useState } from 'react';

const OnboardingPortal = () => {
  const [currentStep, setCurrentStep] = useState('welcome');
  const [formData, setFormData] = useState({
    pharmacyName: '',
    licenseNumber: '',
    email: '',
    phone: '',
    city: '',
    region: '',
    staffCount: '',
    verificationCapacity: '',
    password: '',
    confirmPassword: '',
  });
  const [signupComplete, setSignupComplete] = useState(false);
  const [newPharmacy, setNewPharmacy] = useState(null);
  const [adminDashboard, setAdminDashboard] = useState(false);
  const [pendingSignups, setPendingSignups] = useState([
    {
      id: 1,
      name: 'Accra Premium Pharmacy',
      city: 'Accra',
      license: 'PHARM-999',
      email: 'contact@premium.com',
      appliedAt: '2026-08-14 10:30',
      status: 'pending'
    },
    {
      id: 2,
      name: 'Kumasi Health Center',
      city: 'Kumasi',
      license: 'PHARM-998',
      email: 'contact@kumasi.com',
      appliedAt: '2026-08-14 09:45',
      status: 'pending'
    }
  ]);
  const [activePharmacies, setActivePharmacies] = useState([
    {
      id: 1,
      name: 'Accra Central Pharmacy',
      city: 'Accra',
      status: 'active',
      verifications: 1247,
      revenue: 'GHS 12,500/mo',
      joinedAt: '2026-08-01'
    },
    {
      id: 2,
      name: 'Kumasi Health Plus',
      city: 'Kumasi',
      status: 'active',
      verifications: 856,
      revenue: 'GHS 8,560/mo',
      joinedAt: '2026-08-05'
    }
  ]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSignup = (e) => {
    e.preventDefault();
    
    // Validate
    if (formData.password !== formData.confirmPassword) {
      alert('Passwords do not match');
      return;
    }

    // Create new pharmacy
    const newPharmacyData = {
      id: Math.floor(Math.random() * 10000),
      name: formData.pharmacyName,
      email: formData.email,
      phone: formData.phone,
      license: formData.licenseNumber,
      city: formData.city,
      region: formData.region,
      staffCount: formData.staffCount,
      apiKey: `sk_${Math.random().toString(36).substring(2, 15)}`,
      apiSecret: `sec_${Math.random().toString(36).substring(2, 15)}`,
      createdAt: new Date().toLocaleString(),
      status: 'pending_approval'
    };

    setNewPharmacy(newPharmacyData);
    setPendingSignups([...pendingSignups, {
      id: newPharmacyData.id,
      name: newPharmacyData.name,
      city: newPharmacyData.city,
      license: newPharmacyData.license,
      email: newPharmacyData.email,
      appliedAt: newPharmacyData.createdAt,
      status: 'pending'
    }]);
    setSignupComplete(true);
    setCurrentStep('complete');
  };

  const approveSignup = (signupId) => {
    setPendingSignups(pendingSignups.map(signup => 
      signup.id === signupId ? { ...signup, status: 'approved' } : signup
    ));
    
    // Move to active pharmacies
    const approved = pendingSignups.find(s => s.id === signupId);
    if (approved) {
      setActivePharmacies([...activePharmacies, {
        id: approved.id,
        name: approved.name,
        city: approved.city,
        status: 'active',
        verifications: 0,
        revenue: 'GHS 0/mo',
        joinedAt: new Date().toLocaleDateString()
      }]);
    }
  };

  // ============ WELCOME SCREEN ============
  if (currentStep === 'welcome' && !adminDashboard) {
    return (
      <div style={{ minHeight: '100vh', background: '#F1EFE8', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '40px 24px' }}>
          {/* Top Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '60px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '40px', height: '40px', background: '#0F6E56', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px', color: 'white' }}>
                ✓
              </div>
              <h1 style={{ margin: 0, fontSize: '20px', fontWeight: '600', color: '#2C2C2A' }}>PharmSecure</h1>
            </div>
            <button
              onClick={() => setAdminDashboard(true)}
              style={{
                padding: '8px 16px',
                background: 'white',
                border: '0.5px solid #D3D1C7',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: '500',
                cursor: 'pointer',
                color: '#0F6E56'
              }}
            >
              Admin Dashboard
            </button>
          </div>

          {/* Main Content */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '60px', alignItems: 'center' }}>
            {/* Left: Copy */}
            <div>
              <h2 style={{ fontSize: '40px', fontWeight: '600', color: '#2C2C2A', margin: '0 0 20px', lineHeight: '1.2' }}>
                Verify Authentic Pharmaceuticals in Seconds
              </h2>
              <p style={{ fontSize: '16px', color: '#888780', margin: '0 0 32px', lineHeight: '1.8' }}>
                Join Ghana's leading anti-counterfeiting platform. Protect your customers, stop fake drugs, and build trust with PharmSecure.
              </p>

              {/* Key Benefits */}
              <div style={{ display: 'grid', gap: '20px', marginBottom: '40px' }}>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <div style={{ fontSize: '20px', marginTop: '2px' }}>⚡</div>
                  <div>
                    <p style={{ margin: '0 0 4px', fontSize: '14px', fontWeight: '500', color: '#2C2C2A' }}>Instant Verification</p>
                    <p style={{ margin: '0', fontSize: '13px', color: '#888780' }}>Scan QR codes in seconds, protect customers</p>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                  <div style={{ fontSize: '20px', marginTop: '2px' }}>🛡️</div>
                  <div>
                    <p style={{ margin: '0 0 4px', fontSize: '14px', fontWeight: '500', color: '#2C2C2A' }}>Zero Counterfeits</p>
                    <p style={{ margin: '0', fontSize: '13px', color: '#888780' }}>AI-powered fraud detection catches fakes instantly</p>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                  <div style={{ fontSize: '20px', marginTop: '2px' }}>📊</div>
                  <div>
                    <p style={{ margin: '0 0 4px', fontSize: '14px', fontWeight: '500', color: '#2C2C2A' }}>Complete Audit Trail</p>
                    <p style={{ margin: '0', fontSize: '13px', color: '#888780' }}>FDA-ready compliance tracking for every verification</p>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                  <div style={{ fontSize: '20px', marginTop: '2px' }}>💰</div>
                  <div>
                    <p style={{ margin: '0 0 4px', fontSize: '14px', fontWeight: '500', color: '#2C2C2A' }}>Increase Revenue</p>
                    <p style={{ margin: '0', fontSize: '13px', color: '#888780' }}>Build customer trust, reduce counterfeit losses</p>
                  </div>
                </div>
              </div>

              {/* CTA Button */}
              <button
                onClick={() => setCurrentStep('pharmacy-info')}
                style={{
                  width: '100%',
                  padding: '14px 20px',
                  background: '#0F6E56',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
                onMouseEnter={(e) => e.target.style.background = '#085041'}
                onMouseLeave={(e) => e.target.style.background = '#0F6E56'}
              >
                Start Free 30-Day Trial
              </button>

              <p style={{ fontSize: '12px', color: '#888780', textAlign: 'center', margin: '16px 0 0' }}>
                No credit card required • Setup in 5 minutes
              </p>
            </div>

            {/* Right: Stats */}
            <div>
              <div style={{ background: 'white', border: '0.5px solid #D3D1C7', borderRadius: '12px', padding: '40px', textAlign: 'center' }}>
                <div style={{ marginBottom: '40px' }}>
                  <p style={{ fontSize: '12px', color: '#888780', margin: '0 0 8px', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Pharmacies Trust Us
                  </p>
                  <p style={{ fontSize: '48px', fontWeight: '600', color: '#0F6E56', margin: '0' }}>3+</p>
                </div>

                <div style={{ marginBottom: '40px' }}>
                  <p style={{ fontSize: '12px', color: '#888780', margin: '0 0 8px', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Verifications This Month
                  </p>
                  <p style={{ fontSize: '48px', fontWeight: '600', color: '#3B6D11', margin: '0' }}>2,947</p>
                </div>

                <div style={{ marginBottom: '40px' }}>
                  <p style={{ fontSize: '12px', color: '#888780', margin: '0 0 8px', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Counterfeits Stopped
                  </p>
                  <p style={{ fontSize: '48px', fontWeight: '600', color: '#A32D2D', margin: '0' }}>12</p>
                </div>

                <div style={{
                  background: '#E1F5EE',
                  border: '0.5px solid #0F6E56',
                  borderRadius: '8px',
                  padding: '20px',
                  marginTop: '40px'
                }}>
                  <p style={{ fontSize: '13px', color: '#0F6E56', margin: '0', fontWeight: '500' }}>
                    ✓ Join Ghana's fastest-growing anti-counterfeiting network
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ============ PHARMACY INFO FORM ============
  if (currentStep === 'pharmacy-info' && !adminDashboard && !signupComplete) {
    return (
      <div style={{ minHeight: '100vh', background: '#F1EFE8', fontFamily: 'system-ui, -apple-system, sans-serif', padding: '40px 24px' }}>
        <div style={{ maxWidth: '600px', margin: '0 auto' }}>
          <button
            onClick={() => setCurrentStep('welcome')}
            style={{
              marginBottom: '24px',
              padding: '8px 16px',
              background: 'white',
              border: '0.5px solid #D3D1C7',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: '500',
              cursor: 'pointer',
              color: '#0F6E56'
            }}
          >
            ← Back
          </button>

          <div style={{ background: 'white', border: '0.5px solid #D3D1C7', borderRadius: '12px', padding: '40px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#2C2C2A', margin: '0 0 8px' }}>
              Register Your Pharmacy
            </h2>
            <p style={{ fontSize: '14px', color: '#888780', margin: '0 0 32px' }}>
              Tell us about your pharmacy. Setup takes just 5 minutes.
            </p>

            <form onSubmit={handleSignup} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Pharmacy Name */}
              <div>
                <label style={{ fontSize: '13px', fontWeight: '500', color: '#2C2C2A', display: 'block', marginBottom: '6px' }}>
                  Pharmacy Name *
                </label>
                <input
                  type="text"
                  name="pharmacyName"
                  value={formData.pharmacyName}
                  onChange={handleInputChange}
                  placeholder="e.g., Accra Premium Pharmacy"
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '0.5px solid #D3D1C7',
                    borderRadius: '6px',
                    fontSize: '14px',
                    boxSizing: 'border-box'
                  }}
                  required
                />
              </div>

              {/* License Number */}
              <div>
                <label style={{ fontSize: '13px', fontWeight: '500', color: '#2C2C2A', display: 'block', marginBottom: '6px' }}>
                  FDA License Number *
                </label>
                <input
                  type="text"
                  name="licenseNumber"
                  value={formData.licenseNumber}
                  onChange={handleInputChange}
                  placeholder="e.g., PHARM-2024-001"
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '0.5px solid #D3D1C7',
                    borderRadius: '6px',
                    fontSize: '14px',
                    boxSizing: 'border-box'
                  }}
                  required
                />
              </div>

              {/* Location Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '13px', fontWeight: '500', color: '#2C2C2A', display: 'block', marginBottom: '6px' }}>
                    City *
                  </label>
                  <input
                    type="text"
                    name="city"
                    value={formData.city}
                    onChange={handleInputChange}
                    placeholder="e.g., Accra"
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      border: '0.5px solid #D3D1C7',
                      borderRadius: '6px',
                      fontSize: '14px',
                      boxSizing: 'border-box'
                    }}
                    required
                  />
                </div>
                <div>
                  <label style={{ fontSize: '13px', fontWeight: '500', color: '#2C2C2A', display: 'block', marginBottom: '6px' }}>
                    Region *
                  </label>
                  <select
                    name="region"
                    value={formData.region}
                    onChange={handleInputChange}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      border: '0.5px solid #D3D1C7',
                      borderRadius: '6px',
                      fontSize: '14px',
                      boxSizing: 'border-box',
                      background: 'white'
                    }}
                    required
                  >
                    <option value="">Select region</option>
                    <option value="Greater Accra">Greater Accra</option>
                    <option value="Ashanti">Ashanti</option>
                    <option value="Western">Western</option>
                    <option value="Eastern">Eastern</option>
                    <option value="Central">Central</option>
                    <option value="Volta">Volta</option>
                    <option value="Northern">Northern</option>
                  </select>
                </div>
              </div>

              {/* Contact Info */}
              <div>
                <label style={{ fontSize: '13px', fontWeight: '500', color: '#2C2C2A', display: 'block', marginBottom: '6px' }}>
                  Email Address *
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  placeholder="contact@pharmacy.com"
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '0.5px solid #D3D1C7',
                    borderRadius: '6px',
                    fontSize: '14px',
                    boxSizing: 'border-box'
                  }}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '13px', fontWeight: '500', color: '#2C2C2A', display: 'block', marginBottom: '6px' }}>
                  Phone Number *
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                  placeholder="+233 21 123 4567"
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '0.5px solid #D3D1C7',
                    borderRadius: '6px',
                    fontSize: '14px',
                    boxSizing: 'border-box'
                  }}
                  required
                />
              </div>

              {/* Staff Count */}
              <div>
                <label style={{ fontSize: '13px', fontWeight: '500', color: '#2C2C2A', display: 'block', marginBottom: '6px' }}>
                  Number of Staff Members *
                </label>
                <input
                  type="number"
                  name="staffCount"
                  value={formData.staffCount}
                  onChange={handleInputChange}
                  placeholder="e.g., 5"
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '0.5px solid #D3D1C7',
                    borderRadius: '6px',
                    fontSize: '14px',
                    boxSizing: 'border-box'
                  }}
                  required
                />
              </div>

              {/* Password */}
              <div>
                <label style={{ fontSize: '13px', fontWeight: '500', color: '#2C2C2A', display: 'block', marginBottom: '6px' }}>
                  Password *
                </label>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder="••••••••"
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '0.5px solid #D3D1C7',
                    borderRadius: '6px',
                    fontSize: '14px',
                    boxSizing: 'border-box'
                  }}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '13px', fontWeight: '500', color: '#2C2C2A', display: 'block', marginBottom: '6px' }}>
                  Confirm Password *
                </label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  placeholder="••••••••"
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '0.5px solid #D3D1C7',
                    borderRadius: '6px',
                    fontSize: '14px',
                    boxSizing: 'border-box'
                  }}
                  required
                />
              </div>

              {/* Submit */}
              <button
                type="submit"
                style={{
                  padding: '12px 20px',
                  background: '#0F6E56',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  marginTop: '12px'
                }}
              >
                Create Account & Start Trial
              </button>

              <p style={{ fontSize: '12px', color: '#888780', textAlign: 'center', margin: '0' }}>
                By signing up, you agree to our Terms of Service and Privacy Policy
              </p>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // ============ SIGNUP COMPLETE ============
  if (currentStep === 'complete' && !adminDashboard && signupComplete) {
    return (
      <div style={{ minHeight: '100vh', background: '#EAF3DE', fontFamily: 'system-ui, -apple-system, sans-serif', padding: '40px 24px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ maxWidth: '600px', width: '100%' }}>
          <div style={{ background: 'white', border: '0.5px solid #D3D1C7', borderRadius: '12px', padding: '40px', textAlign: 'center' }}>
            <div style={{
              width: '64px',
              height: '64px',
              background: '#3B6D11',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '32px',
              margin: '0 auto 24px',
              color: 'white'
            }}>
              ✓
            </div>

            <h2 style={{ fontSize: '28px', fontWeight: '600', color: '#2C2C2A', margin: '0 0 12px' }}>
              Welcome to PharmSecure!
            </h2>
            <p style={{ fontSize: '14px', color: '#888780', margin: '0 0 32px' }}>
              Your account has been created and is pending admin approval.
            </p>

            {newPharmacy && (
              <div style={{
                background: '#F1EFE8',
                border: '0.5px solid #D3D1C7',
                borderRadius: '8px',
                padding: '20px',
                marginBottom: '32px',
                textAlign: 'left'
              }}>
                <p style={{ fontSize: '12px', color: '#888780', margin: '0 0 12px', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Account Details
                </p>
                
                <div style={{ marginBottom: '12px' }}>
                  <p style={{ fontSize: '12px', color: '#888780', margin: '0 0 4px' }}>Pharmacy Name</p>
                  <p style={{ fontSize: '14px', color: '#2C2C2A', margin: '0', fontWeight: '500' }}>{newPharmacy.name}</p>
                </div>

                <div style={{ marginBottom: '12px' }}>
                  <p style={{ fontSize: '12px', color: '#888780', margin: '0 0 4px' }}>Email</p>
                  <p style={{ fontSize: '14px', color: '#2C2C2A', margin: '0', fontWeight: '500' }}>{newPharmacy.email}</p>
                </div>

                <div style={{ marginBottom: '12px' }}>
                  <p style={{ fontSize: '12px', color: '#888780', margin: '0 0 4px' }}>Status</p>
                  <p style={{ fontSize: '14px', color: '#A32D2D', margin: '0', fontWeight: '500' }}>Pending Admin Approval</p>
                </div>

                <div>
                  <p style={{ fontSize: '12px', color: '#888780', margin: '0 0 4px' }}>Estimated Approval</p>
                  <p style={{ fontSize: '14px', color: '#3B6D11', margin: '0', fontWeight: '500' }}>Within 1 hour</p>
                </div>
              </div>
            )}

            <div style={{
              background: '#E1F5EE',
              border: '0.5px solid #0F6E56',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '32px'
            }}>
              <p style={{ fontSize: '13px', color: '#0F6E56', margin: '0' }}>
                <strong>Next Step:</strong> We'll send you an email when your account is approved. Then you can start verifying products immediately.
              </p>
            </div>

            <button
              onClick={() => setCurrentStep('welcome')}
              style={{
                width: '100%',
                padding: '12px 20px',
                background: '#0F6E56',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              Back to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ============ ADMIN DASHBOARD ============
  if (adminDashboard) {
    return (
      <div style={{ minHeight: '100vh', background: '#F1EFE8', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
        <div style={{
          background: 'white',
          borderBottom: '0.5px solid #D3D1C7',
          padding: '16px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '40px', height: '40px', background: '#0F6E56', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px', color: 'white' }}>
              ✓
            </div>
            <h2 style={{ margin: '0', fontSize: '16px', fontWeight: '600', color: '#2C2C2A' }}>PharmSecure Admin</h2>
          </div>
          <button
            onClick={() => setAdminDashboard(false)}
            style={{
              padding: '8px 16px',
              background: '#FCE4E4',
              color: '#A32D2D',
              border: 'none',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: '500',
              cursor: 'pointer'
            }}
          >
            Logout
          </button>
        </div>

        <div style={{ padding: '32px 24px', maxWidth: '1200px', margin: '0 auto' }}>
          {/* Stats */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginBottom: '32px' }}>
            <div style={{ background: 'white', border: '0.5px solid #D3D1C7', borderRadius: '8px', padding: '20px', textAlign: 'center' }}>
              <p style={{ fontSize: '12px', color: '#888780', margin: '0 0 8px', fontWeight: '500' }}>Active Pharmacies</p>
              <p style={{ fontSize: '32px', fontWeight: '600', color: '#0F6E56', margin: '0' }}>{activePharmacies.length}</p>
            </div>
            <div style={{ background: 'white', border: '0.5px solid #D3D1C7', borderRadius: '8px', padding: '20px', textAlign: 'center' }}>
              <p style={{ fontSize: '12px', color: '#888780', margin: '0 0 8px', fontWeight: '500' }}>Pending Approvals</p>
              <p style={{ fontSize: '32px', fontWeight: '600', color: '#A32D2D', margin: '0' }}>{pendingSignups.filter(s => s.status === 'pending').length}</p>
            </div>
            <div style={{ background: 'white', border: '0.5px solid #D3D1C7', borderRadius: '8px', padding: '20px', textAlign: 'center' }}>
              <p style={{ fontSize: '12px', color: '#888780', margin: '0 0 8px', fontWeight: '500' }}>Monthly Revenue</p>
              <p style={{ fontSize: '32px', fontWeight: '600', color: '#3B6D11', margin: '0' }}>GHS 21K</p>
            </div>
            <div style={{ background: 'white', border: '0.5px solid #D3D1C7', borderRadius: '8px', padding: '20px', textAlign: 'center' }}>
              <p style={{ fontSize: '12px', color: '#888780', margin: '0 0 8px', fontWeight: '500' }}>Total Verifications</p>
              <p style={{ fontSize: '32px', fontWeight: '600', color: '#0F6E56', margin: '0' }}>2,103</p>
            </div>
          </div>

          {/* Pending Signups */}
          <div style={{ background: 'white', border: '0.5px solid #D3D1C7', borderRadius: '8px', padding: '24px', marginBottom: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#2C2C2A', margin: '0 0 16px' }}>Pending Approvals</h3>
            
            {pendingSignups.filter(s => s.status === 'pending').length === 0 ? (
              <p style={{ color: '#888780', textAlign: 'center', padding: '20px' }}>No pending signups</p>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '0.5px solid #D3D1C7' }}>
                      <th style={{ textAlign: 'left', padding: '12px', fontWeight: '500', color: '#888780' }}>Pharmacy</th>
                      <th style={{ textAlign: 'left', padding: '12px', fontWeight: '500', color: '#888780' }}>City</th>
                      <th style={{ textAlign: 'left', padding: '12px', fontWeight: '500', color: '#888780' }}>Applied</th>
                      <th style={{ textAlign: 'left', padding: '12px', fontWeight: '500', color: '#888780' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingSignups.filter(s => s.status === 'pending').map(signup => (
                      <tr key={signup.id} style={{ borderBottom: '0.5px solid #D3D1C7' }}>
                        <td style={{ padding: '12px', color: '#2C2C2A', fontWeight: '500' }}>{signup.name}</td>
                        <td style={{ padding: '12px', color: '#888780' }}>{signup.city}</td>
                        <td style={{ padding: '12px', color: '#888780' }}>{signup.appliedAt}</td>
                        <td style={{ padding: '12px' }}>
                          <button
                            onClick={() => approveSignup(signup.id)}
                            style={{
                              padding: '6px 12px',
                              background: '#E1F5EE',
                              color: '#0F6E56',
                              border: '0.5px solid #0F6E56',
                              borderRadius: '4px',
                              fontSize: '12px',
                              fontWeight: '600',
                              cursor: 'pointer'
                            }}
                          >
                            Approve
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Active Pharmacies */}
          <div style={{ background: 'white', border: '0.5px solid #D3D1C7', borderRadius: '8px', padding: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#2C2C2A', margin: '0 0 16px' }}>Active Pharmacies</h3>
            
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '0.5px solid #D3D1C7' }}>
                    <th style={{ textAlign: 'left', padding: '12px', fontWeight: '500', color: '#888780' }}>Pharmacy</th>
                    <th style={{ textAlign: 'left', padding: '12px', fontWeight: '500', color: '#888780' }}>City</th>
                    <th style={{ textAlign: 'left', padding: '12px', fontWeight: '500', color: '#888780' }}>Verifications</th>
                    <th style={{ textAlign: 'left', padding: '12px', fontWeight: '500', color: '#888780' }}>Revenue</th>
                    <th style={{ textAlign: 'left', padding: '12px', fontWeight: '500', color: '#888780' }}>Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {activePharmacies.map(pharmacy => (
                    <tr key={pharmacy.id} style={{ borderBottom: '0.5px solid #D3D1C7' }}>
                      <td style={{ padding: '12px', color: '#2C2C2A', fontWeight: '500' }}>{pharmacy.name}</td>
                      <td style={{ padding: '12px', color: '#888780' }}>{pharmacy.city}</td>
                      <td style={{ padding: '12px', color: '#2C2C2A' }}>{pharmacy.verifications}</td>
                      <td style={{ padding: '12px', color: '#3B6D11', fontWeight: '500' }}>{pharmacy.revenue}</td>
                      <td style={{ padding: '12px', color: '#888780' }}>{pharmacy.joinedAt}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    );
  }
};

export default OnboardingPortal;
