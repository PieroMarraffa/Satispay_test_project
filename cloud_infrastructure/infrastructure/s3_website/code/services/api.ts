import { MessageSummary, MessageDetail, CreateMessagePayload } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string | undefined;

if (!API_BASE_URL) {
  throw new Error('Missing VITE_API_BASE_URL. Set it via .env file generated from Terraform.');
}

export const apiService = {
  // GET /messages — backend returns { items: [...], next_token?: string }; each item has message_id, title, message
  getMessages: async (): Promise<MessageSummary[]> => {
    const response = await fetch(`${API_BASE_URL}/messages`);
    if (!response.ok) {
      throw new Error(`Failed to fetch messages (${response.status})`);
    }
    const data = await response.json();
    const rawItems: unknown[] = Array.isArray(data) ? data : (data?.items ?? []);
    if (!Array.isArray(rawItems)) return [];
    return rawItems.map((it: Record<string, unknown>) => ({
      id: String(it.message_id ?? it.id ?? ''),
      title: String(it.title ?? ''),
    })) as MessageSummary[];
  },

  // GET /messages/{id} — backend returns DynamoDB item: message_id, title, message
  getMessageById: async (id: string): Promise<MessageDetail> => {
    const response = await fetch(`${API_BASE_URL}/messages/${id}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch message details (${response.status})`);
    }
    const it = (await response.json()) as Record<string, unknown>;
    return {
      id: String(it.message_id ?? it.id ?? ''),
      title: String(it.title ?? ''),
      message: String(it.message ?? ''),
    } as MessageDetail;
  },

  // POST /messages — backend expects { title: string, message: string }
  createMessage: async (payload: CreateMessagePayload): Promise<{ id: string }> => {
    const body = {
      title: payload.title?.trim() ?? '',
      message: payload.message?.trim() ?? '',
    };
    const response = await fetch(`${API_BASE_URL}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const text = await response.text().catch(() => '');
      throw new Error(`Failed to create message (${response.status}) ${text}`);
    }

    const data = (await response.json()) as { message_id?: string; id?: string };
    return { id: data.message_id ?? data.id ?? '' };
  }
};