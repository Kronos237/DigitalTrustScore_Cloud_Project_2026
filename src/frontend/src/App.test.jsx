import { describe, expect, it, vi } from 'vitest';
import { api } from './App.jsx';

describe('API client', () => {
  it('returns JSON responses and sends JSON bodies', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ id: 'real-response' }) });
    const result = await api('/api/analyze', { method: 'POST', body: JSON.stringify({ url: 'https://example.com' }) });
    expect(result).toEqual({ id: 'real-response' });
    expect(fetch).toHaveBeenCalledWith('/api/analyze', expect.objectContaining({ method: 'POST' }));
  });

  it('surfaces backend errors instead of returning placeholder data', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ error: 'Invalid URL' }) });
    await expect(api('/api/analyze')).rejects.toThrow('Invalid URL');
  });
});