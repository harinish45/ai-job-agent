'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Briefcase, TrendingUp, Mail, Clock,
  CheckCircle, XCircle, AlertCircle, Upload,
  Settings, Search, FileText, BarChart3
} from 'lucide-react';
import api from '@/lib/api';
import ResumeUploader from '@/components/ResumeUploader';
import JobList from '@/components/JobList';
import ApplicationTracker from '@/components/ApplicationTracker';
import StatsPanel from '@/components/StatsPanel';
import ProfileSettings from '@/components/ProfileSettings';

type Tab = 'dashboard' | 'jobs' | 'applications' | 'resume' | 'settings';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const res = await api.get('/api/dashboard/stats');
      return res.data;
    },
  });

  const tabs = [
    { id: 'dashboard' as Tab, label: 'Dashboard', icon: BarChart3 },
    { id: 'jobs' as Tab, label: 'Jobs', icon: Search },
    { id: 'applications' as Tab, label: 'Applications', icon: Briefcase },
    { id: 'resume' as Tab, label: 'Resume', icon: FileText },
    { id: 'settings' as Tab, label: 'Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <aside className="fixed left-0 top-0 h-full w-64 bg-white border-r border-gray-200 z-10">
        <div className="p-6">
          <h1 className="text-xl font-bold text-gray-900">AI Job Agent</h1>
          <p className="text-xs text-gray-500 mt-1">v1.0.0</p>
        </div>

        <nav className="px-4 space-y-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon size={18} />
                {tab.label}
              </button>
            );
          })}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
          <button
            onClick={() => {
              localStorage.removeItem('token');
              window.location.href = '/login';
            }}
            className="w-full text-left px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
          >
            Sign Out
          </button>
        </div>
      </aside>

      <main className="ml-64 p-8">
        {activeTab === 'dashboard' && <StatsPanel stats={stats} />}
        {activeTab === 'jobs' && <JobList />}
        {activeTab === 'applications' && <ApplicationTracker />}
        {activeTab === 'resume' && <ResumeUploader />}
        {activeTab === 'settings' && <ProfileSettings />}
      </main>
    </div>
  );
}
