import { MessageSummary, MessageDetail, CreateMessagePayload } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string | undefined;

if (!API_BASE_URL) {
  throw new Error('Missing VITE_API_BASE_URL. Set it via .env file generated from Terraform.');
}

export const apiService = {
  // GET /messages — backend returns { items: MessageSummary[], next_token?: string }
  getMessages: async (): Promise<MessageSummary[]> => {
    const response = await fetch(`${API_BASE_URL}/messages`);
    if (!response.ok) {
      throw new Error(`Failed to fetch messages (${response.status})`);
    }
    const data = await response.json();
    const rawItems: unknown[] = Array.isArray(data) ? data : (data?.items ?? []);
    if (!Array.isArray(rawItems)) return [];
    return rawItems.map((it: Record<string, unknown>) => ({
      id: String(it.id ?? it.message_id ?? ''),
      title: String(it.title ?? it.author ?? it.text ?? it.id ?? it.message_id ?? ''),
    })) as MessageSummary[];
  },

  // GET /messages/{id} — backend returns raw DynamoDB item (message_id, text, author, …); we normalize to MessageDetail
  getMessageById: async (id: string): Promise<MessageDetail> => {
    const response = await fetch(`${API_BASE_URL}/messages/${id}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch message details (${response.status})`);
    }
    const it = (await response.json()) as Record<string, unknown>;
    return {
      id: String(it.id ?? it.message_id ?? ''),
      title: String(it.title ?? it.author ?? it.text ?? it.id ?? it.message_id ?? ''),
      message: String(it.message ?? it.text ?? ''),
    } as MessageDetail;
  },

  // POST /messages — backend expects { text: string, author?: string }, we send title as author and message as text
  createMessage: async (payload: CreateMessagePayload): Promise<{ id: string }> => {
    const body = {
      text: payload.message,
      ...(payload.title?.trim() && { author: payload.title.trim() }),
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