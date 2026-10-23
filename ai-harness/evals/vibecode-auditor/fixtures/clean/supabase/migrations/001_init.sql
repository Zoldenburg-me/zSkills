create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  role text not null default 'user',
  plan text not null default 'free'
);

create table public.documents (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references public.profiles(id) on delete cascade,
  title text not null,
  content text not null,
  created_at timestamptz default now()
);

alter table public.profiles enable row level security;
alter table public.documents enable row level security;

-- Users read their own profile; role and plan change only through the service role.
create policy "own profile" on public.profiles for select using (auth.uid() = id);

create policy "own documents read" on public.documents for select using (auth.uid() = owner_id);
create policy "own documents insert" on public.documents for insert with check (auth.uid() = owner_id);
create policy "own documents update" on public.documents for update using (auth.uid() = owner_id) with check (auth.uid() = owner_id);
create policy "own documents delete" on public.documents for delete using (auth.uid() = owner_id);

-- Every new auth user gets a profile row.
create function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles (id, email) values (new.id, new.email);
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
