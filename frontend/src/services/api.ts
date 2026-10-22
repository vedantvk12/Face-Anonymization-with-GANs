import axios from 'axios';

const rawApiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').trim();
export const API_URL = rawApiUrl.replace(/\/+$/, '');

const api = axios.create({
  baseURL: API_URL,
});

export interface HealthStatus {
  status: 'online' | 'warming' | 'offline' | 'error' | string;
  face_detection: boolean;
  inswapper: boolean;
  synthetic_identities: number;
  inference: string;
  message?: string;
}

export const DEFAULT_HEALTH_STATUS: HealthStatus = {
  status: 'warming',
  face_detection: false,
  inswapper: false,
  synthetic_identities: 0,
  inference: 'GPU (DirectML)',
  message: 'Initializing AI models...'
};

export interface SyntheticIdentity {
  id: string;
  name: string;
  style: 'realistic' | 'cartoon' | 'anime' | string;
  description: string;
  thumbnail: string;
}

export interface AnonymizeResponse {
  success: boolean;
  faces_detected: number;
  method: string;
  synthetic_identity: string | null;
  processing_time: number;
  result_url: string;
  run_id: string;
  original_url: string;
}

export interface VideoJobStatus {
  id: string;
  filename: string;
  method: string;
  identity: string;
  resolution: string;
  status: 'queued' | 'processing' | 'completed' | 'cancelled' | 'failed';
  current_frame: number;
  total_frames: number;
  progress_percent: number;
  fps: number;
  elapsed_time: number;
  eta_seconds: number | null;
  result_url: string | null;
  original_url: string | null;
  error_message: string | null;
  created_at: number;
}

export interface EvaluationResponse {
  privacy: {
    identity_similarity: {
      blur: number | null;
      generative: number | null;
    };
    interpretation?: string;
  };
  utility: {
    scene_preservation: {
      blur: number | null;
      generative: number | null;
    };
    non_face_difference: {
      blur: number | null;
      generative: number | null;
    };
    interpretation?: string;
  };
}

export interface VideoEvaluationResponse {
  sampling_method: string;
  average_identity_similarity: number | null;
  average_scene_preservation: number | null;
  samples: Array<{
    frame: number;
    timestamp_seconds: number;
    identity_similarity: number | null;
    scene_preservation: number | null;
  }>;
  interpretation: string;
  error?: string;
}

export const getHealth = async (): Promise<HealthStatus> => {
  const response = await api.get('/api/health');
  return response.data;
};

export const getIdentities = async (style?: string): Promise<{ identities: SyntheticIdentity[] }> => {
  const url = style && style !== 'all' ? `/api/identities?style=${style}` : '/api/identities';
  const response = await api.get(url);
  return response.data;
};

export const getSyntheticIdentities = async (): Promise<{ identities: string[] }> => {
  const response = await api.get('/api/synthetic-identities');
  return response.data;
};

export const anonymizeImage = async (
  file: File,
  method: string,
  syntheticIdentity: string,
  uniqueFaces: boolean = true
): Promise<AnonymizeResponse> => {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('method', method);
  formData.append('synthetic_identity', syntheticIdentity);
  formData.append('unique_faces', uniqueFaces ? 'true' : 'false');

  const response = await api.post('/api/anonymize', formData);
  return response.data;
};

export const anonymizeVideo = async (
  file: File,
  method: string,
  syntheticIdentity: string,
  resolution: string = 'original'
): Promise<{ job_id: string; status: string; message: string }> => {
  const formData = new FormData();
  formData.append('video', file);
  formData.append('method', method);
  formData.append('synthetic_identity', syntheticIdentity);
  formData.append('resolution', resolution);

  const response = await api.post('/api/video/anonymize', formData);
  return response.data;
};

export const getVideoStatus = async (jobId: string): Promise<VideoJobStatus> => {
  const response = await api.get(`/api/video/status/${jobId}`);
  return response.data;
};

export const cancelVideoJob = async (jobId: string): Promise<{ message: string }> => {
  const response = await api.post(`/api/video/cancel/${jobId}`);
  return response.data;
};

export const evaluateRun = async (runId: string): Promise<EvaluationResponse> => {
  const formData = new FormData();
  formData.append('run_id', runId);

  const response = await api.post('/api/evaluate', formData);
  return response.data;
};

export const evaluateVideoJob = async (jobId: string): Promise<VideoEvaluationResponse> => {
  const formData = new FormData();
  formData.append('job_id', jobId);

  const response = await api.post('/api/video/evaluate', formData);
  return response.data;
};

export const getResultUrl = (path: string) => {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_URL}${cleanPath}`;
};
