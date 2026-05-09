'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Briefcase, Clock, CheckCircle, XCircle,
  Mail, AlertCircle, Calendar, ChevronDown
} from 'lucide-react';
import api from '@/lib/api';

interface Application {
  id: number;
  job_title: string;
  company: string;
  status: string;
  applied_at: string;
  auto_applied: boolean;
  next_follow_up: string;
  source_platform: string;
}

const statusConfig: Record<string, { label: string; color: string; icon: any }> = {
  new: { label: 'New', color: 'text-gray-600', icon: Briefcase },
  pending_approval: { label: 'Pending Approval', color: 'text-amber-600', icon: Clock },
  applied: { label: 'Applied', color: 'text-blue-600', icon: CheckCircle },
  screening: { label: 'Screening', color: 'text-purple-600', icon: Mail },
  interview: { label: 'Interview', color: 'text-green-600', icon: Calendar },
  offer: { label: 'Offer', color: 'text-emerald-600', icon: CheckCircle },
  rejected: { label: 'Rejected', color: 'text-red-600', icon: XCircle },
  ghosted: { label: 'Ghosted', color: 'text-gray-400', icon: AlertCircle },
};

export default function ApplicationTracker() {
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data, isLoading } = useQuery({
    queryKey: ['applications', statusFilter],
    queryFn: async () => {
      const res = await api.get('/api/applications', {
        params: statusFilter ? { status: statusFilter } : {},
      });
      return res.data;
    },
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      api.put(`/api/applications/${id}/status`, null, { params: { status } }),
  });

  const applications: Application[] = data?.applications || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Application Tracker</h2>
          <p className="text-gray-500 mt-1">Monitor your job applications</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input text-sm py-1.5"
          >
            <option value="">All Statuses</option>
            {Object.entries(statusConfig).map(([key, config]) => (
              <option key={key} value={key}>{config.label}</option>
            ))}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full mx-auto" />
        </div>
      ) : applications.length === 0 ? (
        <div className="card text-center py-12">
          <Briefcase size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">No applications yet</p>
          <p className="text-sm text-gray-400 mt-1">Start by finding and saving jobs</p>
        </div>
      ) : (
        <div className="space-y-3">
          {applications.map((app) => {
            const config = statusConfig[app.status] || statusConfig.new;
            const StatusIcon = config.icon;

            return (
              <div key={app.id} className="card">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900">{app.job_title}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full flex items-center gap-1 bg-gray-100 ${config.color}`}>
                        <StatusIcon size={12} />
                        {config.label}
                      </span>
                      {app.auto_applied && (
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                          Auto
                        </span>
                      )}
                    </div>
                    <p className="text-gray-600 text-sm">{app.company}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      {app.applied_at && (
                        <span>Applied: {new Date(app.applied_at).toLocaleDateString()}</span>
                      )}
                      {app.next_follow_up && (
                        <span className="text-amber-600">
                          Follow up: {new Date(app.next_follow_up).toLocaleDateString()}
                        </span>
                      )}
                      <span className="capitalize">{app.source_platform}</span>
                    </div>
                  </div>

                  <div className="relative group">
                    <button className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1">
                      Update
                      <ChevronDown size={12} />
                    </button>
                    <div className="absolute right-0 mt-1 w-40 bg-white rounded-lg shadow-lg border border-gray-200 hidden group-hover:block z-10">
                      {Object.entries(statusConfig).map(([key, cfg]) => (
                        <button
                          key={key}
                          onClick={() => updateStatus.mutate({ id: app.id, status: key })}
                          className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg"
                        >
                          {cfg.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
