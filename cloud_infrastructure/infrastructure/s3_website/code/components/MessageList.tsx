
import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { MessageSummary } from '../types';

interface MessageListProps {
  onSelectMessage: (id: string) => void;
  onRefreshTrigger?: number;
}

const MessageList: React.FC<MessageListProps> = ({ onSelectMessage, onRefreshTrigger }) => {
  const [messages, setMessages] = useState<MessageSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchMessages = async () => {
      setIsLoading(true);
      const data = await apiService.getMessages();
      setMessages(data);
      setIsLoading(false);
    };
    fetchMessages();
  }, [onRefreshTrigger]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <p className="text-slate-500 font-medium animate-pulse">Fetching your notes...</p>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-slate-300">
        <div className="mx-auto h-24 w-24 text-slate-300 mb-4">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-slate-900">No messages found</h3>
        <p className="text-slate-500 mt-1">Start by creating your first note.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
        <h2 className="text-lg font-bold text-slate-800">Inbox</h2>
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-700">
          {messages.length} notes
        </span>
      </div>
      <ul className="divide-y divide-slate-100">
        {messages.map((msg) => (
          <li 
            key={msg.id}
            onClick={() => onSelectMessage(msg.id)}
            className="group hover:bg-slate-50 transition-all cursor-pointer p-6"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="h-10 w-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 group-hover:bg-indigo-100 group-hover:text-indigo-600 transition-colors">
                   <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-md font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">{msg.title}</h3>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">ID: {msg.id.slice(0, 8)}...</p>
                </div>
              </div>
              <div className="text-slate-300 group-hover:text-indigo-400 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default MessageList;
