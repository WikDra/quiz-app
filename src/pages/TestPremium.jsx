import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../utils/constants';
import { useNavigate } from 'react-router-dom';

// Inline styles
const styles = {
  container: {
    maxWidth: '800px',
    margin: '2rem auto',
    padding: '2rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '8px',
    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)'
  },
  header: {
    color: '#2c3e50',
    textAlign: 'center',
    marginBottom: '2rem',
    fontSize: '2rem'
  },
  card: {
    background: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.05)',
    marginBottom: '2rem'
  },
  cardHeader: {
    color: '#3498db',
    marginBottom: '1rem'
  },
  statusActive: {
    color: '#27ae60',
    fontWeight: 'bold'
  },
  statusInactive: {
    color: '#e74c3c',
    fontWeight: 'bold'
  },
  button: {
    display: 'block',
    width: '100%',
    padding: '1rem',
    margin: '1.5rem 0',
    border: 'none',
    borderRadius: '4px',
    fontSize: '1rem',
    fontWeight: 'bold',
    cursor: 'pointer'
  },
  buttonActivate: {
    backgroundColor: '#2ecc71',
    color: 'white'
  },
  buttonDeactivate: {
    backgroundColor: '#e74c3c',
    color: 'white'
  },
  buttonDisabled: {
    backgroundColor: '#95a5a6',
    cursor: 'not-allowed'
  },
  statusMessage: {
    padding: '1rem',
    marginTop: '1rem',
    borderRadius: '4px',
    textAlign: 'center'
  },
  statusSuccess: {
    backgroundColor: '#d5f5e3',
    color: '#27ae60'
  },
  statusError: {
    backgroundColor: '#fadbd8',
    color: '#e74c3c'
  },
  navigationLinks: {
    display: 'flex',
    justifyContent: 'space-around',
    marginTop: '2rem'
  },
  navLink: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#3498db',
    color: 'white',
    textDecoration: 'none',
    borderRadius: '4px'
  }
};

