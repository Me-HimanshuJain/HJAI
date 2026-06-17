import React from 'react';

export default function ContextPane({ userId }: { userId?: string }) {
  return (
    <div className="hidden xl:flex flex-col w-80 border-l border-outline-variant bg-surface py-md">
      <div className="px-md mb-lg">
        <h3 className="font-label-md text-label-md text-on-surface-variant uppercase tracking-widest mb-md">Context Assets</h3>
        <div className="space-y-sm">
          {/* Asset Card 1 */}
          <div className="p-md rounded-lg border border-outline-variant bg-surface-container-low group hover:border-primary/30 transition-colors cursor-pointer">
            <div className="flex justify-between items-start mb-sm">
              <span className="material-symbols-outlined text-primary">data_object</span>
              <span className="text-[10px] font-code-sm text-green-400">SYNCED</span>
            </div>
            <div className="font-code-sm text-code-sm text-on-surface mb-1">deployment_v12.yaml</div>
            <div className="text-[10px] font-body-sm text-on-surface-variant">Last modified 12m ago</div>
          </div>
          
          {/* Asset Card 2 */}
          <div className="p-md rounded-lg border border-outline-variant bg-surface-container-low group hover:border-primary/30 transition-colors cursor-pointer">
            <div className="flex justify-between items-start mb-sm">
              <span className="material-symbols-outlined text-primary">shield</span>
              <span className="text-[10px] font-code-sm text-on-surface-variant">IDLE</span>
            </div>
            <div className="font-code-sm text-code-sm text-on-surface mb-1">security_policy.pdf</div>
            <div className="text-[10px] font-body-sm text-on-surface-variant">Read-only buffer</div>
          </div>
        </div>
      </div>
      
      <div className="px-md mt-auto">
        <div className="p-md rounded-xl bg-surface-container-high border border-primary/10 system-glow">
          <div className="flex items-center gap-sm mb-md">
            <div className="w-2 h-2 rounded-full bg-primary animate-ping"></div>
            <span className="font-label-md text-label-md text-primary uppercase">Active Agent</span>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed mb-md">
            "Architect" is analyzing the request. Estimating 1.2s to response completion.
          </p>
          <div className="w-full bg-outline-variant/20 h-1 rounded-full overflow-hidden">
            <div className="bg-primary h-full w-2/3"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
