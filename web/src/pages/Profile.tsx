import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User,
  KeyRound,
  Download,
  Trash2,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/endpoints';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { DisclaimerNotice } from '../components/common/DisclaimerNotice';

export const Profile: React.FC = () => {
  const { user, updateUser, logout } = useAuth();
  const navigate = useNavigate();

  const profile = user?.profile || user?.saved_profile || {};

  // Form State
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [age, setAge] = useState(profile.age || 30);
  const [sex, setSex] = useState(profile.sex || 'male');
  const [heightCm, setHeightCm] = useState(profile.height_cm || 175);
  const [weightKg, setWeightKg] = useState(profile.weight_kg || 72);
  const [activityLevel, setActivityLevel] = useState(profile.activity_level || 'moderate');
  const [goal, setGoal] = useState(profile.goal || 'maintenance');
  const [preferredCuisine, setPreferredCuisine] = useState(profile.preferred_cuisine || 'Balanced Mediterranean');

  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);
  const [profileSuccessMsg, setProfileSuccessMsg] = useState<string | null>(null);

  // Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [pwdMsg, setPwdMsg] = useState<{ text: string; isError: boolean } | null>(null);

  // Data export & account deletion
  const [isExporting, setIsExporting] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUpdatingProfile(true);
    setProfileSuccessMsg(null);
    try {
      const updatedProfile = {
        age: Number(age),
        sex,
        height_cm: Number(heightCm),
        weight_kg: Number(weightKg),
        activity_level: activityLevel,
        goal,
        preferred_cuisine: preferredCuisine,
        onboarding_completed: true,
      };

      const updatedUser = await api.users.updateProfile(updatedProfile);
      updateUser(updatedUser);
      setProfileSuccessMsg('Profile and metabolic telemetry updated successfully.');
    } catch (err: any) {
      setProfileSuccessMsg(err.message || 'Failed to update profile.');
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwdMsg(null);

    if (newPassword.length < 8) {
      setPwdMsg({ text: 'New password must be at least 8 characters long.', isError: true });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwdMsg({ text: 'New passwords do not match.', isError: true });
      return;
    }

    setIsChangingPassword(true);
    try {
      await api.users.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPwdMsg({ text: 'Password changed successfully.', isError: false });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setPwdMsg({ text: err.message || 'Failed to change password.', isError: true });
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleExportData = async () => {
    setIsExporting(true);
    try {
      const data = await api.users.exportData();
      const jsonStr = JSON.stringify(data, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `nutriintel_data_export_${user?.id || 'me'}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
    } finally {
      setIsExporting(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText.toLowerCase() !== 'delete') return;

    setIsDeleting(true);
    try {
      await api.users.deleteAccount();
      await logout();
      navigate('/login', { replace: true });
    } catch (err) {
      console.error(err);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <Card className="p-6">
        <div className="flex items-center space-x-2 mb-2">
          <Badge variant="accent">Account Settings</Badge>
          <Badge variant="neutral">GDPR &amp; HIPAA Data Rights</Badge>
        </div>
        <h1 className="text-2xl font-bold text-text">Account Profile &amp; Privacy</h1>
        <p className="text-xs sm:text-sm text-muted mt-1">
          Manage your personal anthropometric parameters, update credentials, and exercise data
          portability or deletion rights.
        </p>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Profile Settings Form */}
        <div className="lg:col-span-7 space-y-6">
          <Card className="p-6">
            <h2 className="text-sm font-bold text-text uppercase tracking-wider mb-4 flex items-center">
              <User className="w-4 h-4 mr-2 text-primary" />
              Anthropometric &amp; Clinical Parameters
            </h2>

            {profileSuccessMsg && (
              <div className="mb-4 p-3 rounded-xl bg-primary-soft border border-primary/20 text-xs font-semibold text-primary flex items-center">
                <CheckCircle2 className="w-4 h-4 mr-1.5 text-primary" />
                {profileSuccessMsg}
              </div>
            )}

            <form onSubmit={handleUpdateProfile} className="space-y-4 text-xs">
              <div>
                <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  disabled
                  value={user?.email || ''}
                  className="w-full px-3.5 py-2 rounded-xl border border-border bg-bg text-muted cursor-not-allowed"
                />
                <span className="text-[10px] text-muted block mt-0.5">
                  Email is immutable for clinical record security.
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                    Age (Years)
                  </label>
                  <input
                    type="number"
                    min="18"
                    max="110"
                    value={age}
                    onChange={(e) => setAge(Number(e.target.value))}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                    Biological Sex
                  </label>
                  <select
                    value={sex}
                    onChange={(e) => setSex(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                    Height (cm)
                  </label>
                  <input
                    type="number"
                    min="100"
                    max="250"
                    value={heightCm}
                    onChange={(e) => setHeightCm(Number(e.target.value))}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                    Weight (kg)
                  </label>
                  <input
                    type="number"
                    min="35"
                    max="250"
                    step="0.5"
                    value={weightKg}
                    onChange={(e) => setWeightKg(Number(e.target.value))}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                    Activity Multiplier
                  </label>
                  <select
                    value={activityLevel}
                    onChange={(e) => setActivityLevel(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  >
                    <option value="sedentary">Sedentary (1.2x)</option>
                    <option value="light">Lightly Active (1.375x)</option>
                    <option value="moderate">Moderately Active (1.55x)</option>
                    <option value="active">Very Active (1.725x)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                    Primary Goal
                  </label>
                  <select
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                  >
                    <option value="weight_loss">Weight Loss (-500 kcal)</option>
                    <option value="maintenance">Maintenance</option>
                    <option value="muscle_gain">Muscle Gain (+300 kcal)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                  Preferred Cuisine Style
                </label>
                <select
                  value={preferredCuisine}
                  onChange={(e) => setPreferredCuisine(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                >
                  <option value="Balanced Mediterranean">Balanced Mediterranean</option>
                  <option value="Indian Traditional">Indian Traditional</option>
                  <option value="Asian Fusion">Asian Fusion</option>
                  <option value="Low-GI Diabetic Friendly">Low-GI Diabetic Friendly</option>
                  <option value="High-Protein Athletic">High-Protein Athletic</option>
                </select>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={isUpdatingProfile}
                className="w-full mt-2"
              >
                Save Profile Parameters
              </Button>
            </form>
          </Card>
        </div>

        {/* Right Column: Password, Data Export, and Account Deletion */}
        <div className="lg:col-span-5 space-y-6">
          {/* Change Password Card */}
          <Card className="p-6">
            <h2 className="text-sm font-bold text-text uppercase tracking-wider mb-4 flex items-center">
              <KeyRound className="w-4 h-4 mr-2 text-primary" />
              Change Password
            </h2>

            {pwdMsg && (
              <div
                className={`mb-4 p-3 rounded-xl border text-xs font-semibold ${
                  pwdMsg.isError
                    ? 'bg-danger-soft border-danger/30 text-danger'
                    : 'bg-primary-soft border-primary/20 text-primary'
                }`}
              >
                {pwdMsg.text}
              </div>
            )}

            <form onSubmit={handleChangePassword} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                  Current Password
                </label>
                <input
                  type="password"
                  required
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                  New Password (Min 8 Chars)
                </label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-muted uppercase mb-1">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-border bg-surface text-text text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                />
              </div>

              <Button
                type="submit"
                variant="outline"
                size="md"
                isLoading={isChangingPassword}
                className="w-full mt-2"
              >
                Update Password
              </Button>
            </form>
          </Card>

          {/* Privacy Note & Data Rights Card */}
          <Card className="p-6">
            <h2 className="text-sm font-bold text-text uppercase tracking-wider mb-2 flex items-center">
              <ShieldCheck className="w-4 h-4 mr-2 text-primary" />
              Privacy &amp; Data Rights
            </h2>

            <div className="p-3.5 rounded-xl bg-bg border border-border text-xs text-muted leading-relaxed mb-4">
              <strong className="text-text block mb-1">Privacy Notice:</strong>
              We adhere strictly to data minimization standards. Only anthropometric inputs required for
              macronutrient formulations and habit risk modeling are preserved.
            </div>

            <div className="space-y-3">
              <Button
                type="button"
                variant="outline"
                size="md"
                onClick={handleExportData}
                isLoading={isExporting}
                className="w-full justify-center"
                leftIcon={<Download className="w-4 h-4 text-primary" />}
              >
                Export My Data (JSON)
              </Button>

              <Button
                type="button"
                variant="danger"
                size="md"
                onClick={() => setDeleteModalOpen(true)}
                className="w-full justify-center"
                leftIcon={<Trash2 className="w-4 h-4" />}
              >
                Delete My Account
              </Button>
            </div>
          </Card>
        </div>
      </div>

      {/* Account Deletion Confirmation Modal */}
      <Modal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Permanently Delete Account"
      >
        <div className="space-y-4 text-xs">
          <div className="p-3.5 rounded-xl bg-danger-soft border border-danger/30 text-danger flex items-start space-x-2.5">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="block text-sm">Warning: This action is irreversible.</strong>
              All your anthropometric profiles, saved meal plans, risk screenings, weight logs, and
              credentials will be permanently expunged.
            </div>
          </div>

          <p className="text-muted leading-relaxed">
            Please type <strong className="text-text font-mono">delete</strong> below to confirm.
          </p>

          <input
            type="text"
            value={deleteConfirmText}
            onChange={(e) => setDeleteConfirmText(e.target.value)}
            placeholder="Type 'delete' to confirm"
            className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-surface text-text text-sm focus:border-danger focus:ring-1 focus:ring-danger"
          />

          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-border">
            <Button variant="outline" size="md" onClick={() => setDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              size="md"
              disabled={deleteConfirmText.toLowerCase() !== 'delete'}
              isLoading={isDeleting}
              onClick={handleDeleteAccount}
            >
              Permanently Expunge My Data
            </Button>
          </div>
        </div>
      </Modal>

      <DisclaimerNotice />
    </div>
  );
};
