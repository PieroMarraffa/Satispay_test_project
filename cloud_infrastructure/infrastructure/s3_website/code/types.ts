
export interface MessageSummary {
  id: string;
  title: string;
}

export interface MessageDetail extends MessageSummary {
  text: string;
}

export interface CreateMessagePayload {
  title: string;
  text: string;
}

export type ViewState = 'list' | 'create' | 'detail';
