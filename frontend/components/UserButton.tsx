// components/UserButton.tsx (optional little indicator)
"use client";
import { useUser } from "@auth0/nextjs-auth0/client";

export function UserButton() {
  const { user, isLoading } = useUser();
  if (isLoading || !user) return null;
  const first = user.name?.split(" ")[0] ?? "You";
  return (
    <div className="flex items-center gap-2">
      {user.picture && <img src={user.picture} alt="avatar" className="h-6 w-6 rounded-full" />}
      <span className="font-mono text-sm">Hi, {first}</span>
    </div>
  );
}
