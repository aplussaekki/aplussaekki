// API 클라이언트 설정

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface RequestOptions extends RequestInit {
  params?: Record<string, string>;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private buildUrl(endpoint: string, params?: Record<string, string>): string {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }
    return url.toString();
  }

  private async handleError(response: Response): Promise<never> {
    let errorMessage = `API Error: ${response.status}`;
    try {
      const errorBody = await response.json();
      console.error('API Error Response:', errorBody);
      if (errorBody.detail) {
        // FastAPI validation error format
        if (Array.isArray(errorBody.detail)) {
          errorMessage = errorBody.detail.map((e: { msg: string; loc: string[] }) => 
            `${e.loc.join('.')}: ${e.msg}`
          ).join(', ');
        } else if (typeof errorBody.detail === 'string') {
          errorMessage = errorBody.detail;
        } else if (errorBody.detail.message) {
          errorMessage = errorBody.detail.message;
        }
      }
    } catch {
      // JSON 파싱 실패 시 기본 에러 메시지 사용
    }
    throw new Error(errorMessage);
  }

  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const { params, ...fetchOptions } = options || {};
    const response = await fetch(this.buildUrl(endpoint, params), {
      ...fetchOptions,
      method: 'GET',
    });
    if (!response.ok) {
      await this.handleError(response);
    }
    return response.json();
  }

  async post<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    const { params, ...fetchOptions } = options || {};
    console.log('POST Request:', endpoint, body); // 디버깅용
    const response = await fetch(this.buildUrl(endpoint, params), {
      ...fetchOptions,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers,
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      await this.handleError(response);
    }
    return response.json();
  }

  async postForm<T>(endpoint: string, formData: FormData): Promise<T> {
    const response = await fetch(this.buildUrl(endpoint), {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      await this.handleError(response);
    }
    return response.json();
  }
}

export const apiClient = new ApiClient(API_BASE_URL);

