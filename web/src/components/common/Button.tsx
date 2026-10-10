import React from 'react';

export type ButtonVariant = 'primary' | 'outline' | 'ghost' | 'danger';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  disabled,
  className = '',
  ...props
}) => {
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-xs font-medium rounded-lg',
    md: 'px-4 py-2 text-sm font-semibold rounded-xl',
    lg: 'px-6 py-3 text-base font-semibold rounded-xl',
  };

  const variantStyles = {
    // Solid green primary button with WCAG AA compliance
    primary:
      'bg-primary text-white hover:bg-primary-hover shadow-sm active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed',
    // Outlined button with 1px border
    outline:
      'bg-surface text-text border border-border hover:bg-bg active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed',
    // Minimal ghost button
    ghost:
      'bg-transparent text-muted hover:text-text hover:bg-bg disabled:opacity-50 disabled:cursor-not-allowed',
    // Danger button
    danger:
      'bg-danger-soft text-danger hover:bg-danger hover:text-white border border-danger/30 disabled:opacity-50 disabled:cursor-not-allowed',
  };

  return (
    <button
      disabled={disabled || isLoading}
      className={`inline-flex items-center justify-center transition-all duration-150 select-none ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {isLoading ? (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      ) : (
        leftIcon && <span className="mr-2 inline-flex items-center">{leftIcon}</span>
      )}
      <span>{children}</span>
      {!isLoading && rightIcon && (
        <span className="ml-2 inline-flex items-center">{rightIcon}</span>
      )}
    </button>
  );
};
