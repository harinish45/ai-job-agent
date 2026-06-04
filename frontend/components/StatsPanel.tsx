'use client';

import { TrendingUp, Briefcase, Mail, Clock, CheckCircle, XCircle } from 'lucide-react';

interface Stats {
  total_applied: number;
  interviews: number;
  offers: number;
  rejections: number;
  ghosted: number;
  interview_rate: number;
  offer_rate: number;
  platform_breakdown: { platform: string; count: number }[];
}

export default function StatsPanel({ stats }: { stats?: Stats }) {
  const statCards = [
    { label: 'Total Applied', value: stats?.total_applied || 0, icon: Briefcase, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Interviews', value: stats?.interviews || 0, icon: Mail, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Offers', value: stats?.offers || 0, icon: CheckCircle, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Rejections', value: stats?.rejections || 0, icon: XCircle, color: 'text-red-600', bg: 'bg-red-50' },
    { label: 'Ghosted', value: stats?.ghosted || 0, icon: Clock, color: 'text-gray-600', bg: 'bg-gray-50' },
    { label: 'Interview Rate', value: `${stats?.interview_rate || 0}%`, icon: TrendingUp, color: 'text-purple-600', bg: 'bg-purple-50' },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <p className="text-gray-500 mt-1">Track your job search performance</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.label} className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{card.label}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">{card.value}</p>
                </div>
                <div className={`p-3 rounded-lg ${card.bg}`}>
                  <Icon size={24} className={card.color} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {stats?.platform_breakdown && stats.platform_breakdown.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Platform Breakdown</h3>
          <div className="space-y-3">
            {stats.platform_breakdown.map((platform) => (
              <div key={platform.platform} className="flex items-center justify-between">
                <span className="text-sm text-gray-600 capitalize">{platform.platform}</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full"
                      style={{
                        width: `${(platform.count / (stats.total_applied || 1)) * 100}%`,
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-900 w-8 text-right">
                    {platform.count}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
