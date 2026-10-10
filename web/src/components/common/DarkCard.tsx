import React from 'react';

interface DarkCardProps {
  children: React.ReactNode;
  className?: string;
}

export const DarkCard: React.FC<DarkCardProps> = ({ children, className = '' }) => {
  return (
    <div
      className={`hero-gradient text-white rounded-card p-6 shadow-md border border-primary/20 ${className}`}
    >
      {children}
    </div>
  );
};
