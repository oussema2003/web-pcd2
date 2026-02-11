import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Briefcase, LogOut, LayoutDashboard, Menu, X } from "lucide-react";
import { useState } from "react";

export default function Navbar() {
  const { user, role, signOut } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleSignOut = async () => {
    await signOut();
    navigate("/");
  };

  return (
    <nav className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-lg">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-xl bg-primary flex items-center justify-center">
            <Briefcase className="h-4 w-4 text-primary-foreground" />
          </div>
          <span className="text-xl font-display font-bold text-foreground">RecruPro</span>
        </Link>

        {/* Desktop */}
        <div className="hidden md:flex items-center gap-4">
          {user ? (
            <>
              <Link to="/offres" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                Offres
              </Link>
              <Link to="/dashboard" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                <span className="flex items-center gap-1">
                  <LayoutDashboard className="h-4 w-4" />
                  Dashboard
                </span>
              </Link>
              <div className="flex items-center gap-2 ml-2 pl-4 border-l border-border">
                <span className="text-xs font-medium px-2 py-1 rounded-full bg-primary/10 text-primary">
                  {role === "rh" ? "Recruteur" : "Candidat"}
                </span>
                <Button variant="ghost" size="sm" onClick={handleSignOut}>
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            </>
          ) : (
            <>
              <Link to="/offres" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                Offres
              </Link>
              <Button variant="default" size="sm" onClick={() => navigate("/auth")}>
                Connexion
              </Button>
            </>
          )}
        </div>

        {/* Mobile toggle */}
        <button className="md:hidden" onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-border bg-background px-4 py-4 space-y-3">
          <Link to="/offres" className="block text-sm font-medium text-muted-foreground" onClick={() => setMobileOpen(false)}>
            Offres
          </Link>
          {user ? (
            <>
              <Link to="/dashboard" className="block text-sm font-medium text-muted-foreground" onClick={() => setMobileOpen(false)}>
                Dashboard
              </Link>
              <button onClick={handleSignOut} className="text-sm font-medium text-destructive">
                Déconnexion
              </button>
            </>
          ) : (
            <Button variant="default" size="sm" className="w-full" onClick={() => { navigate("/auth"); setMobileOpen(false); }}>
              Connexion
            </Button>
          )}
        </div>
      )}
    </nav>
  );
}
