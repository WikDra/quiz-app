import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSignOut, faExclamationTriangle } from '@fortawesome/free-solid-svg-icons';

const LogoutConfirmationModal = ({ 
  isOpen = true, 
  onConfirm, 
  onCancel, 
  isLoading = false 
}) => {
  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm();
  };

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content logout-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <FontAwesomeIcon icon={faExclamationTriangle} className="warning-icon" />
          <h3>Potwierdź wylogowanie</h3>
        </div>
        
        <div className="modal-body">
          <p>Czy na pewno chcesz się wylogować?</p>
        </div>
        
        <div className="modal-footer">
          <button 
            className="btn btn-secondary" 
            onClick={onCancel}
            disabled={isLoading}
          >
            Anuluj
          </button>
          <button 
            className="btn btn-danger" 
            onClick={handleConfirm}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <div className="spinner-small"></div>
                Wylogowywanie...
              </>
            ) : (
              <>
                <FontAwesomeIcon icon={faSignOut} />
                Wyloguj
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LogoutConfirmationModal;
