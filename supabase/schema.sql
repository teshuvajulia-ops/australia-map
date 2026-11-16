-- CITYSIDE: service providers directory
create table if not exists public.providers (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  name text not null check (char_length(name) between 2 and 60),
  category text not null check (category in ('moving','cleaning','handyman','tutoring','photo','visa','english','other')),
  city text not null check (city in ('melbourne','sydney')),
  description text not null check (char_length(description) between 10 and 600),
  price_note text check (price_note is null or char_length(price_note) <= 80),
  languages text[] not null default '{}' check (cardinality(languages) <= 8),
  whatsapp text not null check (whatsapp ~ '^[0-9]{8,15}$')
);

alter table public.providers enable row level security;

drop policy if exists "public read approved" on public.providers;
create policy "public read approved" on public.providers
  for select to anon using (status = 'approved');

drop policy if exists "public submit pending" on public.providers;
create policy "public submit pending" on public.providers
  for insert to anon with check (status = 'pending');

grant usage on schema public to anon;
grant select, insert on public.providers to anon;
