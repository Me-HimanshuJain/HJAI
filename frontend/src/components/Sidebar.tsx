import React from 'react';

export default function Sidebar() {
  return (
    <aside className="hidden lg:flex flex-col h-full w-64 bg-surface border-r border-outline-variant py-md transition-all duration-200">
      <div className="px-md mb-xl">
        <div className="flex items-center gap-sm">
          <div className="w-8 h-8 rounded-lg bg-primary-container flex items-center justify-center">
            <span className="material-symbols-outlined text-white text-md">terminal</span>
          </div>
          <div className="flex flex-col">
            <span className="font-code-md text-code-md text-primary font-bold">HJAI Terminal</span>
            <span className="font-body-sm text-body-sm text-on-surface-variant opacity-60">v1.0.4-alpha</span>
          </div>
        </div>
      </div>
      <nav className="flex-1 px-sm space-y-xs">
        <a className="flex items-center gap-md px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-high transition-colors group cursor-pointer">
          <span className="material-symbols-outlined">grid_view</span>
          <span className="font-body-sm text-body-sm">Workspace</span>
        </a>
        {/* Active Tab: Cockpit maps to Chat Engine / Agents */}
        <a className="flex items-center gap-md px-md py-sm rounded-lg text-primary border-r-2 border-primary bg-primary-container/10 transition-colors group cursor-pointer">
          <span className="material-symbols-outlined">smart_toy</span>
          <span className="font-body-sm text-body-sm font-medium">Agents Engine</span>
        </a>
        <a className="flex items-center gap-md px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-high transition-colors group cursor-pointer">
          <span className="material-symbols-outlined">description</span>
          <span className="font-body-sm text-body-sm">Logs</span>
        </a>
        <a className="flex items-center gap-md px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-high transition-colors group cursor-pointer">
          <span className="material-symbols-outlined">terminal</span>
          <span className="font-body-sm text-body-sm">Terminal</span>
        </a>
      </nav>
      <div className="px-sm pt-md border-t border-outline-variant/30 space-y-xs">
        <a className="flex items-center gap-md px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-high transition-colors group cursor-pointer">
          <span className="material-symbols-outlined">help</span>
          <span className="font-body-sm text-body-sm">Help</span>
        </a>
        <a className="flex items-center gap-md px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-high transition-colors group cursor-pointer">
          <span className="material-symbols-outlined">logout</span>
          <span className="font-body-sm text-body-sm">Logout</span>
        </a>
      </div>
    </aside>
  );
}
