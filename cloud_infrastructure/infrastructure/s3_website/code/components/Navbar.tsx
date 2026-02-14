
import React from 'react';
import { ViewState } from '../types';

interface NavbarProps {
  onNavigate: (view: ViewState) => void;
  currentView: ViewState;
}

const Navbar: React.FC<NavbarProps> = ({ onNavigate, currentView }) => {
  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div 
            className="flex items-center cursor-pointer group"
            onClick={() => onNavigate('list')}
          >
            <div className="bg-indigo-600 p-2 rounded-lg mr-3 shadow-md group-hover:bg-indigo-700 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <span className="text-xl font-bold text-slate-900 tracking-tight">Test Marraffa for <span className="text-indigo-600">Satispay</span></span>
          </div>
          
          <div className="flex space-x-4">
            <button
              onClick={() => onNavigate('list')}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-all ${
                currentView === 'list' || currentView === 'detail' 
                ? 'text-indigo-600 bg-indigo-50' 
                : 'text-slate-600 hover:text-indigo-600 hover:bg-slate-50'
              }`}
            >
              My Messages
            </button>
            <button
              onClick={() => onNavigate('create')}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all shadow-sm ${
                currentView === 'create'
                ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                : 'bg-white text-slate-700 border border-slate-200 hover:border-indigo-300 hover:text-indigo-600'
              }`}
            >
              + New Note
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
