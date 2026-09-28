export interface ApiBaseResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: {
    code: string;
    message: string;
  };
}

export interface AuthLoginResponse {
  token: string;
}

export interface ChatRequest {
  message: string;
  latitude: number;
  longitude: number;
  language?: string;
  conversation_id?: string;
}

export interface ChatResponse {
  answer: string;
  intent: string;
  sources: string[];
  mode: string;
  conversation_id: string;
}
