import React from 'react';
import { ShieldAlert } from 'lucide-react';

interface DisclaimerNoticeProps {
  className?: string;
  compact?: boolean;
}

export const DisclaimerNotice: React.FC<DisclaimerNoticeProps> = ({
  className = '',
  compact = false,
}) => {
  return (
    <div
      className={`flex items-start gap-2.5 p-3 rounded-xl bg-bg border border-border text-xs text-muted ${className}`}
    >
      <ShieldAlert className="w-4 h-4 text-muted flex-shrink-0 mt-0.5" />
      <div>
        <span className="font-semibold text-text uppercase tracking-wider mr-1.5">
          Educational Notice:
        </span>
        This application provides informational and algorithmic nutritional screening. It does not
        constitute medical diagnosis, prescriptive dietetics, or clinical treatment. Always consult a
        qualified physician or registered dietitian before initiating substantial dietary adjustments.
      </div>
    </div>
  );
};
