import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { Footer } from './Footer';
import { useAuth } from '../../context/AuthContext';
import { Toast } from '../common/Toast';

export const AppShell: React.FC = () => {
  const { sessionExpiredToast, dismissSessionToast } = useAuth();

  return (
    <div className="min-h-screen flex flex-col bg-bg text-text">
      <Navbar />

      {sessionExpiredToast && (
        <Toast
          type="warning"
          message="Session expired, please sign in again"
          onClose={dismissSessionToast}
        />
      )}

      <main className="flex-grow w-full max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      <Footer />
    </div>
  );
};