function TestPremium() {
  const { user, refreshUserState } = useAuth();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [webhookEvent, setWebhookEvent] = useState('checkout.session.completed');
  const [webhookStatus, setWebhookStatus] = useState(null);
  const [webhookLoading, setWebhookLoading] = useState(false);
  const navigate = useNavigate();

  const togglePremiumStatus = async () => {
    try {
      setLoading(true);
      setStatus(null);

      const response = await fetch(`${API_BASE_URL}/api/test/update_premium`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      const data = await response.json();
      
      if (response.ok) {
        setStatus({
          success: true,
          message: data.message
        });
        // Update the user state to reflect the change
        if (refreshUserState) {
          await refreshUserState();
        }
      } else {
        setStatus({
          success: false,
          message: data.error || 'Wystąpił błąd podczas aktualizacji statusu premium'
        });
      }
    } catch (error) {
      console.error('Error toggling premium status:', error);
      setStatus({
        success: false,
        message: 'Wystąpił błąd sieciowy podczas aktualizacji statusu premium'
      });
    } finally {
      setLoading(false);
    }
  };

  const simulateWebhook = async (eventType) => {
    if (!user) {
      return;
    }

    try {
      setWebhookLoading(true);
      setWebhookStatus(null);

      const response = await fetch(`${API_BASE_URL}/api/test/webhook-simulation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          event_type: eventType,
          user_id: user.id
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setWebhookStatus({
          success: true,
          message: `Webhook event ${eventType} processed successfully. Premium status is now ${data.has_premium_access ? 'ACTIVE' : 'INACTIVE'}`
        });
        
        // Update the user state to reflect the change
        if (refreshUserState) {
          await refreshUserState();
        }
      } else {
        setWebhookStatus({
          success: false,
          message: data.error || 'Failed to process webhook simulation'
        });
      }
    } catch (error) {
      console.error('Error simulating webhook:', error);
      setWebhookStatus({
        success: false,
        message: 'Error connecting to server'
      });
    } finally {
      setWebhookLoading(false);
    }
  };

  // Function to test the complete payment flow
  const testCompletePremiumFlow = async () => {
    try {
      setWebhookLoading(true);
      setWebhookStatus({
        success: true, 
        message: "Starting complete premium flow test..."
      });
      
      // Step 1: Ensure user has premium deactivated first
      if (user?.has_premium_access) {
        await simulateWebhook('customer.subscription.deleted');
        await new Promise(resolve => setTimeout(resolve, 500)); // Small delay
      }
      
      // Step 2: Simulate checkout completion webhook
      await simulateWebhook('checkout.session.completed');
      
      setWebhookStatus({
        success: true, 
        message: "Complete premium flow test completed successfully."
      });
      
    } catch (error) {
      console.error('Error testing complete premium flow:', error);
      setWebhookStatus({
        success: false,
        message: 'Error during complete premium flow test'
      });
    } finally {
      setWebhookLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.header}>Panel Testowy Premium</h1>
      
      <div style={styles.card}>
        <h2 style={styles.cardHeader}>Status Premium</h2>        <p>Aktualny status: <span style={user?.has_premium_access ? styles.statusActive : styles.statusInactive}>
          {user?.has_premium_access ? 'AKTYWNY' : 'NIEAKTYWNY'}
        </span></p>
        {user?.premium_since && (
          <p>Data aktywacji: <span style={{color: '#2c3e50', fontWeight: 'bold'}}>
            {new Date(user.premium_since).toLocaleString()}
          </span></p>
        )}
        
        <button 
          onClick={togglePremiumStatus} 
          disabled={loading}
          style={{
            ...styles.button,
            ...(user?.has_premium_access ? styles.buttonDeactivate : styles.buttonActivate),
            ...(loading ? styles.buttonDisabled : {})
          }}
        >
          {loading ? 'Przetwarzanie...' : user?.has_premium_access ? 'Wyłącz premium' : 'Włącz premium'}
        </button>
        
        {status && (
          <div style={{
            ...styles.statusMessage,
            ...(status.success ? styles.statusSuccess : styles.statusError)
          }}>
            {status.message}
          </div>
        )}
      </div>
      
      <div style={styles.navigationLinks}>
        <Link to="/user-settings" style={styles.navLink}>
          Powrót do ustawień
        </Link>
        <Link to="/" style={styles.navLink}>
          Strona główna
        </Link>
      </div>        <div style={{marginTop: '2rem'}}>
          <h2 style={styles.cardHeader}>Symulacja Webhooków</h2>
          <p>Ta sekcja pozwala na symulację otrzymania webhooków od Stripe bez konieczności konfiguracji rzeczywistych webhooków.</p>
          
          <div style={{display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1.5rem'}}>
            <button 
              onClick={() => simulateWebhook('checkout.session.completed')}
              disabled={webhookLoading}
              style={{
                ...styles.button,
                backgroundColor: '#4CAF50',
                color: 'white',
                ...(webhookLoading ? styles.buttonDisabled : {})
              }}
            >
              Symuluj aktywację premium
            </button>
            
            <button 
              onClick={() => simulateWebhook('customer.subscription.deleted')}
              disabled={webhookLoading}
              style={{
                ...styles.button,
                backgroundColor: '#F44336',
                color: 'white',
                ...(webhookLoading ? styles.buttonDisabled : {})
              }}
            >
              Symuluj anulowanie subskrypcji
            </button>
          </div>
          
          <button 
            onClick={testCompletePremiumFlow}
            disabled={webhookLoading}
            style={{
              ...styles.button,
              backgroundColor: '#2196F3',
              color: 'white',
              marginTop: '1rem',
              ...(webhookLoading ? styles.buttonDisabled : {})
            }}
          >
            Przetestuj pełny proces premium
          </button>
          
          {webhookStatus && (
            <div style={{
              ...styles.statusMessage,
              ...(webhookStatus.success ? styles.statusSuccess : styles.statusError),
              marginTop: '1.5rem'
            }}>
              {webhookStatus.message}
            </div>
          )}
          
          <div style={{margin: '2rem 0', padding: '1rem', backgroundColor: '#f1f1f1', borderRadius: '8px'}}>
            <h3 style={{margin: '0 0 1rem 0'}}>Konfiguracja rzeczywistych webhooków:</h3>
            <ol style={{textAlign: 'left', lineHeight: '1.5', paddingLeft: '1.5rem'}}>
              <li>Uzyskaj prawidłowy webhook secret ze swojego panelu Stripe</li>
              <li>Uruchom skrypt konfiguracyjny: <code>python -m backend.utils.update_webhook_secret</code></li>
              <li>Wprowadź sekret zaczynający się od <code>whsec_</code></li>
              <li>Zrestartuj serwer aplikacji</li>
            </ol>
            <div style={{margin: '1rem 0', padding: '0.75rem', backgroundColor: '#fff9c2', borderRadius: '4px', textAlign: 'left'}}>
              <p style={{margin: 0}}><strong>Uwaga:</strong> Aktualny sekret w pliku <code>.env</code> wymaga aktualizacji do rzeczywistego sekretu z panelu Stripe.</p>
            </div>
          </div>
        </div>
    </div>
  );
}

export default TestPremium;
