# Frontend Session Management - Usage Guide

## Overview

The TrustGuard frontend now includes comprehensive session management utilities that handle JWT tokens, automatic refresh, and secure API calls.

---

## Components

### 1. Session Manager (`lib/sessionManager.ts`)

Manages JWT token lifecycle with auto-refresh and expiration handling.

#### Features
- ✅ 60-minute JWT sessions with auto-logout
- ✅ Auto-refresh at 50 minutes (before expiration)
- ✅ Session expiry warnings (5-minute countdown)
- ✅ Secure token storage in localStorage
- ✅ Automatic redirect to login on expiration

#### Usage

```typescript
import { sessionManager, isAuthenticated, logout } from '@/lib/sessionManager';

// Initialize session after login
const handleLogin = async (email: string, password: string) => {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
    headers: { 'Content-Type': 'application/json' }
  });
  
  const data = await response.json();
  
  if (data.status === 'success') {
    const token = data.data.token;
    const user = {
      user_id: data.data.user_id,
      role: data.data.role,
      name: data.data.name,
      email: email
    };
    
    // Initialize session with auto-refresh
    sessionManager.initializeSession(token, user);
    
    // Redirect to dashboard
    router.push('/dashboard');
  }
};

// Check authentication status
const ProtectedRoute = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" />;
  }
  return children;
};

// Manual logout
const handleLogout = () => {
  logout(); // Clears session and redirects to login
};

// Get current user
const user = sessionManager.getUser();
console.log(`Welcome ${user?.name}!`);
```

---

### 2. API Client (`lib/apiClient.ts`)

HTTP client with automatic token injection and refresh on 401 errors.

#### Features
- ✅ Automatic Authorization header injection
- ✅ Auto-retry on 401 with token refresh
- ✅ Centralized error handling
- ✅ TypeScript type safety
- ✅ User-friendly error toasts

#### Usage

```typescript
import { apiClient, get, post, patch, del } from '@/lib/apiClient';

// GET request
const fetchVendors = async () => {
  try {
    const response = await get('/ceo/vendors');
    console.log('Vendors:', response.data);
  } catch (error) {
    console.error('Failed to fetch vendors:', error);
  }
};

// POST request
const createVendor = async (vendorData) => {
  try {
    const response = await post('/ceo/vendors', vendorData);
    toast.success('Vendor created successfully!');
    return response.data;
  } catch (error) {
    // Error toast shown automatically
    console.error('Failed to create vendor:', error);
  }
};

// PATCH request
const updateVendor = async (vendorId: string, updates) => {
  try {
    const response = await patch(`/ceo/vendors/${vendorId}`, updates);
    return response.data;
  } catch (error) {
    console.error('Update failed:', error);
  }
};

// DELETE request
const deleteVendor = async (vendorId: string) => {
  try {
    await del(`/ceo/vendors/${vendorId}`);
    toast.success('Vendor deleted');
  } catch (error) {
    console.error('Delete failed:', error);
  }
};

// Custom request with options
const uploadReceipt = async (file: File) => {
  const formData = new FormData();
  formData.append('receipt', file);
  
  try {
    const response = await apiClient.request('/ceo/receipts/upload', {
      method: 'POST',
      body: formData,
      headers: {
        // Content-Type automatically set for FormData
      }
    });
    return response.data;
  } catch (error) {
    console.error('Upload failed:', error);
  }
};
```

---

## Integration Examples

### React Component with Session Management

```typescript
import React, { useEffect, useState } from 'react';
import { sessionManager, isAuthenticated } from '@/lib/sessionManager';
import { get } from '@/lib/apiClient';
import { useNavigate } from 'react-router-dom';

export const DashboardPage = () => {
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const user = sessionManager.getUser();

  useEffect(() => {
    // Check authentication
    if (!isAuthenticated()) {
      navigate('/login');
      return;
    }

    // Fetch data with automatic token refresh
    loadVendors();

    // Cleanup timers on unmount
    return () => {
      sessionManager.cleanup();
    };
  }, []);

  const loadVendors = async () => {
    try {
      const response = await get('/ceo/vendors');
      setVendors(response.data || []);
    } catch (error) {
      console.error('Failed to load vendors:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Welcome, {user?.name}!</h1>
      {loading ? (
        <p>Loading vendors...</p>
      ) : (
        <ul>
          {vendors.map(vendor => (
            <li key={vendor.vendor_id}>{vendor.name}</li>
          ))}
        </ul>
      )}
    </div>
  );
};
```

### Login Component

```typescript
import React, { useState } from 'react';
import { sessionManager } from '@/lib/sessionManager';
import { post } from '@/lib/apiClient';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState<'credentials' | 'otp'>('credentials');
  const [ceoId, setCeoId] = useState('');
  const navigate = useNavigate();

  const handleRequestOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const response = await post('/auth/login', { email, password });
      
      if (response.data.ceo_id) {
        setCeoId(response.data.ceo_id);
        setStep('otp');
        toast.success('OTP sent to your registered phone number');
      }
    } catch (error) {
      toast.error('Login failed');
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const response = await post('/auth/verify-otp', { ceo_id: ceoId, otp });
      
      if (response.data.token) {
        const user = {
          user_id: ceoId,
          role: 'CEO',
          name: response.data.name,
          email: email
        };
        
        // Initialize session with auto-refresh
        sessionManager.initializeSession(response.data.token, user);
        
        toast.success('Logged in successfully!');
        navigate('/dashboard');
      }
    } catch (error) {
      toast.error('Invalid OTP');
    }
  };

  return (
    <div>
      {step === 'credentials' ? (
        <form onSubmit={handleRequestOTP}>
          <h2>CEO Login</h2>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            required
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            required
          />
          <button type="submit">Request OTP</button>
        </form>
      ) : (
        <form onSubmit={handleVerifyOTP}>
          <h2>Verify OTP</h2>
          <p>Enter the 6-character code sent to your phone</p>
          <input
            type="text"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            placeholder="OTP"
            maxLength={6}
            required
          />
          <button type="submit">Verify</button>
        </form>
      )}
    </div>
  );
};
```

