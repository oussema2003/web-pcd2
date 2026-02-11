import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Briefcase, Search, Users, ArrowRight, CheckCircle } from "lucide-react";
import { motion } from "framer-motion";

export default function LandingPage() {
  const navigate = useNavigate();

  const features = [
    {
      icon: Search,
      title: "Trouvez l'emploi idéal",
      description: "Parcourez des centaines d'offres et postulez en quelques clics.",
    },
    {
      icon: Users,
      title: "Recrutez les meilleurs talents",
      description: "Publiez vos offres et gérez les candidatures efficacement.",
    },
    {
      icon: CheckCircle,
      title: "Suivi en temps réel",
      description: "Suivez l'état de vos candidatures instantanément.",
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative overflow-hidden" style={{ background: "var(--gradient-hero)" }}>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_hsl(215_80%_48%_/_0.15),_transparent_70%)]" />
        <div className="container mx-auto px-4 py-24 md:py-36 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="max-w-3xl mx-auto text-center"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-8">
              <Briefcase className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium" style={{ color: "hsl(210, 20%, 90%)" }}>
                Plateforme de recrutement moderne
              </span>
            </div>
            <h1 className="text-4xl md:text-6xl font-display font-bold tracking-tight mb-6" style={{ color: "hsl(0, 0%, 100%)" }}>
              Connectez les talents
              <br />
              <span style={{ color: "hsl(160, 60%, 55%)" }}>aux opportunités</span>
            </h1>
            <p className="text-lg md:text-xl mb-10 max-w-2xl mx-auto" style={{ color: "hsl(210, 15%, 70%)" }}>
              RecruPro simplifie le recrutement. Candidats, trouvez votre prochain emploi.
              Recruteurs, trouvez les meilleurs profils.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                onClick={() => navigate("/auth")}
                className="text-base px-8 py-6"
              >
                Commencer gratuitement
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={() => navigate("/offres")}
                className="text-base px-8 py-6 border-primary/30 bg-primary/5 hover:bg-primary/10"
                style={{ color: "hsl(210, 20%, 90%)" }}
              >
                Voir les offres
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 md:py-28 bg-background">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-display font-bold text-foreground mb-4">
              Tout ce dont vous avez besoin
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Une solution complète pour candidats et recruteurs.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.15 }}
                viewport={{ once: true }}
                className="group p-8 rounded-2xl border border-border bg-card hover:shadow-lg hover:border-primary/20 transition-all duration-300"
              >
                <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center mb-5 group-hover:bg-primary/15 transition-colors">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-xl font-display font-semibold text-foreground mb-2">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-muted/40">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-display font-bold text-foreground mb-4">
            Prêt à commencer ?
          </h2>
          <p className="text-muted-foreground text-lg mb-8 max-w-lg mx-auto">
            Créez votre compte gratuitement et accédez à toutes les fonctionnalités.
          </p>
          <Button size="lg" onClick={() => navigate("/auth")} className="px-8 py-6 text-base">
            Créer un compte
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 bg-background">
        <div className="container mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <Briefcase className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="font-display font-bold text-foreground">RecruPro</span>
          </div>
          <p className="text-sm text-muted-foreground">© 2026 RecruPro. Tous droits réservés.</p>
        </div>
      </footer>
    </div>
  );
}
