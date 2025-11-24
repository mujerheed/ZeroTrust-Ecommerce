"use client";

import { Sidebar } from "@/components/ceo/Sidebar";
import { TopBar } from "@/components/ceo/TopBar";

interface CEOLayoutProps {
  children: React.ReactNode;
}

export function CEOLayout({ children }: CEOLayoutProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-950">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Top Bar */}
        <TopBar />

        {/* Page Content - Centered with max-width */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
