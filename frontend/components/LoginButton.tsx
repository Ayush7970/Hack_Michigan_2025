"use client";

import Link from "next/link";
import { useUser } from "@auth0/nextjs-auth0/client";
import type { ReactNode } from "react";

type LoginButtonProps = {
  className?: string;
  children?: ReactNode;
};

export default function LoginButton({ className, children }: LoginButtonProps) {
  const { user, isLoading } = useUser();
  if (isLoading) return null;

  // Use defaults if no children provided
  const label = children ?? (user ? "Log Out" : "Log In");
  const href = user ? "/api/auth/logout" : "/api/auth/login";

  return (
    <Link className={className} href={href}>
      {label}
    </Link>
  );
}