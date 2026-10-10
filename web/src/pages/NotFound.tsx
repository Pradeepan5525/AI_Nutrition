import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, FileQuestion } from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

export const NotFound: React.FC = () => {
  return (
    <div className="min-h-[60vh] flex items-center justify-center py-12">
      <Card className="max-w-md w-full text-center p-8 space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-primary-soft text-primary flex items-center justify-center mx-auto">
          <FileQuestion className="w-6 h-6 text-primary" />
        </div>
        <h1 className="text-3xl font-extrabold text-text tracking-tight">404</h1>
        <h2 className="text-base font-bold text-text">Page Not Found</h2>
        <p className="text-xs text-muted leading-relaxed">
          The requested nutritional module or page does not exist or has been relocated.
        </p>
        <div className="pt-2">
          <Link to="/dashboard">
            <Button variant="primary" size="md" leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Return to Dashboard
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
};
