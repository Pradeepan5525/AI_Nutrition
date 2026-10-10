import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverEffect?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  onClick,
  hoverEffect = false,
}) => {
  return (
    <div
      onClick={onClick}
      className={`bg-surface border border-border rounded-card shadow-soft p-5 sm:p-6 ${
        hoverEffect ? 'card-hover-border cursor-pointer' : ''
      } ${className}`}
    >
      {children}
    </div>
  );
};
