
-- Add foreign key from candidatures to profiles for join capability
ALTER TABLE public.candidatures
ADD CONSTRAINT candidatures_candidat_id_profiles_fkey
FOREIGN KEY (candidat_id) REFERENCES public.profiles(id) ON DELETE CASCADE;

-- Also allow RH to view profiles of candidates who applied to their offres
CREATE POLICY "RH can view candidate profiles" ON public.profiles
FOR SELECT TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.candidatures c
    JOIN public.offres o ON c.offre_id = o.id
    WHERE c.candidat_id = profiles.id AND o.created_by = auth.uid()
  )
);
