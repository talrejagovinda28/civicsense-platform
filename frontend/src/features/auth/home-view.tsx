import Link from "next/link";
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs";

export function HomeView() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-8 px-6">
      <div>
        <p className="text-sm font-medium uppercase tracking-wide text-neutral-500">
          Pune MVP
        </p>
        <h1 className="mt-2 text-4xl font-bold tracking-tight">CivicSense</h1>
        <p className="mt-4 text-lg text-neutral-600">
          Report civic issues in your city. Sprint 1 foundation is live.
        </p>
      </div>

      <div className="flex items-center gap-4">
        <SignedOut>
          <SignInButton mode="modal">
            <button className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white">
              Sign in
            </button>
          </SignInButton>
        </SignedOut>

        <SignedIn>
          <Link
            href="/complaints"
            className="rounded-lg border border-neutral-300 px-4 py-2 text-sm font-medium"
          >
            View Feed
          </Link>
          <Link
            href="/complaints/new"
            className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white"
          >
            Raise Complaint
          </Link>
          <Link
            href="/dashboard"
            className="rounded-lg border border-neutral-300 px-4 py-2 text-sm font-medium"
          >
            Dashboard
          </Link>
          <UserButton />
        </SignedIn>
      </div>
    </main>
  );
}
