
export interface MessageSummary {
  id: string;
  title: string;
}

export interface MessageDetail extends MessageSummary {
  message: string;
}

export interface CreateMessagePayload {
  title: string;
  message: string;
}

export type ViewState = 'list' | 'create' | 'detail';
