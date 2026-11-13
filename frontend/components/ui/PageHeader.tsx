import React from "react";
import { ChevronRight } from "lucide-react";
import Link from "next/link";

interface PageHeaderProps {
  title: string;
  description: string;
  breadcrumbs?: { label: string; href?: string }[];
  action?: React.ReactNode;
}

export function PageHeader({
  title,
  description,
  breadcrumbs,
  action,
}: PageHeaderProps) {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border/60">
      <div>
        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav className="flex items-center space-x-1.5 text-xs text-muted mb-2 font-medium">
            {breadcrumbs.map((crumb, idx) => (
              <React.Fragment key={idx}>
                {idx > 0 && <ChevronRight className="w-3 h-3 text-muted/60" />}
                {crumb.href ? (
                  <Link
                    href={crumb.href}
                    className="hover:text-foreground transition"
                  >
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-foreground/90 font-semibold">
                    {crumb.label}
                  </span>
                )}
              </React.Fragment>
            ))}
          </nav>
        )}
        <h1 className="text-2xl font-black text-foreground tracking-tight">
          {title}
        </h1>
        <p className="text-xs text-muted mt-1 max-w-2xl leading-relaxed">
          {description}
        </p>
      </div>

      {action && <div className="flex items-center gap-3">{action}</div>}
    </div>
  );
}

