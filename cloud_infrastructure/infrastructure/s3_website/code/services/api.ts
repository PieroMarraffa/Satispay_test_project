import { MessageSummary, MessageDetail, CreateMessagePayload } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string | undefined;

if (!API_BASE_URL) {
  throw new Error('Missing VITE_API_BASE_URL. Set it via .env file generated from Terraform.');
}

export const apiService = {
  // GET /messages
  getMessages: async (): Promise<MessageSummary[]> => {
    const response = await fetch(`${API_BASE_URL}/messages`);
    if (!response.ok) {
      throw new Error(`Failed to fetch messages (${response.status})`);
    }
    return await response.json();
  },

  // GET /messages/{id}
  getMessageById: async (id: string): Promise<MessageDetail> => {
    const response = await fetch(`${API_BASE_URL}/messages/${id}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch message details (${response.status})`);
    }
    return await response.json();
  },

  // POST /messages
  createMessage: async (payload: CreateMessagePayload): Promise<{ id: string }> => {
    const response = await fetch(`${API_BASE_URL}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const text = await response.text().catch(() => '');
      throw new Error(`Failed to create message (${response.status}) ${text}`);
    }

    return await response.json();
  }
};