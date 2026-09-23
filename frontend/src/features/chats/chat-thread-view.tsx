"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { AppShell } from "@/features/shell/app-shell";
import { getChatMessages, sendChatMessage } from "@/lib/api";

const POLL_INTERVAL_MS = 8000;

type ChatThreadViewProps = {
  chatId: string;
};

export function ChatThreadView({ chatId }: ChatThreadViewProps) {
  const { getToken, isLoaded } = useAuth();
  const queryClient = useQueryClient();
  const [body, setBody] = useState("");
  const [sendError, setSendError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const messagesQuery = useQuery({
    queryKey: ["chat-messages", chatId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) {
        return null;
      }
      return getChatMessages(token, chatId);
    },
    enabled: isLoaded,
    refetchInterval: () =>
      typeof document !== "undefined" && document.visibilityState === "visible"
        ? POLL_INTERVAL_MS
        : false,
  });

  const sendMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token || !body.trim()) {
        throw new Error("Enter a message.");
      }
      const result = await sendChatMessage(token, chatId, body.trim());
      if (!result.ok) {
        throw new Error(result.error);
      }
      return result.data;
    },
    onSuccess: () => {
      setBody("");
      setSendError(null);
      void queryClient.invalidateQueries({ queryKey: ["chat-messages", chatId] });
    },
    onError: (error) => {
      setSendError(error instanceof Error ? error.message : "Could not send message.");
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messagesQuery.data?.items.length]);

  const unavailable = messagesQuery.data === null && !messagesQuery.isLoading;

  return (
    <AppShell>
      <div className="flex min-h-[70vh] flex-col">
        <div className="mb-4">
          <Link href="/chats" className="text-sm text-[var(--muted)] hover:text-civic-navy">
            ← Back to chats
          </Link>
        </div>

        {messagesQuery.isLoading && (
          <p className="text-sm text-[var(--muted)]">Loading messages…</p>
        )}

        {unavailable && (
          <p className="rounded-lg border border-civic bg-[var(--surface-muted)] px-4 py-3 text-sm text-[var(--muted)]">
            Messages are not available yet — the API endpoint is not deployed.
          </p>
        )}

        <div className="flex-1 space-y-3 overflow-y-auto rounded-xl border border-civic bg-[var(--surface)] p-4">
          {messagesQuery.data?.items.map((message) => (
            <div key={message.id} className="rounded-lg bg-[var(--surface-muted)] px-3 py-2">
              <p className="text-xs font-medium text-civic-navy">
                {message.sender_display_name}
              </p>
              <p className="mt-1 text-sm">{message.body}</p>
              <time className="mt-1 block text-xs text-[var(--muted)]">
                {new Date(message.created_at).toLocaleString()}
              </time>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        <form
          className="mt-4 space-y-2"
          onSubmit={(event) => {
            event.preventDefault();
            sendMutation.mutate();
          }}
        >
          <label className="sr-only" htmlFor="chat-message">
            Message
          </label>
          <textarea
            id="chat-message"
            value={body}
            onChange={(event) => setBody(event.target.value)}
            rows={2}
            placeholder="Type a message…"
            className="w-full rounded-lg border border-civic px-3 py-2 text-sm"
            disabled={unavailable}
          />
          {sendError && <p className="text-sm text-red-600">{sendError}</p>}
          <button
            type="submit"
            disabled={!body.trim() || sendMutation.isPending || unavailable}
            className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
          >
            {sendMutation.isPending ? "Sending…" : "Send"}
          </button>
        </form>
      </div>
    </AppShell>
  );
}
