"use client";

import React from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";
import { useNavigationStore } from "@/hooks/useStore";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { sidebarOpen } = useNavigationStore();

  return (
    <div className="min-h-screen bg-background text-foreground flex">
      {/* Collapsible Left Sidebar */}
      <Sidebar />

      {/* Main Content Pane */}
      <div
        className={cn(
          "flex-1 flex flex-col min-w-0 transition-all duration-300 ease-in-out",
          sidebarOpen ? "pl-64" : "pl-20"
        )}
      >
        <Navbar />
        <main className="flex-1 p-4 lg:p-8 max-w-7xl w-full mx-auto space-y-6">
          {children}
        </main>
      </div>
    </div>
  );
}

