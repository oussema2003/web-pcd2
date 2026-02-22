import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { MapPin, DollarSign, Clock, ArrowLeft, Send, Upload } from "lucide-react";
import { apiFetch } from "@/api/client";

interface OffreDetail {
  id: number;
  titre: string;
  description: string;
  localisation: string;
  salaire: string | null;
  date_creation: string;
  has_applied: boolean;
  questions?: Array<{ id: number; text: string; required: boolean; input_type: string }>;
}

export default function OffreDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user, role } = useAuth();
  const navigate = useNavigate();
  const [offre, setOffre] = useState<OffreDetail | null>(null);
  const [hasApplied, setHasApplied] = useState(false);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    nom: "",
    prenom: "",
    email: "",
    telephone: "",
    cv: null as File | null,
    video: null as File | null,
    answers: {} as Record<number, string>
  });
  const [fileNames, setFileNames] = useState({
    cv: "",
    video: "",
  });

  useEffect(() => {
    const fetch = async () => {
      if (!id) return;
      try {
        const data = await apiFetch<OffreDetail>(`/offres/${id}/`);
        setOffre(data);
        setHasApplied(data.has_applied);
      } catch (error: Error | unknown) {
        const message = error instanceof Error ? error.message : "Erreur lors du chargement de l'offre";
        toast.error(message);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [id, user]);

  const handleApply = async () => {
    if (!user || !id) return;
    setShowForm(true);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    fileType: "cv" | "video"
  ) => {
    const file = e.target.files?.[0];
    if (file) {
      setFormData((prev) => ({ ...prev, [fileType]: file }));
      setFileNames((prev) => ({ ...prev, [fileType]: file.name }));
    }
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (
      !formData.nom ||
      !formData.prenom ||
      !formData.email ||
      !formData.telephone ||
      !formData.cv ||
      !formData.video
    ) {
      toast.error("Veuillez remplir tous les champs");
      return;
    }

    setApplying(true);
    try {
      const formDataObj = new FormData();
      formDataObj.append("nom", formData.nom);
      formDataObj.append("prenom", formData.prenom);
      formDataObj.append("email", formData.email);
      formDataObj.append("telephone", formData.telephone);
      formDataObj.append("cv", formData.cv);
      formDataObj.append("video", formData.video);
      // Attach answers as a JSON string
      if (offre?.questions && Object.keys(formData.answers).length > 0) {
        formDataObj.append("answers", JSON.stringify(formData.answers));
      }

      console.log("Envoi de la candidature...", {
        nom: formData.nom,
        prenom: formData.prenom,
        email: formData.email,
        telephone: formData.telephone,
        cv_size: formData.cv?.size,
        video_size: formData.video?.size,
      });

      const response = await apiFetch(`/offres/${id}/postuler/`, {
        method: "POST",
        body: formDataObj,
      });

      console.log("Réponse du serveur:", response);

      toast.success("Candidature envoyée avec succès !");
      setHasApplied(true);
      setShowForm(false);
      setFormData({
        nom: "",
        prenom: "",
        email: "",
        telephone: "",
        cv: null,
        video: null,
      });
      setFileNames({ cv: "", video: "" });
    } catch (error: Error | unknown) {
      const message =
        error instanceof Error ? error.message : "Erreur lors de la candidature";
      console.error("Erreur candidature:", error);
      toast.error(message);
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

        {/* Application Form Dialog */}
        <Dialog open={showForm} onOpenChange={setShowForm}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Formulaire de Candidature</DialogTitle>
              <DialogDescription>
                Veuillez remplir tous les champs pour postuler à cette offre
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleFormSubmit} className="space-y-6">
              {/* Coordonnées Personnelles */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold">Informations Personnelles</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="prenom">Prénom *</Label>
                    <Input
                      id="prenom"
                      name="prenom"
                      placeholder="Votre prénom"
                      value={formData.prenom}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="nom">Nom *</Label>
                    <Input
                      id="nom"
                      name="nom"
                      placeholder="Votre nom"
                      value={formData.nom}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email *</Label>
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      placeholder="votre.email@example.com"
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="telephone">Téléphone *</Label>
                    <Input
                      id="telephone"
                      name="telephone"
                      type="tel"
                      placeholder="+216 XX XXX XXX"
                      value={formData.telephone}
                      onChange={handleInputChange}
                      required
                    />
                  </div>
                </div>
              </div>

              {/* File Uploads */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold">Documents</h3>

                {/* CV Upload */}
                <div className="space-y-2">
                  <Label htmlFor="cv">Télécharger CV (PDF, DOC) *</Label>
                  <label
                    htmlFor="cv"
                    className="flex items-center justify-center w-full px-4 py-8 border-2 border-dashed border-border rounded-lg cursor-pointer hover:bg-accent transition-colors"
                  >
                    <div className="text-center">
                      <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                      <p className="text-sm font-medium">
                        {fileNames.cv || "Cliquez pour sélectionner votre CV"}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        PDF, DOC, DOCX (Max 10MB)
                      </p>
                    </div>
                    <input
                      id="cv"
                      type="file"
                      accept=".pdf,.doc,.docx"
                      onChange={(e) => handleFileChange(e, "cv")}
                      className="hidden"
                      required
                    />
                  </label>
                </div>

                {/* Video Upload */}
                <div className="space-y-2">
                  <Label htmlFor="video">Télécharger Vidéo de Présentation *</Label>
                  <label
                    htmlFor="video"
                    className="flex items-center justify-center w-full px-4 py-8 border-2 border-dashed border-border rounded-lg cursor-pointer hover:bg-accent transition-colors"
                  >
                    <div className="text-center">
                      <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                      <p className="text-sm font-medium">
                        {fileNames.video || "Cliquez pour sélectionner votre vidéo"}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        MP4, AVI, MOV (Max 50MB)
                      </p>
                    </div>
                    <input
                      id="video"
                      type="file"
                      accept="video/*,.mp4,.avi,.mov"
                      onChange={(e) => handleFileChange(e, "video")}
                      className="hidden"
                      required
                    />
                  </label>
                </div>
              </div>

              {/* Dynamic Questions */}
              {offre.questions && offre.questions.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold">Questions supplémentaires</h3>
                  {offre.questions.map((q) => (
                    <div key={q.id} className="space-y-2">
                      <Label htmlFor={`q_${q.id}`}>{q.text} {q.required ? '*' : ''}</Label>
                      {q.input_type === 'textarea' ? (
                        <textarea
                          id={`q_${q.id}`}
                          className="w-full p-2 border rounded"
                          required={q.required}
                          value={formData.answers[q.id] || ''}
                          onChange={(e) => setFormData((prev) => ({ ...prev, answers: { ...prev.answers, [q.id]: e.target.value } }))}
                        />
                      ) : (
                        <Input
                          id={`q_${q.id}`}
                          value={formData.answers[q.id] || ''}
                          onChange={(e) => setFormData((prev) => ({ ...prev, answers: { ...prev.answers, [q.id]: e.target.value } }))}
                          required={q.required}
                        />
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Form Actions */}
              <div className="flex justify-end gap-3 pt-6 border-t border-border">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowForm(false)}
                  disabled={applying}
                >
                  Annuler
                </Button>
                <Button type="submit" disabled={applying}>
                  {applying ? "Envoi en cours..." : "Envoyer Candidature"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
