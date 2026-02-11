
-- Create role enum
CREATE TYPE public.app_role AS ENUM ('rh', 'candidate');

-- Create profiles table
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT NOT NULL,
  email TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT TO authenticated USING (id = auth.uid());
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE TO authenticated USING (id = auth.uid());
CREATE POLICY "Users can insert own profile" ON public.profiles FOR INSERT TO authenticated WITH CHECK (id = auth.uid());

-- Create user_roles table
CREATE TABLE public.user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  role app_role NOT NULL,
  UNIQUE (user_id, role)
);

ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

-- Security definer function to check roles
CREATE OR REPLACE FUNCTION public.has_role(_user_id UUID, _role app_role)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.user_roles WHERE user_id = _user_id AND role = _role
  )
$$;

-- RLS for user_roles
CREATE POLICY "Users can view own roles" ON public.user_roles FOR SELECT TO authenticated USING (user_id = auth.uid());

-- Function to get current user role
CREATE OR REPLACE FUNCTION public.get_user_role(_user_id UUID)
RETURNS app_role
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT role FROM public.user_roles WHERE user_id = _user_id LIMIT 1
$$;

-- Create offres table
CREATE TABLE public.offres (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titre TEXT NOT NULL,
  description TEXT NOT NULL,
  localisation TEXT NOT NULL,
  salaire TEXT,
  date_creation TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL
);

ALTER TABLE public.offres ENABLE ROW LEVEL SECURITY;

-- Everyone authenticated can view offres
CREATE POLICY "Authenticated users can view offres" ON public.offres FOR SELECT TO authenticated USING (true);
-- Only RH can insert
CREATE POLICY "RH can create offres" ON public.offres FOR INSERT TO authenticated WITH CHECK (public.has_role(auth.uid(), 'rh'));
-- Only RH who created can update
CREATE POLICY "RH can update own offres" ON public.offres FOR UPDATE TO authenticated USING (created_by = auth.uid() AND public.has_role(auth.uid(), 'rh'));
-- Only RH who created can delete
CREATE POLICY "RH can delete own offres" ON public.offres FOR DELETE TO authenticated USING (created_by = auth.uid() AND public.has_role(auth.uid(), 'rh'));

-- Create candidatures table
CREATE TYPE public.candidature_statut AS ENUM ('en_attente', 'acceptee', 'refusee');

CREATE TABLE public.candidatures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  candidat_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  offre_id UUID REFERENCES public.offres(id) ON DELETE CASCADE NOT NULL,
  date_postulation TIMESTAMPTZ NOT NULL DEFAULT now(),
  statut candidature_statut NOT NULL DEFAULT 'en_attente',
  UNIQUE (candidat_id, offre_id)
);

ALTER TABLE public.candidatures ENABLE ROW LEVEL SECURITY;

-- Candidates can view own candidatures
CREATE POLICY "Candidates can view own candidatures" ON public.candidatures FOR SELECT TO authenticated USING (candidat_id = auth.uid());
-- RH can view candidatures for their offres
CREATE POLICY "RH can view candidatures for own offres" ON public.candidatures FOR SELECT TO authenticated USING (
  EXISTS (SELECT 1 FROM public.offres WHERE offres.id = offre_id AND offres.created_by = auth.uid())
);
-- Only candidates can insert
CREATE POLICY "Candidates can apply" ON public.candidatures FOR INSERT TO authenticated WITH CHECK (
  candidat_id = auth.uid() AND public.has_role(auth.uid(), 'candidate')
);
-- Only RH can update status
CREATE POLICY "RH can update candidature status" ON public.candidatures FOR UPDATE TO authenticated USING (
  EXISTS (SELECT 1 FROM public.offres WHERE offres.id = offre_id AND offres.created_by = auth.uid())
);

-- Trigger to auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, username, email)
  VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1)), NEW.email);
  
  INSERT INTO public.user_roles (user_id, role)
  VALUES (NEW.id, (NEW.raw_user_meta_data->>'role')::app_role);
  
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();
