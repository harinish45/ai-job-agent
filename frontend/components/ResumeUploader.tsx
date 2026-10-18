'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Upload, FileText, CheckCircle, AlertTriangle, Lightbulb } from 'lucide-react';
import api from '@/lib/api';

export default function ResumeUploader() {
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');

  const { data: analysis } = useQuery({
    queryKey: ['resume-analysis'],
    queryFn: async () => {
      const res = await api.get('/api/resume/analysis');
      return res.data;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post('/api/resume/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: () => {
      setUploadStatus('success');
    },
    onError: () => {
      setUploadStatus('error');
    },
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setUploadStatus('uploading');
      uploadMutation.mutate(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
  });

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Resume Intelligence</h2>
        <p className="text-gray-500 mt-1">Upload your resume for AI analysis</p>
      </div>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input {...getInputProps()} />
        <Upload size={48} className="mx-auto text-gray-400 mb-4" />
        <p className="text-lg font-medium text-gray-700">
          {isDragActive ? 'Drop your resume here' : 'Drag & drop your resume'}
        </p>
        <p className="text-sm text-gray-500 mt-2">PDF or DOCX up to 10MB</p>
      </div>

      {uploadStatus === 'uploading' && (
        <div className="card text-center">
          <div className="animate-pulse">
            <FileText size={32} className="mx-auto text-primary-500 mb-2" />
            <p className="text-gray-600">Analyzing your resume with AI...</p>
          </div>
        </div>
      )}

      {uploadStatus === 'success' && (
        <div className="card bg-green-50 border-green-200">
          <div className="flex items-center gap-3">
            <CheckCircle size={24} className="text-green-600" />
            <div>
              <p className="font-medium text-green-800">Resume uploaded successfully!</p>
              <p className="text-sm text-green-600">AI analysis complete.</p>
            </div>
          </div>
        </div>
      )}

      {analysis && (
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <CheckCircle size={20} className="text-green-600" />
              Strengths
            </h3>
            <ul className="space-y-2">
              {analysis.strengths?.map((strength: string, i: number) => (
                <li key={i} className="flex items-start gap-2 text-gray-700">
                  <span className="text-green-500 mt-1">•</span>
                  {strength}
                </li>
              )) || <p className="text-gray-500">No strengths data available</p>}
            </ul>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <AlertTriangle size={20} className="text-amber-600" />
              Gaps
            </h3>
            <ul className="space-y-2">
              {analysis.gaps?.map((gap: string, i: number) => (
                <li key={i} className="flex items-start gap-2 text-gray-700">
                  <span className="text-amber-500 mt-1">•</span>
                  {gap}
                </li>
              )) || <p className="text-gray-500">No gaps identified</p>}
            </ul>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Lightbulb size={20} className="text-primary-600" />
              Improvement Suggestions
            </h3>
            <div className="space-y-3">
              {analysis.suggestions?.map((suggestion: any, i: number) => (
                <div key={i} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                      suggestion.priority === 'high' ? 'bg-red-100 text-red-700' :
                      suggestion.priority === 'medium' ? 'bg-amber-100 text-amber-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {suggestion.priority}
                    </span>
                    <span className="text-xs text-gray-500 capitalize">{suggestion.category}</span>
                  </div>
                  <p className="text-gray-700 text-sm">{suggestion.suggestion}</p>
                </div>
              )) || <p className="text-gray-500">No suggestions available</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
