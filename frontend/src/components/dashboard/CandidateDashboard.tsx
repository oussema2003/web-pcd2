import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, CheckCircle, Clock, XCircle } from "lucide-react";
import { apiFetch } from "@/api/client";

type CandidatureStatus = "en_attente" | "acceptee" | "refusee";

interface Offre {
  id: number;
  titre: string;
  localisation: string;
  salaire: string | null;
}

interface CandidatureWithOffre {
  id: number;
  offre: Offre;
  date_postulation: string;
  statut: CandidatureStatus;
}

export default function CandidateDashboard() {
  const { user, loading: authLoading } = useAuth();
  const [candidatures, setCandidatures] = useState<CandidatureWithOffre[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      if (authLoading) return;
      if (!user) {
        setCandidatures([]);
        setLoading(false);
        return;
      }
      try {
        setError(null);
        const data = await apiFetch<CandidatureWithOffre[]>("/candidatures/me/");
        setCandidatures(data || []);
      } catch (err: any) {
        setError(err?.message || "Erreur lors de la récupération des candidatures.");
        setCandidatures([]);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [user]);

  const statutConfig: Record<
    CandidatureStatus,
    { label: string; icon: typeof Clock; variant: "outline" | "default" | "destructive"; color: string }
  > = {
    en_attente: { label: "En attente", icon: Clock, variant: "outline" as const, color: "text-warning" },
    acceptee: { label: "Acceptée", icon: CheckCircle, variant: "default" as const, color: "text-success" },
    refusee: { label: "Refusée", icon: XCircle, variant: "destructive" as const, color: "text-destructive" },
  };

  const stats = {
    total: candidatures.length,
    en_attente: candidatures.filter((c) => c.statut === "en_attente").length,
    acceptee: candidatures.filter((c) => c.statut === "acceptee").length,
    refusee: candidatures.filter((c) => c.statut === "refusee").length,
  };

  // Render list content with explicit branches to avoid nested JSX ternary parsing issues
  let listContent: JSX.Element;
  if (loading) {
    listContent = (
      <div className="flex justify-center py-10">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  } else if (candidatures.length === 0) {
    listContent = error ? (
      <Card>
        <CardContent className="py-16 text-center">
          <p className="text-destructive text-lg">{error}</p>
          <p className="text-muted-foreground text-sm mt-1">Vérifiez que le backend est démarré et reconnectez-vous.</p>
        </CardContent>
      </Card>
    ) : (
      <Card>
        <CardContent className="py-16 text-center">
          <FileText className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
          <p className="text-muted-foreground text-lg">Aucune candidature pour le moment.</p>
          <p className="text-muted-foreground text-sm mt-1">Parcourez les offres pour postuler.</p>
        </CardContent>
      </Card>
    );
  } else {
    listContent = (
      <div className="space-y-3">
        {candidatures.map((c) => {
          const config = statutConfig[c.statut];
          const Icon = config.icon;
          return (
            <Card key={c.id} className="hover:shadow-sm transition-all">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="font-medium text-foreground">{c.offre?.titre || "Offre"}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {c.offre?.localisation} • Postulé le {new Date(c.date_postulation).toLocaleDateString("fr-FR")}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Icon className={`h-4 w-4 ${config.color}`} />
                  <Badge variant={config.variant}>{config.label}</Badge>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-display font-bold text-foreground">Mes Candidatures</h1>
        <p className="text-muted-foreground mt-1">Suivez l'état de vos candidatures</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="flex items-center gap-3 p-5">
            <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <FileText className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-xl font-bold text-foreground">{stats.total}</p>
              <p className="text-xs text-muted-foreground">Total</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 p-5">
            <div className="h-10 w-10 rounded-xl bg-warning/10 flex items-center justify-center">
              <Clock className="h-5 w-5 text-warning" />
            </div>
            <div>
              <p className="text-xl font-bold text-foreground">{stats.en_attente}</p>
              <p className="text-xs text-muted-foreground">En attente</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 p-5">
            <div className="h-10 w-10 rounded-xl bg-success/10 flex items-center justify-center">
              <CheckCircle className="h-5 w-5 text-success" />
            </div>
            <div>
              <p className="text-xl font-bold text-foreground">{stats.acceptee}</p>
              <p className="text-xs text-muted-foreground">Acceptées</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 p-5">
            <div className="h-10 w-10 rounded-xl bg-destructive/10 flex items-center justify-center">
              <XCircle className="h-5 w-5 text-destructive" />
            </div>
            <div>
              <p className="text-xl font-bold text-foreground">{stats.refusee}</p>
              <p className="text-xs text-muted-foreground">Refusées</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* List */}
      {listContent}
    </div>
  );
}
