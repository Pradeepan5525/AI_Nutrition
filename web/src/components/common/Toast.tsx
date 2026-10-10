import React from 'react';
import { AlertCircle, CheckCircle, Info, X } from 'lucide-react';

export type ToastType = 'info' | 'success' | 'warning' | 'danger';

interface ToastProps {
  message: string;
  type?: ToastType;
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({
  message,
  type = 'warning',
  onClose,
}) => {
  const icons = {
    info: <Info className="w-5 h-5 text-primary" />,
    success: <CheckCircle className="w-5 h-5 text-primary" />,
    warning: <AlertCircle className="w-5 h-5 text-warning" />,
    danger: <AlertCircle className="w-5 h-5 text-danger" />,
  };

  const borders = {
    info: 'border-primary/20 bg-primary-soft',
    success: 'border-primary/20 bg-primary-soft',
    warning: 'border-warning/30 bg-warning-soft',
    danger: 'border-danger/30 bg-danger-soft',
  };

  return (
    <div
      role="status"
      className={`fixed top-5 right-5 z-50 flex items-center gap-3 px-4 py-3 rounded-card border shadow-lg max-w-md ${borders[type]} animate-in slide-in-from-top-2 duration-200`}
    >
      <div className="flex-shrink-0">{icons[type]}</div>
      <div className="text-sm font-medium text-text flex-grow">{message}</div>
      <button
        onClick={onClose}
        className="text-muted hover:text-text p-1 rounded-md transition-colors"
        aria-label="Dismiss toast"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};