---

## Session Lifecycle

### 1. Login Flow
```
User enters credentials → Request OTP → Verify OTP
→ Receive JWT token → sessionManager.initializeSession()
→ Auto-refresh timer starts (50 minutes)
→ Expiry check timer starts (every 1 minute)
```

### 2. Active Session
```
API calls use apiClient → Authorization header auto-added
→ If 401 (expired) → Auto-refresh attempted
→ If refresh succeeds → Retry original request
→ If refresh fails → Logout and redirect
```

### 3. Token Refresh (Auto at 50 minutes)
```
50-minute timer fires → POST /auth/refresh-token
→ Validate current token → Issue new 60-minute token
→ Update localStorage → Reset expiry time
→ Show "Session extended" toast
```

### 4. Expiry Warnings (Last 5 minutes)
```
Check timer (every 1 minute) → Calculate time left
→ If < 5 minutes → Show warning toast
→ "Session expires in X minutes"
```

### 5. Session Expiry
```
Time exceeds 60 minutes → Clear all timers
→ Remove token from localStorage → Show "Session Expired" toast
→ Redirect to /login
```

### 6. Manual Logout
```
User clicks logout → sessionManager.logout()
→ Clear all timers → Remove token
→ Show "Logged out" toast → Redirect to /login
```

---

## Error Handling

### Automatic Error Handling

The API client automatically handles:

1. **Expired Sessions (401)**
   - Attempts token refresh
   - Retries original request
   - Logs out if refresh fails

2. **Invalid Tokens (401)**
   - Immediate logout
   - Redirect to login

3. **Server Errors (500)**
   - Shows error toast
   - Logs error to console

4. **Network Errors**
   - Shows error toast
   - Preserves session

### Custom Error Handling

```typescript
const fetchData = async () => {
  try {
    const response = await get('/ceo/analytics');
    return response.data;
  } catch (error: any) {
    if (error.message.includes('expired')) {
      // Session expired, already handled by apiClient
      console.log('Redirecting to login...');
    } else {
      // Custom error handling
      console.error('Data fetch failed:', error.message);
      // Show custom error UI
    }
  }
};
```

---

## Security Best Practices

### ✅ Do's
- ✅ Use `apiClient` for all API calls (auto-handles auth)
- ✅ Check `isAuthenticated()` before rendering protected routes
- ✅ Call `sessionManager.cleanup()` on component unmount
- ✅ Trust the auto-refresh mechanism (configured at 50 minutes)
- ✅ Use HTTPS in production

### ❌ Don'ts
- ❌ Don't manually add Authorization headers (apiClient does it)
- ❌ Don't store token in state (use sessionManager.getToken())
- ❌ Don't implement custom token refresh logic
- ❌ Don't ignore session expiry warnings
- ❌ Don't bypass authentication checks

---

## Configuration

### Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### API Client Configuration

```typescript
// lib/apiClient.ts
const apiClient = new ApiClient(process.env.NEXT_PUBLIC_API_URL || '/api');
```

---

## Testing

### Manual Testing

1. **Test Auto-Refresh**:
   - Login and wait 50 minutes
   - Should see "Session extended" toast
   - Token should be refreshed automatically

2. **Test Expiry Warning**:
   - Login and wait 55 minutes
   - Should see "Session expires in 5 minutes" warning

3. **Test Auto-Logout**:
   - Login and wait 60 minutes
   - Should see "Session expired" toast
   - Should redirect to /login

4. **Test Manual Logout**:
   - Login and click logout
   - Should see "Logged out" toast
   - Should clear all session data

### Automated Testing

```typescript
import { sessionManager } from '@/lib/sessionManager';

describe('Session Manager', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should initialize session correctly', () => {
    const token = 'test-token';
    const user = { user_id: 'ceo_123', role: 'CEO' };
    
    sessionManager.initializeSession(token, user);
    
    expect(sessionManager.getToken()).toBe(token);
    expect(sessionManager.getUser()).toEqual(user);
    expect(sessionManager.isAuthenticated()).toBe(true);
  });

  it('should detect expired sessions', () => {
    // Set expiry to past
    localStorage.setItem('trustguard_token', 'test-token');
    localStorage.setItem('trustguard_token_expiry', String(Date.now() - 1000));
    
    expect(sessionManager.isAuthenticated()).toBe(false);
  });
});
```

---

## Troubleshooting

### Issue: Token not being added to requests
**Solution**: Use `apiClient` instead of raw `fetch()`

### Issue: Auto-refresh not working
**Solution**: Ensure session was initialized with `sessionManager.initializeSession()`

### Issue: Session expires too quickly
**Solution**: Check backend JWT expiration setting (should be 60 minutes)

### Issue: Warnings not showing
**Solution**: Ensure toast library (sonner) is properly installed and configured

---

## Related Documentation

- [Session Security Guide](./SESSION_SECURITY.md)
- [Multi-Tenancy Certification](./MULTI_TENANCY_CERTIFICATION.md)
- [Backend API Documentation](../backend/README.md)

---

**Last Updated**: November 23, 2025  
**Status**: ✅ Production Ready
