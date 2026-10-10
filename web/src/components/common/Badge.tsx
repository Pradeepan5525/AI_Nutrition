import React from 'react';

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'neutral' | 'accent';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  className = '',
}) => {
  const variantStyles: Record<BadgeVariant, string> = {
    // Green accent = active / success / low risk
    success: 'bg-primary-soft text-primary border border-primary/20',
    // Amber = medium priority / pending / warning
    warning: 'bg-warning-soft text-warning border border-warning/20',
    // Red = high risk / danger / error
    danger: 'bg-danger-soft text-danger border border-danger/20',
    // Slate gray = neutral / informational
    neutral: 'bg-bg text-muted border border-border',
    // Bright green accent for confidence / highlights
    accent: 'bg-primary text-white font-medium',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
