import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus, Trash2, Eye, Pencil, Briefcase, Users, FileText } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { apiFetch } from "@/api/client";

type CandidatureStatus = "en_attente" | "acceptee" | "refusee";

interface Offre {
  id: number;
  titre: string;
  description: string;
  localisation: string;
  salaire: string | null;
  date_creation: string;
}

interface CandidatureWithProfile {
  id: number;
  offre: number;
  date_postulation: string;
  statut: CandidatureStatus;
  candidat: { id: number; username: string; email: string };
}

export default function RHDashboard() {
  const { user } = useAuth();
  const [offres, setOffres] = useState<Offre[]>([]);
  const [selectedOffre, setSelectedOffre] = useState<string | null>(null);
  const [candidatures, setCandidatures] = useState<CandidatureWithProfile[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [editingOffre, setEditingOffre] = useState<Tables<"offres"> | null>(null);
  const [form, setForm] = useState({ titre: "", description: "", localisation: "", salaire: "" });
  const [loading, setLoading] = useState(true);

  const fetchOffres = async () => {
    if (!user) return;
    try {
      const data = await apiFetch<Offre[]>("/offres/mine/");
      setOffres(data || []);
    } catch (error: any) {
      toast.error(error.message || "Erreur lors du chargement des offres");
    } finally {
      setLoading(false);
    }
  };

  const fetchCandidatures = async (offreId: number) => {
    try {
      const data = await apiFetch<CandidatureWithProfile[]>(`/offres/${offreId}/candidatures/`);
      setCandidatures(data || []);
    } catch (error: any) {
      toast.error(error.message || "Erreur lors du chargement des candidatures");
    }
  };

  useEffect(() => {
    fetchOffres();
  }, [user]);

  useEffect(() => {
    if (selectedOffre) fetchCandidatures(selectedOffre);
  }, [selectedOffre]);

  const handleCreate = async () => {
    if (!user) return;
    try {
      await apiFetch<Offre>("/offres/mine/", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          salaire: form.salaire || null,
        }),
      });
      toast.success("Offre créée !");
      setCreateOpen(false);
      setForm({ titre: "", description: "", localisation: "", salaire: "" });
      fetchOffres();
    } catch (error: any) {
      toast.error(error.message || "Erreur lors de la création");
    }
  };

  const handleUpdate = async () => {
    if (!editingOffre) return;
    try {
      await apiFetch<Offre>(`/offres/${editingOffre.id}/`, {
        method: "PUT",
        body: JSON.stringify({
          ...form,
          salaire: form.salaire || null,
        }),
      });
      toast.success("Offre mise à jour !");
      setEditingOffre(null);
      fetchOffres();
    } catch (error: any) {
      toast.error(error.message || "Erreur lors de la mise à jour");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await apiFetch(`/offres/${id}/`, {
        method: "DELETE",
      });
      toast.success("Offre supprimée");
      fetchOffres();
      if (selectedOffre === id) {
        setSelectedOffre(null);
        setCandidatures([]);
      }
    } catch (error: any) {
      toast.error(error.message || "Erreur lors de la suppression");
    }
  };

  const updateCandidatureStatus = async (id: number, statut: CandidatureStatus) => {
    try {
      await apiFetch(`/candidatures/${id}/`, {
        method: "PATCH",
        body: JSON.stringify({ statut }),
      });
      toast.success("Statut mis à jour");
      if (selectedOffre) fetchCandidatures(selectedOffre);
    } catch (error: any) {
      toast.error(error.message || "Erreur");
    }
  };

  const OffreForm = ({ onSubmit, submitLabel }: { onSubmit: () => void; submitLabel: string }) => (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Titre</Label>
        <Input value={form.titre} onChange={(e) => setForm({ ...form, titre: e.target.value })} placeholder="Ex: Développeur Full-Stack" />
      </div>
      <div className="space-y-2">
        <Label>Description</Label>
        <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Décrivez le poste..." rows={4} />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Localisation</Label>
          <Input value={form.localisation} onChange={(e) => setForm({ ...form, localisation: e.target.value })} placeholder="Ex: Paris" />
        </div>
        <div className="space-y-2">
          <Label>Salaire (optionnel)</Label>
          <Input value={form.salaire} onChange={(e) => setForm({ ...form, salaire: e.target.value })} placeholder="Ex: 45k-55k€" />
        </div>
      </div>
      <Button onClick={onSubmit} className="w-full">{submitLabel}</Button>
    </div>
  );

  const statutBadge = (statut: CandidatureStatus) => {
    const map = {
      en_attente: { label: "En attente", variant: "outline" as const },
      acceptee: { label: "Acceptée", variant: "default" as const },
      refusee: { label: "Refusée", variant: "destructive" as const },
    };
    const s = map[statut];
    return <Badge variant={s.variant}>{s.label}</Badge>;
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground">Dashboard Recruteur</h1>
          <p className="text-muted-foreground mt-1">Gérez vos offres et candidatures</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Nouvelle offre
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="font-display">Créer une offre</DialogTitle>
            </DialogHeader>
            <OffreForm onSubmit={handleCreate} submitLabel="Créer l'offre" />
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
              <Briefcase className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{offres.length}</p>
              <p className="text-sm text-muted-foreground">Offres publiées</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="h-12 w-12 rounded-xl bg-accent/10 flex items-center justify-center">
              <Users className="h-6 w-6 text-accent" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">{candidatures.length}</p>
              <p className="text-sm text-muted-foreground">Candidatures (sélection)</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-6">
            <div className="h-12 w-12 rounded-xl bg-warning/10 flex items-center justify-center">
              <FileText className="h-6 w-6 text-warning" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">
                {candidatures.filter((c) => c.statut === "en_attente").length}
              </p>
              <p className="text-sm text-muted-foreground">En attente</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Offres list */}
        <div>
          <h2 className="text-xl font-display font-semibold mb-4 text-foreground">Mes offres</h2>
          {loading ? (
            <div className="flex justify-center py-10">
              <div className="h-6 w-6 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : offres.length === 0 ? (
            <Card><CardContent className="py-10 text-center text-muted-foreground">Aucune offre créée.</CardContent></Card>
          ) : (
            <div className="space-y-3">
              {offres.map((offre) => (
                <Card
                  key={offre.id}
                  className={`cursor-pointer transition-all ${selectedOffre === offre.id ? "border-primary shadow-sm" : "hover:border-primary/20"}`}
                  onClick={() => setSelectedOffre(offre.id)}
                >
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-foreground">{offre.titre}</p>
                      <p className="text-xs text-muted-foreground">{offre.localisation}</p>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingOffre(offre);
                          setForm({
                            titre: offre.titre,
                            description: offre.description,
                            localisation: offre.localisation,
                            salaire: offre.salaire || "",
                          });
                        }}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(offre.id);
                        }}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Candidatures */}
        <div>
          <h2 className="text-xl font-display font-semibold mb-4 text-foreground">Candidatures</h2>
          {!selectedOffre ? (
            <Card><CardContent className="py-10 text-center text-muted-foreground">Sélectionnez une offre pour voir les candidatures.</CardContent></Card>
          ) : candidatures.length === 0 ? (
            <Card><CardContent className="py-10 text-center text-muted-foreground">Aucune candidature pour cette offre.</CardContent></Card>
          ) : (
            <div className="space-y-3">
              {candidatures.map((c) => (
                <Card key={c.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <p className="font-medium text-foreground">{c.profiles?.username || "Candidat"}</p>
                        <p className="text-xs text-muted-foreground">{c.profiles?.email}</p>
                      </div>
                      {statutBadge(c.statut)}
                    </div>
                    <div className="flex items-center gap-2 mt-3">
                      <Select
                        value={c.statut}
                        onValueChange={(v) => updateCandidatureStatus(c.id, v as CandidatureStatus)}
                      >
                        <SelectTrigger className="w-40 h-8 text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="en_attente">En attente</SelectItem>
                          <SelectItem value="acceptee">Acceptée</SelectItem>
                          <SelectItem value="refusee">Refusée</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Edit dialog */}
      <Dialog open={!!editingOffre} onOpenChange={(open) => !open && setEditingOffre(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="font-display">Modifier l'offre</DialogTitle>
          </DialogHeader>
          <OffreForm onSubmit={handleUpdate} submitLabel="Mettre à jour" />
        </DialogContent>
      </Dialog>
    </div>
  );
}
