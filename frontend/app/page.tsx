"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken, setToken } from "@/lib/auth";
import LoginForm from "@/components/LoginForm";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    if (getToken()) {
      router.replace("/chat");
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <LoginForm
      onSuccess={(token) => {
        setToken(token);
        router.push("/chat");
      }}
    />
  );
}
