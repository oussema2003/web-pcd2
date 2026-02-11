import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { MapPin, DollarSign, Clock, ArrowLeft, Send } from "lucide-react";
import { apiFetch } from "@/api/client";

interface OffreDetail {
  id: number;
  titre: string;
  description: string;
  localisation: string;
  salaire: string | null;
  date_creation: string;
  has_applied: boolean;
}

export default function OffreDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user, role } = useAuth();
  const navigate = useNavigate();
  const [offre, setOffre] = useState<OffreDetail | null>(null);
  const [hasApplied, setHasApplied] = useState(false);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      if (!id) return;
      try {
        const data = await apiFetch<OffreDetail>(`/offres/${id}/`);
        setOffre(data);
        setHasApplied(data.has_applied);
      } catch (error: any) {
        toast.error(error.message || "Erreur lors du chargement de l'offre");
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [id, user]);

  const handleApply = async () => {
    if (!user || !id) return;
    setApplying(true);
    try {
      await apiFetch(`/offres/${id}/postuler/`, {
        method: "POST",
      });
      toast.success("Candidature envoyée !");
      setHasApplied(true);
    } catch (error: any) {
      toast.error(error.message || "Erreur lors de la candidature");
    } finally {
      setApplying(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!offre) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <p className="text-muted-foreground">Offre introuvable.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-10 max-w-3xl">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="mb-6">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Retour
        </Button>

        <Card>
          <CardHeader>
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <CardTitle className="text-2xl font-display">{offre.titre}</CardTitle>
              {offre.salaire && (
                <Badge variant="secondary" className="text-sm">
                  <DollarSign className="h-3 w-3 mr-1" />
                  {offre.salaire}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground mt-2">
              <span className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                {offre.localisation}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {new Date(offre.date_creation).toLocaleDateString("fr-FR")}
              </span>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="prose prose-sm max-w-none">
              <p className="text-foreground whitespace-pre-wrap">{offre.description}</p>
            </div>

            {role === "candidate" && (
              <div className="pt-4 border-t border-border">
                {hasApplied ? (
                  <Badge variant="outline" className="text-sm py-2 px-4">
                    ✓ Candidature envoyée
                  </Badge>
                ) : (
                  <Button onClick={handleApply} disabled={applying}>
                    <Send className="h-4 w-4 mr-2" />
                    {applying ? "Envoi..." : "Postuler"}
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
