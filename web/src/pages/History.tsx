import React, { useState, useEffect } from 'react';
import {
  History as HistoryIcon,
  Trash2,
  Eye,
  Calendar,
  Activity,
  HeartPulse,
  CalendarCheck,
} from 'lucide-react';
import { api } from '../api/endpoints';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { DisclaimerNotice } from '../components/common/DisclaimerNotice';

export const History: React.FC = () => {
  const [filterType, setFilterType] = useState<'all' | 'assess' | 'risk' | 'plan'>('all');
  const [assessments, setAssessments] = useState<any[]>([]);
  const [risks, setRisks] = useState<any[]>([]);
  const [plans, setPlans] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const [selectedItem, setSelectedItem] = useState<any | null>(null);
  const [viewModalOpen, setViewModalOpen] = useState(false);

  useEffect(() => {
    loadAllHistory();
  }, []);

  const loadAllHistory = async () => {
    setIsLoading(true);
    try {
      const [aList, rList, pList] = await Promise.all([
        api.assess.listHistory(),
        api.risk.listHistory(),
        api.plan.listHistory(),
      ]);
      setAssessments(aList || []);
      setRisks(rList || []);
      setPlans(pList || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (type: string, id: number) => {
    if (!confirm('Are you sure you want to delete this historical record?')) return;
    try {
      if (type === 'assess') await api.assess.delete(id);
      if (type === 'risk') await api.risk.delete(id);
      if (type === 'plan') await api.plan.delete(id);
      await loadAllHistory();
    } catch (err) {
      console.error(err);
    }
  };

  // Combine and sort chronologically
  const unifiedHistory = [
    ...assessments.map((a) => ({
      ...a,
      recordType: 'assess',
      typeLabel: 'Health Assessment',
      summary: `BMI ${a.bmi} (${a.bmi_category}) &bull; ${Math.round(a.target_kcal)} kcal`,
      badgeVariant: 'accent' as const,
    })),
    ...risks.map((r) => ({
      ...r,
      recordType: 'risk',
      typeLabel: 'Lifestyle Risk Screening',
      summary: `Predicted ${r.predicted_tier} (${Math.round((r.confidence || 0) * 100)}% conf)`,
      badgeVariant: 'warning' as const,
    })),
    ...plans.map((p) => ({
      ...p,
      recordType: 'plan',
      typeLabel: 'Optimized Meal Plan',
      summary: `${p.days}-day schedule &bull; ${Math.round(p.target_kcal)} kcal/day`,
      badgeVariant: 'success' as const,
    })),
  ].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

  const filtered =
    filterType === 'all' ? unifiedHistory : unifiedHistory.filter((h) => h.recordType === filterType);

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card className="p-6">
        <div className="flex items-center space-x-2 mb-2">
          <Badge variant="accent">User Telemetry</Badge>
          <Badge variant="neutral">Historical Records</Badge>
        </div>
        <h1 className="text-2xl font-bold text-text">Saved Clinical &amp; Nutrition History</h1>
        <p className="text-xs sm:text-sm text-muted mt-1">
          Review previous anthropometric assessments, lifestyle risk screenings, and LP-generated
          meal plans saved to your account.
        </p>
      </Card>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 border-b border-border pb-3">
        {[
          { id: 'all', label: `All Records (${unifiedHistory.length})` },
          { id: 'assess', label: `Assessments (${assessments.length})` },
          { id: 'risk', label: `Risk Screenings (${risks.length})` },
          { id: 'plan', label: `Meal Plans (${plans.length})` },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setFilterType(t.id as any)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all ${
              filterType === t.id
                ? 'bg-primary text-white shadow-sm'
                : 'bg-surface text-muted hover:text-text border border-border'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* History Table Card */}
      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-bg text-[11px] font-bold text-muted uppercase tracking-wider border-b border-border">
                <th className="py-3 px-4">Date &amp; Time</th>
                <th className="py-3 px-4">Record Type</th>
                <th className="py-3 px-4">Result Summary</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border text-xs text-text">
              {isLoading ? (
                <tr>
                  <td colSpan={4} className="py-10 text-center text-muted">
                    Loading account history...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-10 text-center text-muted">
                    No historical records found for this filter.
                  </td>
                </tr>
              ) : (
                filtered.map((item, idx) => (
                  <tr key={`${item.recordType}-${item.id || idx}`} className="hover:bg-bg/80 transition-colors">
                    <td className="py-3.5 px-4 text-muted flex items-center">
                      <Calendar className="w-3.5 h-3.5 mr-1.5 text-muted" />
                      {new Date(item.created_at).toLocaleString(undefined, {
                        dateStyle: 'medium',
                        timeStyle: 'short',
                      })}
                    </td>
                    <td className="py-3.5 px-4 font-semibold">
                      <Badge variant={item.badgeVariant}>{item.typeLabel}</Badge>
                    </td>
                    <td
                      className="py-3.5 px-4 text-text font-medium"
                      dangerouslySetInnerHTML={{ __html: item.summary }}
                    />
                    <td className="py-3.5 px-4 text-right space-x-1">
                      <button
                        onClick={() => {
                          setSelectedItem(item);
                          setViewModalOpen(true);
                        }}
                        className="p-1.5 rounded-lg text-muted hover:text-primary hover:bg-bg"
                        title="View details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(item.recordType, item.id)}
                        className="p-1.5 rounded-lg text-muted hover:text-danger hover:bg-danger-soft"
                        title="Delete record"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Record View Modal */}
      <Modal
        isOpen={viewModalOpen}
        onClose={() => setViewModalOpen(false)}
        title={selectedItem?.typeLabel || 'Record Details'}
      >
        {selectedItem && (
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-bg border border-border">
              <span className="text-[10px] font-bold text-muted uppercase block">Timestamp</span>
              <span className="font-semibold text-text">
                {new Date(selectedItem.created_at).toLocaleString()}
              </span>
            </div>

            {selectedItem.recordType === 'assess' && (
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2.5 rounded-lg bg-bg border border-border">
                    <span className="text-muted block">BMI</span>
                    <span className="font-bold text-text text-sm">{selectedItem.bmi}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-bg border border-border">
                    <span className="text-muted block">Target Calories</span>
                    <span className="font-bold text-primary text-sm">{Math.round(selectedItem.target_kcal)} kcal</span>
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-bg border border-border">
                  <span className="text-muted block">Macronutrient Splits</span>
                  <span className="text-text font-medium">
                    Protein: {selectedItem.protein_g}g &bull; Carbs: {selectedItem.carbs_g}g &bull; Fat: {selectedItem.fat_g}g
                  </span>
                </div>
              </div>
            )}

            {selectedItem.recordType === 'risk' && (
              <div className="space-y-2">
                <div className="p-3 rounded-lg bg-bg border border-border">
                  <span className="text-muted block">Risk Classification</span>
                  <span className="font-bold text-text text-base">{selectedItem.predicted_tier}</span>
                </div>
                {selectedItem.top_risk_drivers?.length > 0 && (
                  <div className="p-3 rounded-lg bg-warning-soft border border-warning/20">
                    <span className="font-semibold text-warning block mb-1">Risk Factors</span>
                    <ul className="space-y-1 text-muted">
                      {selectedItem.top_risk_drivers.map((d: any, di: number) => (
                        <li key={di}>&bull; {d.factor || d.feature}: {d.explanation}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {selectedItem.recordType === 'plan' && (
              <div className="space-y-2">
                <div className="p-3 rounded-lg bg-bg border border-border">
                  <span className="text-muted block">Plan Scope</span>
                  <span className="font-bold text-text">{selectedItem.days} Days &bull; {Math.round(selectedItem.target_kcal)} kcal/day</span>
                </div>
                <div className="p-3 rounded-lg bg-bg border border-border max-h-48 overflow-y-auto">
                  <span className="font-semibold text-muted block mb-1">Meal Outline</span>
                  {selectedItem.daily_plans?.map((dp: any, dpi: number) => (
                    <div key={dpi} className="text-muted mb-1">
                      Day {dp.day}: ~{dp.daily_totals?.kcal} kcal
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>

      <DisclaimerNotice />
    </div>
  );
};
