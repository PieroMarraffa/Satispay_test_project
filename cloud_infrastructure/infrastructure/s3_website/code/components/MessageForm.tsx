
import React, { useState } from 'react';
import { apiService } from '../services/api';

interface MessageFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

const MessageForm: React.FC<MessageFormProps> = ({ onSuccess, onCancel }) => {
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !text) return;

    setIsSubmitting(true);
    await apiService.createMessage({ title, text });
    setIsSubmitting(false);
    onSuccess();
  };

  return (
    <div className="max-w-2xl mx-auto animate-in fade-in zoom-in-95 duration-300">
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-100 p-8 md:p-10">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-900">Create New Note</h2>
          <p className="text-slate-500 mt-1">Fill in the details below to sync with the cloud.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="title" className="block text-sm font-semibold text-slate-700 mb-2">
              Note Title
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Weekly Meeting Notes"
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all outline-none"
              required
            />
          </div>

          <div>
            <label htmlFor="text" className="block text-sm font-semibold text-slate-700 mb-2">
              Message Body
            </label>
            <textarea
              id="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Write your content here..."
              rows={6}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all outline-none resize-none"
              required
            />
          </div>

          <div className="flex flex-col sm:flex-row-reverse sm:space-x-4 sm:space-x-reverse space-y-3 sm:space-y-0 pt-4">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 bg-indigo-600 text-white font-bold py-3.5 rounded-xl hover:bg-indigo-700 active:scale-95 transition-all shadow-lg shadow-indigo-200 flex items-center justify-center disabled:opacity-70"
            >
              {isSubmitting ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Syncing...
                </>
              ) : (
                'Publish Note'
              )}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 bg-slate-50 text-slate-700 font-bold py-3.5 rounded-xl hover:bg-slate-100 transition-all border border-slate-200"
            >
              Discard
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MessageForm;
