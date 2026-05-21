'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Search, MapPin, DollarSign, Star, ExternalLink, Bot, Filter } from 'lucide-react';
import api from '@/lib/api';

interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  work_mode: string;
  salary_min: number;
  salary_max: number;
  source_platform: string;
  apply_url: string;
  is_ai_role: boolean;
  ai_role_category: string;
  posted_at: string;
  match_score: number;
  is_strong_match: boolean;
}

export default function JobList() {
  const [filters, setFilters] = useState({
    minScore: 0.7,
    aiOnly: false,
    remoteOnly: true,
  });

  const { data: jobsData, isLoading } = useQuery({
    queryKey: ['jobs', filters],
    queryFn: async () => {
      const res = await api.get('/api/jobs', {
        params: {
          min_score: filters.minScore,
          is_ai_role: filters.aiOnly || undefined,
          limit: 50,
        },
      });
      return res.data;
    },
  });

  const matchMutation = useMutation({
    mutationFn: (jobId: number) => api.post(`/api/jobs/${jobId}/match`),
  });

  const applyMutation = useMutation({
    mutationFn: (jobId: number) => api.post(`/api/jobs/${jobId}/apply`, null, { params: { auto_apply: false } }),
  });

  const jobs: Job[] = jobsData?.jobs || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Job Matches</h2>
          <p className="text-gray-500 mt-1">AI-curated opportunities</p>
        </div>
        <button
          onClick={() => api.post('/api/search/trigger')}
          className="btn-primary flex items-center gap-2"
        >
          <Search size={16} />
          Refresh Jobs
        </button>
      </div>

      <div className="flex flex-wrap gap-3">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={filters.aiOnly}
            onChange={(e) => setFilters({ ...filters, aiOnly: e.target.checked })}
            className="rounded border-gray-300"
          />
          AI roles only
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={filters.remoteOnly}
            onChange={(e) => setFilters({ ...filters, remoteOnly: e.target.checked })}
            className="rounded border-gray-300"
          />
          Remote only
        </label>
        <div className="flex items-center gap-2 text-sm">
          <Filter size={14} />
          <span>Min match:</span>
          <select
            value={filters.minScore}
            onChange={(e) => setFilters({ ...filters, minScore: parseFloat(e.target.value) })}
            className="border rounded px-2 py-1 text-sm"
          >
            <option value={0.5}>50%</option>
            <option value={0.6}>60%</option>
            <option value={0.7}>70%</option>
            <option value={0.8}>80%</option>
            <option value={0.9}>90%</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-gray-500 mt-4">Loading jobs...</p>
        </div>
      ) : jobs.length === 0 ? (
        <div className="card text-center py-12">
          <Search size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">No jobs found matching your criteria</p>
          <p className="text-sm text-gray-400 mt-1">Try adjusting your filters or upload a resume first</p>
        </div>
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => (
            <div key={job.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                    {job.is_ai_role && (
                      <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <Bot size={12} />
                        AI Role
                      </span>
                    )}
                    {job.is_strong_match && (
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                        <Star size={12} />
                        Strong Match
                      </span>
                    )}
                  </div>
                  <p className="text-gray-600 font-medium">{job.company}</p>

                  <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <MapPin size={14} />
                      {job.location || 'Remote'}
                    </span>
                    {job.salary_min && (
                      <span className="flex items-center gap-1">
                        <DollarSign size={14} />
                        ${job.salary_min.toLocaleString()} - ${job.salary_max?.toLocaleString()}
                      </span>
                    )}
                    <span className="capitalize">{job.work_mode}</span>
                    <span className="text-gray-400">via {job.source_platform}</span>
                  </div>

                  {job.match_score && (
                    <div className="mt-3 flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            job.match_score >= 0.8 ? 'bg-green-500' :
                            job.match_score >= 0.6 ? 'bg-amber-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${job.match_score * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-700">
                        {Math.round(job.match_score * 100)}% match
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex flex-col gap-2 ml-4">
                  <button
                    onClick={() => matchMutation.mutate(job.id)}
                    disabled={matchMutation.isPending && matchMutation.variables === job.id}
                    className="btn-secondary text-xs px-3 py-1.5"
                  >
                    {matchMutation.isPending && matchMutation.variables === job.id ? 'Analyzing...' : 'Analyze Match'}
                  </button>
                  <button
                    onClick={() => applyMutation.mutate(job.id)}
                    disabled={applyMutation.isPending && applyMutation.variables === job.id}
                    className="btn-primary text-xs px-3 py-1.5"
                  >
                    {applyMutation.isPending && applyMutation.variables === job.id ? 'Saving...' : 'Save Job'}
                  </button>
                  <a
                    href={job.apply_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary text-xs px-3 py-1.5 flex items-center justify-center gap-1"
                  >
                    <ExternalLink size={12} />
                    Apply
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
