"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { AnalysisReport } from "@/lib/types";
import ReportView from "@/components/ReportView";
import { ErrorBanner, ReportSkeleton } from "@/components/ui";

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params?.id) return;
    api.incident(params.id).then(setReport).catch((e) => setError(e instanceof ApiError ? e.message : "Could not load report."));
  }, [params?.id]);

  if (error) return <div className="space-y-4"><ErrorBanner message={error} /><Link href="/history" className="btn-ghost">Back to history</Link></div>;
  if (!report) return <ReportSkeleton />;
  return (
    <div className="space-y-5">
      <Link href="/history" className="text-sm text-mist-400 transition hover:text-mist-100">← History</Link>
      <ReportView report={report} />
    </div>
  );
}
