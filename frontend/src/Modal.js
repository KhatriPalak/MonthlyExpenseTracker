import React from 'react';
import './Modal.css';

const Modal = ({ 
  show, 
  onClose, 
  title, 
  message, 
  type = 'info', // 'info', 'success', 'error', 'confirm'
  onConfirm = null,
  confirmText = 'OK',
  cancelText = 'Cancel'
}) => {
  if (!show) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'confirm':
        return '?';
      default:
        return 'ℹ';
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className={`modal-content modal-${type}`}>
        <div className="modal-header">
          <div className="modal-icon">{getIcon()}</div>
          <h3 className="modal-title">{title}</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <p>{message}</p>
        </div>
        <div className="modal-footer">
          {type === 'confirm' ? (
            <>
              <button className="modal-btn modal-btn-cancel" onClick={onClose}>
                {cancelText}
              </button>
              <button className="modal-btn modal-btn-confirm" onClick={onConfirm}>
                {confirmText}
              </button>
            </>
          ) : (
            <button className="modal-btn modal-btn-primary" onClick={onClose}>
              {confirmText}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Modal;