import axios from 'axios';

// Mock API for visual verification without a real backend
const api = axios.create();

api.interceptors.request.use((config) => {
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error);
  }
);

// Override methods for mocked responses
const originalGet = api.get;
api.get = async function(url, config) {
  if (url === '/api/jobs') {
    return { data: { jobs: [
      {
        id: 1,
        title: "Senior ML Engineer",
        company: "Tech Corp",
        match_score: 0.85,
        is_ai_role: true,
        location: "Remote",
        work_mode: "remote"
      },
      {
        id: 2,
        title: "Frontend Developer",
        company: "Web Inc",
        match_score: 0.65,
        is_ai_role: false,
        location: "New York",
        work_mode: "hybrid"
      }
    ] } };
  }
  if (url === '/api/applications') {
    return { data: { applications: [] } };
  }
  if (url === '/api/dashboard/stats') {
    return { data: {
      total_applications: 10,
      interviews: 2,
      offers: 0,
      active_jobs: 5,
      response_rate: 0.2
    } };
  }
  if (url === '/api/profile') {
    return { data: { profile: { preferences: {}, auto_apply_rules: {} } } };
  }
  return { data: {} };
}

const originalPost = api.post;
api.post = async function(url, data, config) {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 3000));
  return { data: { success: true } };
}

export default api;
