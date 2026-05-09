'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Save, User, Target, Shield, Zap } from 'lucide-react';
import api from '@/lib/api';

export default function ProfileSettings() {
  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const res = await api.get('/api/profile');
      return res.data;
    },
  });

  const [formData, setFormData] = useState({
    target_roles: profile?.preferences?.target_roles?.join(', ') || '',
    preferred_locations: profile?.preferences?.preferred_locations?.join(', ') || '',
    min_salary: profile?.preferences?.min_salary || '',
    max_salary: profile?.preferences?.max_salary || '',
    work_mode: profile?.preferences?.work_mode || 'remote',
    experience_level: profile?.preferences?.experience_level || 'mid',
    visa_sponsorship: profile?.preferences?.visa_sponsorship_required || false,
    willing_to_relocate: profile?.preferences?.willing_to_relocate || false,
    notice_period: profile?.preferences?.notice_period_days || 30,
    auto_apply: profile?.auto_apply_rules?.enabled || false,
    min_match_score: profile?.auto_apply_rules?.min_match_score || 0.8,
    max_daily: profile?.auto_apply_rules?.max_daily || 5,
    excluded_companies: profile?.auto_apply_rules?.excluded_companies?.join(', ') || '',
    excluded_industries: profile?.auto_apply_rules?.excluded_industries?.join(', ') || '',
  });

  const updateProfile = useMutation({
    mutationFn: (data: any) => api.put('/api/profile', data),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile.mutate({
      preferences: {
        target_roles: formData.target_roles.split(',').map((s: string) => s.trim()).filter(Boolean),
        preferred_locations: formData.preferred_locations.split(',').map((s: string) => s.trim()).filter(Boolean),
        min_salary: formData.min_salary ? parseInt(formData.min_salary as string) : null,
        max_salary: formData.max_salary ? parseInt(formData.max_salary as string) : null,
        work_mode: formData.work_mode,
        experience_level: formData.experience_level,
        visa_sponsorship_required: formData.visa_sponsorship,
        willing_to_relocate: formData.willing_to_relocate,
        notice_period_days: parseInt(formData.notice_period as string),
      },
      auto_apply_rules: {
        enabled: formData.auto_apply,
        min_match_score: parseFloat(formData.min_match_score as string),
        max_daily: parseInt(formData.max_daily as string),
        excluded_companies: formData.excluded_companies.split(',').map((s: string) => s.trim()).filter(Boolean),
        excluded_industries: formData.excluded_industries.split(',').map((s: string) => s.trim()).filter(Boolean),
      },
    });
  };

  const inputClass = "input text-sm";
  const labelClass = "block text-sm font-medium text-gray-700 mb-1";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
        <p className="text-gray-500 mt-1">Configure your preferences and auto-apply rules</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Preferences */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Target size={20} className="text-primary-600" />
            Job Preferences
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Target Roles (comma-separated)</label>
              <input
                type="text"
                value={formData.target_roles}
                onChange={(e) => setFormData({ ...formData, target_roles: e.target.value })}
                className={inputClass}
                placeholder="AI Engineer, ML Engineer, Data Scientist"
              />
            </div>
            <div>
              <label className={labelClass}>Preferred Locations</label>
              <input
                type="text"
                value={formData.preferred_locations}
                onChange={(e) => setFormData({ ...formData, preferred_locations: e.target.value })}
                className={inputClass}
                placeholder="San Francisco, Remote, New York"
              />
            </div>
            <div>
              <label className={labelClass}>Min Salary (USD)</label>
              <input
                type="number"
                value={formData.min_salary}
                onChange={(e) => setFormData({ ...formData, min_salary: e.target.value })}
                className={inputClass}
                placeholder="100000"
              />
            </div>
            <div>
              <label className={labelClass}>Max Salary (USD)</label>
              <input
                type="number"
                value={formData.max_salary}
                onChange={(e) => setFormData({ ...formData, max_salary: e.target.value })}
                className={inputClass}
                placeholder="200000"
              />
            </div>
            <div>
              <label className={labelClass}>Work Mode</label>
              <select
                value={formData.work_mode}
                onChange={(e) => setFormData({ ...formData, work_mode: e.target.value })}
                className={inputClass}
              >
                <option value="remote">Remote</option>
                <option value="hybrid">Hybrid</option>
                <option value="onsite">On-site</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Experience Level</label>
              <select
                value={formData.experience_level}
                onChange={(e) => setFormData({ ...formData, experience_level: e.target.value })}
                className={inputClass}
              >
                <option value="intern">Intern</option>
                <option value="entry">Entry Level</option>
                <option value="mid">Mid Level</option>
                <option value="senior">Senior</option>
                <option value="staff">Staff</option>
                <option value="principal">Principal</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Notice Period (days)</label>
              <input
                type="number"
                value={formData.notice_period}
                onChange={(e) => setFormData({ ...formData, notice_period: e.target.value })}
                className={inputClass}
              />
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={formData.visa_sponsorship}
                  onChange={(e) => setFormData({ ...formData, visa_sponsorship: e.target.checked })}
                  className="rounded border-gray-300"
                />
                Needs visa sponsorship
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={formData.willing_to_relocate}
                  onChange={(e) => setFormData({ ...formData, willing_to_relocate: e.target.checked })}
                  className="rounded border-gray-300"
                />
                Willing to relocate
              </label>
            </div>
          </div>
        </div>

        {/* Auto Apply Rules */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Zap size={20} className="text-amber-600" />
            Auto-Apply Rules
          </h3>

          <div className="mb-4">
            <label className="flex items-center gap-2 text-sm font-medium">
              <input
                type="checkbox"
                checked={formData.auto_apply}
                onChange={(e) => setFormData({ ...formData, auto_apply: e.target.checked })}
                className="rounded border-gray-300"
              />
              Enable Auto-Apply
            </label>
            <p className="text-xs text-gray-500 mt-1">
              When enabled, the agent will automatically apply to jobs that meet your criteria
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Minimum Match Score</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={formData.min_match_score}
                onChange={(e) => setFormData({ ...formData, min_match_score: e.target.value })}
                className={inputClass}
              />
              <p className="text-xs text-gray-500 mt-1">Only auto-apply if match score is above this threshold</p>
            </div>
            <div>
              <label className={labelClass}>Max Daily Applications</label>
              <input
                type="number"
                min="1"
                max="50"
                value={formData.max_daily}
                onChange={(e) => setFormData({ ...formData, max_daily: e.target.value })}
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Excluded Companies</label>
              <input
                type="text"
                value={formData.excluded_companies}
                onChange={(e) => setFormData({ ...formData, excluded_companies: e.target.value })}
                className={inputClass}
                placeholder="Company A, Company B"
              />
            </div>
            <div>
              <label className={labelClass}>Excluded Industries</label>
              <input
                type="text"
                value={formData.excluded_industries}
                onChange={(e) => setFormData({ ...formData, excluded_industries: e.target.value })}
                className={inputClass}
                placeholder="Gambling, Tobacco"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={updateProfile.isPending}
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            <Save size={16} />
            {updateProfile.isPending ? 'Saving...' : 'Save Settings'}
          </button>
        </div>

        {updateProfile.isSuccess && (
          <div className="p-3 bg-green-50 text-green-700 rounded-lg text-sm">
            Settings saved successfully!
          </div>
        )}
      </form>
    </div>
  );
}
