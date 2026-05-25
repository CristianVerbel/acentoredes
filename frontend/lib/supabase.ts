import { createClient } from "@supabase/supabase-js";

// Variables públicas (se inyectan en build). En Vercel/Supabase usa la
// "Project URL" y la "anon public" key del proyecto. Son seguras de exponer:
// el acceso está restringido por las políticas RLS definidas en el SQL.
const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://placeholder.supabase.co";
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "placeholder-anon-key";

export const supabase = createClient(url, anonKey, {
  auth: { persistSession: false },
});

export const supabaseConfigured =
  !!process.env.NEXT_PUBLIC_SUPABASE_URL && !!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
