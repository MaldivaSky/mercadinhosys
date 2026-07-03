import React from 'react';
import { X } from 'lucide-react';

interface DetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export default function DetailsModal({ isOpen, onClose, title, children }: DetailsModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm animate-in fade-in duration-200"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-slate-800 border border-slate-700/60 shadow-2xl rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col animate-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between p-6 border-b border-slate-700/60 bg-slate-800/80 rounded-t-2xl">
          <h2 className="text-xl font-bold text-white">{title}</h2>
          <button 
            onClick={onClose}
            className="p-2 text-slate-400 hover:bg-slate-700 hover:text-white rounded-full transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto custom-scrollbar">
          {children}
        </div>
      </div>
    </div>
  );
}
