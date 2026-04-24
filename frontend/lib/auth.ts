const TOKEN_KEY = "avanon_token";

export const getToken = (): string | null =>
  typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;

export const setToken = (t: string): void => localStorage.setItem(TOKEN_KEY, t);

export const clearToken = (): void => localStorage.removeItem(TOKEN_KEY);
