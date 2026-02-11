import { useAuth } from "@/hooks/useAuth";
import RHDashboard from "@/components/dashboard/RHDashboard";
import CandidateDashboard from "@/components/dashboard/CandidateDashboard";

export default function DashboardPage() {
  const { role, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-10">
        {role === "rh" ? <RHDashboard /> : <CandidateDashboard />}
      </div>
    </div>
  );
}
