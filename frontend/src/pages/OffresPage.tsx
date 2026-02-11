import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MapPin, DollarSign, Clock, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { motion } from "framer-motion";
import { apiFetch } from "@/api/client";

interface Offre {
  id: number;
  titre: string;
  description: string;
  localisation: string;
  salaire: string | null;
  date_creation: string;
}

export default function OffresPage() {
  const [offres, setOffres] = useState<Offre[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    const fetchOffres = async () => {
      try {
        const data = await apiFetch<Offre[]>("/offres/");
        setOffres(data || []);
      } finally {
        setLoading(false);
      }
    };
    fetchOffres();
  }, []);

  const filtered = offres.filter(
    (o) =>
      o.titre.toLowerCase().includes(search.toLowerCase()) ||
      o.localisation.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-10">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-display font-bold text-foreground mb-2">
              Offres d'emploi
            </h1>
            <p className="text-muted-foreground">
              {offres.length} offre{offres.length > 1 ? "s" : ""} disponible{offres.length > 1 ? "s" : ""}
            </p>
          </div>

          <div className="relative mb-8">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Rechercher par titre ou localisation..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>

          {loading ? (
            <div className="flex justify-center py-20">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-muted-foreground text-lg">Aucune offre trouvée.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filtered.map((offre, i) => (
                <motion.div
                  key={offre.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Link to={user ? `/offres/${offre.id}` : "/auth"}>
                    <Card className="hover:shadow-md hover:border-primary/20 transition-all cursor-pointer">
                      <CardHeader className="pb-2">
                        <div className="flex items-start justify-between gap-4">
                          <CardTitle className="text-lg font-display">{offre.titre}</CardTitle>
                          {offre.salaire && (
                            <Badge variant="secondary" className="shrink-0">
                              <DollarSign className="h-3 w-3 mr-1" />
                              {offre.salaire}
                            </Badge>
                          )}
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                          {offre.description}
                        </p>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {offre.localisation}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {new Date(offre.date_creation).toLocaleDateString("fr-FR")}
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
