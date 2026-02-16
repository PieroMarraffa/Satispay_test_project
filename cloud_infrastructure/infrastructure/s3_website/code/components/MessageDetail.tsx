
import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { MessageDetail as IMessageDetail } from '../types';

interface MessageDetailProps {
  id: string;
  onBack: () => void;
}

const MessageDetail: React.FC<MessageDetailProps> = ({ id, onBack }) => {
  const [message, setMessage] = useState<IMessageDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDetail = async () => {
      setIsLoading(true);
      const data = await apiService.getMessageById(id);
      setMessage(data);
      setIsLoading(false);
    };
    fetchDetail();
  }, [id]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <p className="text-slate-500 font-medium">Opening note...</p>
      </div>
    );
  }

  if (!message) return null;

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <button 
        onClick={onBack}
        className="mb-6 flex items-center text-sm font-medium text-slate-500 hover:text-indigo-600 transition-colors group"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1 group-hover:-translate-x-1 transition-transform" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
        Back to messages
      </button>

      <div className="bg-white rounded-3xl shadow-xl shadow-slate-200 border border-slate-100 overflow-hidden">
        <div className="h-2 bg-indigo-600 w-full" />
        <div className="p-8 md:p-12">
          <header className="mb-8 pb-8 border-b border-slate-50">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 leading-tight">
                {message.title}
              </h1>
              <span className="px-4 py-1.5 rounded-full text-xs font-bold tracking-wider uppercase bg-slate-100 text-slate-600">
                REF: {message.id?.slice(0, 12) ?? message.id ?? '—'}
              </span>
            </div>
          </header>

          <article className="prose prose-slate max-w-none">
            <p className="text-lg leading-relaxed text-slate-700 whitespace-pre-wrap">
              {message.text}
            </p>
          </article>

          <footer className="mt-12 pt-8 border-t border-slate-50 flex items-center space-x-4">
             <div className="h-10 w-10 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-500">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
             </div>
             <p className="text-sm text-slate-500">
               Stored in AWS Cloud (DynamoDB). Managed via Secure API Gateway.
             </p>
          </footer>
        </div>
      </div>
    </div>
  );
};

export default MessageDetail;
