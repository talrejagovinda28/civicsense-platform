"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { AppShell } from "@/features/shell/app-shell";
import { getChats } from "@/lib/api";

export function ChatListView() {
  const { getToken, isLoaded } = useAuth();

  const chatsQuery = useQuery({
    queryKey: ["chats"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) {
        return [];
      }
      return getChats(token);
    },
    enabled: isLoaded,
  });

  const unavailable =
    !chatsQuery.isLoading && chatsQuery.data !== undefined && chatsQuery.data.length === 0;

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-civic-navy">Chats</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Direct messages and group conversations.
          </p>
        </div>

        {chatsQuery.isLoading && (
          <p className="text-sm text-[var(--muted)]">Loading chats…</p>
        )}

        {chatsQuery.error && (
          <p className="text-sm text-red-600">Could not load chats.</p>
        )}

        {unavailable && (
          <p className="rounded-lg border border-civic bg-[var(--surface-muted)] px-4 py-3 text-sm text-[var(--muted)]">
            No conversations yet, or the messaging API is not deployed.
          </p>
        )}

        <ul className="divide-y divide-[var(--border)] overflow-hidden rounded-xl border border-civic bg-[var(--surface)]">
          {chatsQuery.data?.map((chat) => (
            <li key={chat.id}>
              <Link
                href={`/chats/${chat.id}`}
                className="flex items-center justify-between gap-4 px-4 py-3 transition hover:bg-[var(--surface-muted)]"
              >
                <div className="min-w-0">
                  <p className="font-medium text-civic-navy">{chat.title}</p>
                  {chat.last_message_preview && (
                    <p className="mt-0.5 truncate text-sm text-[var(--muted)]">
                      {chat.last_message_preview}
                    </p>
                  )}
                </div>
                <div className="shrink-0 text-right">
                  {chat.last_message_at && (
                    <time className="text-xs text-[var(--muted)]">
                      {new Date(chat.last_message_at).toLocaleDateString()}
                    </time>
                  )}
                  {chat.unread_count > 0 && (
                    <span className="mt-1 inline-block rounded-full bg-[var(--primary)] px-2 py-0.5 text-xs text-white">
                      {chat.unread_count}
                    </span>
                  )}
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </AppShell>
  );
}
