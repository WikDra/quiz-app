import React, { memo } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';

// Komponent ładowania
export const LoadingSpinner = memo(({ message = 'Ładowanie...' }) => (
  <div className="loading-container">
    <div className="spinner"></div>
    <p>{message}</p>
  </div>
));

// Komponent komunikatu o błędzie
export const ErrorMessage = memo(({ message, onRetry }) => (
  <div className="error-container">
    <h3>Błąd</h3>
    <p>{message}</p>
    {onRetry && (
      <button onClick={onRetry} className="retry-button">
        Spróbuj ponownie
      </button>
    )}
  </div>
));

// Komponent przycisku
export const Button = memo(({ 
  onClick, 
  disabled, 
  className, 
  icon, 
  children,
  type = 'button',
  loading = false
}) => (
  <button
    type={type}
    className={`custom-button ${className || ''} ${loading ? 'loading' : ''}`}
    onClick={onClick}
    disabled={disabled || loading}
  >
    {loading ? (
      <div className="button-spinner"></div>
    ) : (
      <>
        {icon && <FontAwesomeIcon icon={icon} />}
        {children}
      </>
    )}
  </button>
));

// Komponent nagłówka sekcji
export const SectionHeader = memo(({ 
  title, 
  subtitle,
  rightContent 
}) => (
  <div className="section-header">
    <div className="section-header-left">
      <h2>{title}</h2>
      {subtitle && <p className="section-subtitle">{subtitle}</p>}
    </div>
    {rightContent && (
      <div className="section-header-right">
        {rightContent}
      </div>
    )}
  </div>
));

// Komponent pustego stanu
export const EmptyState = memo(({ 
  icon, 
  title, 
  description, 
  action 
}) => (
  <div className="empty-state">
    {icon && <FontAwesomeIcon icon={icon} className="empty-state-icon" />}
    <h3>{title}</h3>
    {description && <p>{description}</p>}
    {action}
  </div>
));

// Komponent potwierdzenia
export const ConfirmDialog = memo(({ 
  isOpen, 
  title, 
  message, 
  confirmLabel = 'Potwierdź',
  cancelLabel = 'Anuluj',
  onConfirm,
  onCancel,
  variant = 'default' // 'default' | 'danger' | 'warning'
}) => {
  if (!isOpen) return null;

  return (
    <div className="confirm-dialog-overlay">
      <div className={`confirm-dialog ${variant}`}>
        <h3>{title}</h3>
        <p>{message}</p>
        <div className="confirm-dialog-actions">
          <Button 
            onClick={onCancel}
            className="cancel-button"
          >
            {cancelLabel}
          </Button>
          <Button 
            onClick={onConfirm}
            className={`confirm-button ${variant}`}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
});

// Komponent paginacji
export const Pagination = memo(({ 
  currentPage, 
  totalPages, 
  onPageChange 
}) => {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);
  
  return (
    <div className="pagination">
      <Button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="pagination-button"
      >
        Poprzednia
      </Button>
      
      {pages.map(page => (
        <Button
          key={page}
          onClick={() => onPageChange(page)}
          className={`pagination-button ${currentPage === page ? 'active' : ''}`}
        >
          {page}
        </Button>
      ))}
      
      <Button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="pagination-button"
      >
        Następna
      </Button>
    </div>
  );
});