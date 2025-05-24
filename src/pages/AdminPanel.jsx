import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faUsers, 
  faQuoteLeft, 
  faCreditCard, 
  faCheck, 
  faTimes, 
  faPlus,
  faChartBar,
  faUserShield,
  faArrowLeft
} from '@fortawesome/free-solid-svg-icons';
import { API_BASE_URL } from '../utils/constants';
import '../styles/AdminPanel.css';

const AdminPanel = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboardStats, setDashboardStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [offlinePayments, setOfflinePayments] = useState([]);
  const [failedPayments, setFailedPayments] = useState({ payments: [], subscriptions: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Redirect if not admin
  useEffect(() => {
    if (!user || !user.is_admin) {
      navigate('/home');
      return;
    }
  }, [user, navigate]);
  // Load dashboard stats on mount
  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadDashboardStats();
    } else if (activeTab === 'users') {
      loadUsers();
    } else if (activeTab === 'payments') {
      loadOfflinePayments();
    } else if (activeTab === 'failed-payments') {
      loadFailedPayments();
    }
  }, [activeTab]);

  const loadDashboardStats = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/dashboard`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setDashboardStats(data.stats);
      } else {
        setError('Failed to load dashboard stats');
      }
    } catch (err) {
      setError('Error loading dashboard stats');
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users);
      } else {
        setError('Failed to load users');
      }
    } catch (err) {
      setError('Error loading users');
    } finally {
      setLoading(false);
    }
  };

  const loadOfflinePayments = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/payments/offline`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setOfflinePayments(data.payments);
      } else {
        setError('Failed to load offline payments');
      }
    } catch (err) {
      setError('Error loading offline payments');
    } finally {
      setLoading(false);
    }
  };

  const loadFailedPayments = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/payments/failed`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setFailedPayments({
          payments: data.failed_payments || [],
          subscriptions: data.failed_subscriptions || []
        });
      } else {
        setError('Failed to load failed payments');
      }
    } catch (err) {
      setError('Error loading failed payments');
    } finally {
      setLoading(false);
    }
  };

  const approvePayment = async (paymentId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/payments/offline/${paymentId}/approve`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          notes: 'Approved by admin'
        })
      });
      
      if (response.ok) {
        setSuccess('Payment approved successfully');
        loadOfflinePayments(); // Reload payments
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to approve payment');
      }
    } catch (err) {
      setError('Error approving payment');
    }
  };

  const rejectPayment = async (paymentId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/payments/offline/${paymentId}/reject`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          notes: 'Rejected by admin'
        })
      });
      
      if (response.ok) {
        setSuccess('Payment rejected');
        loadOfflinePayments(); // Reload payments
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to reject payment');
      }
    } catch (err) {
      setError('Error rejecting payment');
    }
  };

  const promoteUser = async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/promote`, {
        method: 'POST',
        credentials: 'include'
      });
      
      if (response.ok) {
        setSuccess('User promoted to admin');
        loadUsers(); // Reload users
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to promote user');
      }
    } catch (err) {
      setError('Error promoting user');
    }
  };

  const demoteUser = async (userId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/demote`, {
        method: 'POST',
        credentials: 'include'
      });
      
      if (response.ok) {
        setSuccess('User demoted to regular user');
        loadUsers(); // Reload users
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to demote user');
      }
    } catch (err) {
      setError('Error demoting user');
    }
  };

  const renderDashboard = () => (
    <div className="dashboard-stats">
      <h3>System Statistics</h3>
      {dashboardStats && (
        <div className="stats-grid">
          <div className="stat-card">
            <FontAwesomeIcon icon={faUsers} className="stat-icon" />
            <div className="stat-info">
              <h4>Users</h4>
              <p className="stat-number">{dashboardStats.users.total}</p>
              <p className="stat-detail">
                {dashboardStats.users.premium} premium • {dashboardStats.users.admins} admins
              </p>
            </div>
          </div>
          
          <div className="stat-card">
            <FontAwesomeIcon icon={faQuoteLeft} className="stat-icon" />
            <div className="stat-info">
              <h4>Quizzes</h4>
              <p className="stat-number">{dashboardStats.quizzes.total}</p>
            </div>
          </div>
          
          <div className="stat-card">
            <FontAwesomeIcon icon={faCreditCard} className="stat-icon" />
            <div className="stat-info">
              <h4>Payments</h4>
              <p className="stat-number">{dashboardStats.payments.pending_offline}</p>
              <p className="stat-detail">Pending approval</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderUsers = () => (
    <div className="users-management">
      <h3>User Management</h3>
      <div className="users-table">
        {users.map(user => (
          <div key={user.id} className="user-row">
            <div className="user-info">
              <img src={user.avatar} alt={user.username} className="user-avatar" />
              <div>
                <h4>{user.username}</h4>
                <p>{user.email}</p>
                <span className={`role-badge ${user.role}`}>
                  {user.role}
                </span>
              </div>
            </div>
            <div className="user-actions">
              {!user.is_admin ? (
                <button 
                  onClick={() => promoteUser(user.id)}
                  className="btn btn-primary"
                >
                  <FontAwesomeIcon icon={faUserShield} /> Promote to Admin
                </button>
              ) : user.id !== parseInt(user?.id) && (
                <button 
                  onClick={() => demoteUser(user.id)}
                  className="btn btn-secondary"
                >
                  Demote to User
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderPayments = () => (
    <div className="payments-management">
      <h3>Offline Payments</h3>
      <div className="payments-table">
        {offlinePayments.map(payment => (
          <div key={payment.id} className="payment-row">
            <div className="payment-info">
              <h4>{payment.user_name} ({payment.user_email})</h4>
              <p><strong>Amount:</strong> {payment.amount} {payment.currency}</p>
              <p><strong>Description:</strong> {payment.description}</p>
              <p><strong>Status:</strong> 
                <span className={`status-badge ${payment.status}`}>
                  {payment.status}
                </span>
              </p>
              <p><strong>Created:</strong> {new Date(payment.created_at).toLocaleDateString()}</p>
            </div>
            
            {payment.status === 'pending' && (
              <div className="payment-actions">
                <button 
                  onClick={() => approvePayment(payment.id)}
                  className="btn btn-success"
                >
                  <FontAwesomeIcon icon={faCheck} /> Approve
                </button>
                <button 
                  onClick={() => rejectPayment(payment.id)}
                  className="btn btn-danger"
                >
                  <FontAwesomeIcon icon={faTimes} /> Reject
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
  const renderFailedPayments = () => (
    <div className="failed-payments-management">
      <h3>Failed Payments</h3>
      
      {failedPayments?.payments?.length > 0 && (
        <div className="failed-payments-section">
          <h4>Failed Payment Intents</h4>
          <div className="payments-table">
            {failedPayments.payments.map(payment => (
              <div key={`payment-${payment.id}`} className="payment-row">
                <div className="payment-info">
                  <h4>Payment Intent: {payment.stripe_payment_intent_id}</h4>
                  <p><strong>Amount:</strong> ${payment.amount}</p>
                  <p><strong>Status:</strong> 
                    <span className={`status-badge ${payment.status}`}>
                      {payment.status}
                    </span>
                  </p>
                  <p><strong>Type:</strong> {payment.type}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {failedPayments?.subscriptions?.length > 0 && (
        <div className="failed-subscriptions-section">
          <h4>Failed Subscriptions</h4>
          <div className="payments-table">
            {failedPayments.subscriptions.map(subscription => (
              <div key={`subscription-${subscription.id}`} className="payment-row">
                <div className="payment-info">
                  <h4>{subscription.user_name} ({subscription.user_email})</h4>
                  <p><strong>Status:</strong> 
                    <span className={`status-badge ${subscription.status}`}>
                      {subscription.status}
                    </span>
                  </p>
                  <p><strong>Failed Attempts:</strong> {subscription.failed_payment_count}</p>
                  <p><strong>Period End:</strong> {subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : 'N/A'}</p>
                  <p><strong>Type:</strong> {subscription.type}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {(!failedPayments?.payments?.length && !failedPayments?.subscriptions?.length) && (
        <div className="no-failed-payments">
          <p>No failed payments found.</p>
        </div>
      )}
    </div>
  );

  if (!user || !user.is_admin) {
    return null; // Will redirect via useEffect
  }

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <button 
          className="back-button" 
          onClick={() => navigate('/home')}
        >
          <FontAwesomeIcon icon={faArrowLeft} /> Back to Home
        </button>
        <h1>Admin Panel</h1>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div className="admin-tabs">
        <button 
          className={`tab ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          <FontAwesomeIcon icon={faChartBar} /> Dashboard
        </button>
        <button 
          className={`tab ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          <FontAwesomeIcon icon={faUsers} /> Users
        </button>
        <button 
          className={`tab ${activeTab === 'payments' ? 'active' : ''}`}
          onClick={() => setActiveTab('payments')}
        >
          <FontAwesomeIcon icon={faCreditCard} /> Offline Payments
        </button>
        <button 
          className={`tab ${activeTab === 'failed-payments' ? 'active' : ''}`}
          onClick={() => setActiveTab('failed-payments')}
        >
          Failed Payments
        </button>
      </div>

      <div className="admin-content">
        {loading ? (
          <div className="loading">Loading...</div>
        ) : (
          <>
            {activeTab === 'dashboard' && renderDashboard()}
            {activeTab === 'users' && renderUsers()}
            {activeTab === 'payments' && renderPayments()}
            {activeTab === 'failed-payments' && renderFailedPayments()}
          </>
        )}
      </div>
    </div>
  );
};

export default AdminPanel;
