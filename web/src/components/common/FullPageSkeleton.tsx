import React from 'react';

export const FullPageSkeleton: React.FC = () => {
  return (
    <div className="min-h-screen bg-bg flex flex-col items-center justify-center p-6 space-y-6 animate-pulse">
      {/* Logo & Spinner */}
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-primary-soft flex items-center justify-center border border-primary/20">
          <div className="w-4 h-4 rounded-full border-2 border-primary border-t-transparent animate-spin" />
        </div>
        <div>
          <div className="h-4 w-28 bg-border rounded" />
          <div className="h-2.5 w-16 bg-border/60 rounded mt-1.5" />
        </div>
      </div>

      {/* Main Skeleton Card */}
      <div className="w-full max-w-md bg-surface rounded-card border border-border p-8 space-y-4 shadow-soft">
        <div className="h-5 w-40 bg-border rounded mx-auto" />
        <div className="h-3 w-56 bg-border/60 rounded mx-auto" />
        <div className="space-y-3 pt-4">
          <div className="h-10 w-full bg-bg rounded-xl border border-border" />
          <div className="h-10 w-full bg-bg rounded-xl border border-border" />
          <div className="h-11 w-full bg-primary/20 rounded-xl" />
        </div>
      </div>
    </div>
  );
};
