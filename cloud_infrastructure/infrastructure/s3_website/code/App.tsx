
import React, { useState } from 'react';
import Navbar from './components/Navbar';
import MessageList from './components/MessageList';
import MessageDetail from './components/MessageDetail';
import MessageForm from './components/MessageForm';
import { ViewState } from './types';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewState>('list');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleNavigate = (view: ViewState) => {
    setCurrentView(view);
    if (view !== 'detail') setSelectedId(null);
  };

  const handleSelectMessage = (id: string) => {
    setSelectedId(id);
    setCurrentView('detail');
  };

  const handleCreateSuccess = () => {
    setRefreshKey(prev => prev + 1);
    setCurrentView('list');
  };

  return (
    <div className="min-h-screen pb-20">
      <Navbar currentView={currentView} onNavigate={handleNavigate} />
      
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 mt-12">
        {currentView === 'list' && (
          <div className="space-y-8">
            <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
              <div>
                <h1 className="text-3xl font-extrabold text-slate-900">Welcome Satispay!</h1>
                <p className="text-slate-500 mt-1">View and manage your messages across the cloud.</p>
              </div>
              <div className="flex space-x-3">
                 <button 
                  onClick={() => setRefreshKey(prev => prev + 1)}
                  className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-white rounded-lg transition-all"
                  title="Refresh data"
                 >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                 </button>
              </div>
            </header>
            
            <MessageList 
              onSelectMessage={handleSelectMessage} 
              onRefreshTrigger={refreshKey}
            />
          </div>
        )}

        {currentView === 'detail' && selectedId && (
          <MessageDetail 
            id={selectedId} 
            onBack={() => handleNavigate('list')} 
          />
        )}

        {currentView === 'create' && (
          <MessageForm 
            onSuccess={handleCreateSuccess} 
            onCancel={() => handleNavigate('list')} 
          />
        )}
      </main>

      {/* Floating Action Button (Mobile Only) */}
      {currentView === 'list' && (
        <button
          onClick={() => handleNavigate('create')}
          className="fixed bottom-8 right-8 md:hidden h-16 w-16 bg-indigo-600 text-white rounded-full shadow-2xl flex items-center justify-center hover:scale-110 active:scale-95 transition-all z-50"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      )}
    </div>
  );
};

export default App;
