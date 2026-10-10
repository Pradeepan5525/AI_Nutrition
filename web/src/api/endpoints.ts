import { apiClient } from './client';

export interface UserProfile {
  age?: number;
  sex?: string;
  height_cm?: number;
  weight_kg?: number;
  activity_level?: string;
  goal?: string;
  is_asian?: boolean;
  conditions?: string[];
  allergies?: string[];
  dietary_restrictions?: string[];
  preferred_cuisine?: string;
  onboarding_completed?: boolean;
  updated_at?: string;
}

export interface UserAccount {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: string;
  profile?: UserProfile;
  saved_profile?: UserProfile;
  created_at: string;
  last_login?: string;
}

export const api = {
  auth: {
    login: (credentials: { username_or_email?: string; email?: string; password: string; remember_me?: boolean }) =>
      apiClient<{ access_token: string; token_type: string; user: UserAccount }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      }),

    register: (payload: { email: string; password: string; full_name?: string; accept_disclaimer: boolean }) =>
      apiClient<{ access_token: string; token_type: string; user: UserAccount }>('/auth/register', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    refresh: () =>
      apiClient<{ access_token: string; token_type: string; user: UserAccount }>('/auth/refresh', {
        method: 'POST',
      }),

    logout: () =>
      apiClient<{ message: string }>('/auth/logout', {
        method: 'POST',
      }),

    getMe: () => apiClient<UserAccount>('/users/me'),
  },

  users: {
    updateProfile: (profile: UserProfile) =>
      apiClient<UserAccount>('/users/me/profile', {
        method: 'PUT',
        body: JSON.stringify({ profile }),
      }),

    changePassword: (data: { current_password: string; new_password: string }) =>
      apiClient<{ message: string }>('/users/me/password', {
        method: 'PUT',
        body: JSON.stringify(data),
      }),

    exportData: () => apiClient<any>('/users/me/export'),

    deleteAccount: () =>
      apiClient<{ message: string }>('/users/me', {
        method: 'DELETE',
      }),
  },

  assess: {
    run: (payload: any) =>
      apiClient<any>('/assess', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    listHistory: () => apiClient<any[]>('/users/me/assessments'),

    save: (payload: any) =>
      apiClient<any>('/users/me/assessments', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    delete: (id: number) =>
      apiClient<{ message: string }>(`/users/me/assessments/${id}`, {
        method: 'DELETE',
      }),
  },

  risk: {
    run: (payload: any) =>
      apiClient<any>('/risk', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    listHistory: () => apiClient<any[]>('/users/me/risk-results'),

    save: (payload: any) =>
      apiClient<any>('/users/me/risk-results', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    delete: (id: number) =>
      apiClient<{ message: string }>(`/users/me/risk-results/${id}`, {
        method: 'DELETE',
      }),
  },

  plan: {
    run: (payload: any) =>
      apiClient<any>('/plan', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    listHistory: () => apiClient<any[]>('/users/me/meal-plans'),

    save: (payload: any) =>
      apiClient<any>('/users/me/meal-plans', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    delete: (id: number) =>
      apiClient<{ message: string }>(`/users/me/meal-plans/${id}`, {
        method: 'DELETE',
      }),
  },

  foods: {
    search: (params: {
      q?: string;
      category?: string;
      food_type?: string;
      min_health_score?: number;
      exclude_allergens?: string[];
      strict_allergens?: boolean;
      page?: number;
      page_size?: number;
    }) => {
      const qp = new URLSearchParams();
      if (params.q) qp.set('q', params.q);
      if (params.category) qp.set('category', params.category);
      if (params.food_type) qp.set('food_type', params.food_type);
      if (params.min_health_score !== undefined) qp.set('min_health_score', String(params.min_health_score));
      if (params.exclude_allergens && params.exclude_allergens.length > 0) {
        params.exclude_allergens.forEach((a) => qp.append('exclude_allergens', a));
      }
      if (params.strict_allergens !== undefined) qp.set('strict_allergens', String(params.strict_allergens));
      if (params.page) qp.set('page', String(params.page));
      if (params.page_size) qp.set('page_size', String(params.page_size));

      return apiClient<any>(`/foods/search?${qp.toString()}`);
    },

    getById: (id: string) => apiClient<any>(`/foods/${id}`),

    getSwaps: (id: string, maxSwaps = 5, strictAllergens = true) =>
      apiClient<any>(`/foods/${id}/swaps?max_swaps=${maxSwaps}&strict_allergens=${strictAllergens}`),
  },

  reports: {
    downloadPdf: (payload: any) =>
      apiClient<Blob>('/report', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },

  weights: {
    list: () => apiClient<any[]>('/users/me/weight-logs'),
    add: (payload: { weight_kg: number; bmi?: number; note?: string }) =>
      apiClient<any>('/users/me/weight-logs', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    delete: (id: number) =>
      apiClient<{ message: string }>(`/users/me/weight-logs/${id}`, {
        method: 'DELETE',
      }),
  },

  goals: {
    list: () => apiClient<any[]>('/users/me/goals-alerts'),
    update: (payload: any) =>
      apiClient<any>('/users/me/goals-alerts', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },

  notifications: {
    list: () => apiClient<any[]>('/users/me/notifications'),
    markRead: (id: number) =>
      apiClient<{ message: string }>(`/users/me/notifications/${id}/read`, {
        method: 'PUT',
      }),
  },
};
