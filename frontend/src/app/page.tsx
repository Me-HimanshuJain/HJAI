"use client";
import React, { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import ChatInterface from '@/components/ChatInterface';
import ContextPane from '@/components/ContextPane';

export default function Home() {
  const [userId] = useState('user-123'); // Hardcoded for demo purposes
  
  return (
    <div className="bg-background text-on-surface overflow-hidden h-screen flex">
      {/* SideNavBar */}
      <Sidebar />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-background">
        {/* TopAppBar */}
        <header className="flex justify-between items-center w-full px-margin h-16 border-b border-outline-variant bg-background z-10">
          <div className="flex items-center gap-md">
            <span className="font-code-md text-code-md font-bold text-primary tracking-tighter">Cockpit / Chat Engine</span>
            <div className="hidden md:flex items-center gap-xs px-2 py-0.5 rounded border border-outline-variant bg-surface-container text-[10px] font-code-sm text-on-surface-variant uppercase tracking-widest">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
              Live Session
            </div>
          </div>
          <div className="flex items-center gap-md">
            <div className="flex items-center gap-sm">
              <button className="p-2 rounded-lg text-on-surface-variant hover:bg-surface-container-highest transition-colors active:opacity-80">
                <span className="material-symbols-outlined">history</span>
              </button>
              <button className="p-2 rounded-lg text-on-surface-variant hover:bg-surface-container-highest transition-colors active:opacity-80">
                <span className="material-symbols-outlined">settings</span>
              </button>
            </div>
            <div className="w-8 h-8 rounded-full border border-outline-variant overflow-hidden bg-surface-container-high flex items-center justify-center text-xs text-primary font-bold">
              U
            </div>
          </div>
        </header>

        {/* ChatInterface covers the middle */}
        <ChatInterface userId={userId} />
        
        {/* Atmospheric Side Decorations */}
        <div className="absolute top-1/2 -right-64 w-96 h-96 bg-primary/5 blur-[120px] rounded-full pointer-events-none"></div>
        <div className="absolute bottom-1/4 -left-64 w-80 h-80 bg-primary/5 blur-[100px] rounded-full pointer-events-none"></div>
      </main>

      {/* Side Overlay Panels */}
      <ContextPane userId={userId} />
    </div>
  );
}
