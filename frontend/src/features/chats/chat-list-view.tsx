"use client";



import { useAuth } from "@clerk/nextjs";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import Link from "next/link";

import { useRouter } from "next/navigation";

import { useState } from "react";



import { AppShell } from "@/features/shell/app-shell";

import { createGroupChat, getChats, getReputation } from "@/lib/api";



export function ChatListView() {

  const { getToken, isLoaded, isSignedIn } = useAuth();

  const queryClient = useQueryClient();

  const router = useRouter();

  const [groupName, setGroupName] = useState("");

  const [showCreateGroup, setShowCreateGroup] = useState(false);

  const [createError, setCreateError] = useState<string | null>(null);



  const chatsQuery = useQuery({

    queryKey: ["chats"],

    queryFn: async () => {

      const token = await getToken();

      if (!token) {

        return [];

      }

      return getChats(token);

    },

    enabled: isLoaded && Boolean(isSignedIn),

  });



  const reputationQuery = useQuery({

    queryKey: ["reputation-me"],

    queryFn: async () => {

      const token = await getToken();

      if (!token) {

        return null;

      }

      return getReputation(token);

    },

    enabled: isLoaded && Boolean(isSignedIn),

  });



  const createGroupMutation = useMutation({

    mutationFn: async () => {

      const token = await getToken();

      if (!token) {

        throw new Error("Sign in to create a group.");

      }

      if (!groupName.trim()) {

        throw new Error("Enter a group name.");

      }

      const result = await createGroupChat(token, {

        name: groupName.trim(),

        type: "private",

      });

      if (!result.ok) {

        throw new Error(result.error);

      }

      return result.data!;

    },

    onSuccess: (data) => {

      setGroupName("");

      setShowCreateGroup(false);

      setCreateError(null);

      void queryClient.invalidateQueries({ queryKey: ["chats"] });

      router.push(`/chats/${data.id}`);

    },

    onError: (error) => {

      setCreateError(error instanceof Error ? error.message : "Could not create group.");

    },

  });



  const chats = Array.isArray(chatsQuery.data) ? chatsQuery.data : [];

  const canCreateGroups = reputationQuery.data?.unlocks?.can_create_groups ?? false;

  const isEmpty = !chatsQuery.isLoading && chats.length === 0;



  return (

    <AppShell>

      <div className="space-y-6">

        <div className="flex flex-wrap items-start justify-between gap-4">

          <div>

            <h1 className="text-2xl font-bold text-civic-navy">Chats</h1>

            <p className="mt-1 text-sm text-[var(--muted)]">

              Direct messages and group conversations.

            </p>

          </div>

          {canCreateGroups && (

            <button

              type="button"

              onClick={() => setShowCreateGroup((open) => !open)}

              className="rounded-lg bg-civic-navy px-4 py-2 text-sm font-medium text-white"

            >

              {showCreateGroup ? "Cancel" : "Create group"}

            </button>

          )}

        </div>



        {showCreateGroup && canCreateGroups && (

          <form

            className="rounded-xl border border-civic bg-[var(--surface-muted)] p-4"

            onSubmit={(event) => {

              event.preventDefault();

              createGroupMutation.mutate();

            }}

          >

            <label className="block text-sm font-medium">

              Group name

              <input

                type="text"

                value={groupName}

                onChange={(event) => setGroupName(event.target.value)}

                className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"

                placeholder="Neighborhood watch"

              />

            </label>

            {createError && <p className="mt-2 text-sm text-red-600">{createError}</p>}

            <button

              type="submit"

              disabled={createGroupMutation.isPending || !groupName.trim()}

              className="mt-3 rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"

            >

              {createGroupMutation.isPending ? "Creating…" : "Create group chat"}

            </button>

          </form>

        )}



        {!canCreateGroups && reputationQuery.data && (

          <p className="text-sm text-[var(--muted)]">

            Group creation unlocks at 500 eligible XP.

          </p>

        )}



        {chatsQuery.isLoading && (

          <p className="text-sm text-[var(--muted)]">Loading chats…</p>

        )}



        {chatsQuery.error && (

          <p className="text-sm text-red-600">Could not load chats.</p>

        )}



        {isEmpty && (

          <div className="rounded-lg border border-civic bg-[var(--surface-muted)] px-4 py-6 text-center">

            <p className="text-sm font-medium text-civic-navy">No conversations yet</p>

            <p className="mt-1 text-sm text-[var(--muted)]">

              Start a direct message from someone&apos;s profile, or create a group when

              unlocked.

            </p>

          </div>

        )}



        {chats.length > 0 && (

          <ul className="divide-y divide-[var(--border)] overflow-hidden rounded-xl border border-civic bg-[var(--surface)]">

            {chats.map((chat) => (

              <li key={chat.id}>

                <Link

                  href={`/chats/${chat.id}`}

                  className="flex items-center justify-between gap-4 px-4 py-3 transition hover:bg-[var(--surface-muted)]"

                >

                  <div className="min-w-0">

                    <p className="font-medium text-civic-navy">{chat.title}</p>

                    {chat.last_message_preview ? (

                      <p className="mt-0.5 truncate text-sm text-[var(--muted)]">

                        {chat.last_message_preview}

                      </p>

                    ) : (

                      <p className="mt-0.5 text-sm text-[var(--muted)]">No messages yet</p>

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

        )}

      </div>

    </AppShell>

  );

}

