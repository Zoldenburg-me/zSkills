create table public.profiles (
  id uuid primary key references auth.users(id),
  email text not null,
  role text not null default 'user',
  plan text not null default 'free'
);

create table public.documents (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references public.profiles(id),
  title text not null,
  content text not null,
  created_at timestamptz default now()
);

alter table public.profiles enable row level security;
create policy "profiles are readable" on public.profiles for select using (true);
create policy "profiles are writable" on public.profiles for update using (true);
