import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
});

export interface HealthStatus {
  status: string;
  face_detection: boolean;
  inswapper: boolean;
  synthetic_identities: number;
  inference: string;
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

export interface EvaluationResponse {
  privacy: {
    identity_similarity: {
      blur: number | null;
      generative: number | null;
    };
  };
  utility: {
    scene_preservation: {
      blur: number | null;
      generative: number | null;
    };
  };
}

export const getHealth = async (): Promise<HealthStatus> => {
  const response = await api.get('/api/health');
  return response.data;
};

export const getSyntheticIdentities = async (): Promise<{ identities: string[] }> => {
  const response = await api.get('/api/synthetic-identities');
  return response.data;
};

export const anonymizeImage = async (
  file: File,
  method: string,
  syntheticIdentity: string
): Promise<AnonymizeResponse> => {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('method', method);
  formData.append('synthetic_identity', syntheticIdentity);

  const response = await api.post('/api/anonymize', formData);
  return response.data;
};

export const evaluateRun = async (runId: string): Promise<EvaluationResponse> => {
  const formData = new FormData();
  formData.append('run_id', runId);

  const response = await api.post('/api/evaluate', formData);
  return response.data;
};

export const getResultUrl = (path: string) => {
  return `${API_URL}${path}`;
};
