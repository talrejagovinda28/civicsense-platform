"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import { AppShell } from "@/features/shell/app-shell";
import type { ComplaintFeedItem } from "@/lib/api";

const CivicMap = dynamic(
  () => import("@/features/map/civic-map").then((module) => module.CivicMap),
  { ssr: false, loading: () => <p className="p-6">Loading sample map…</p> },
);

type DemoIssue = ComplaintFeedItem & { likes: number; affected: number; comments: string[] };
type Tab = "feed" | "map" | "chats" | "profile" | "dashboard" | "report";
type Message = { author: string; body: string };
type Conversation = { title: string; messages: Message[] };

function makeIssue(n: number, title: string, description: string, category: string, area: string, status: string, lat: number, lng: number, likes: number, affected: number, comments: string[] = []): DemoIssue {
  return {
    id: `demo-${n}`, title, description, status, city: "Pune", ward: area,
    category: { id: `demo-cat-${n}`, name: category, slug: category.toLowerCase().replace(/\s+/g, "-") },
    category_id: null, electoral_ward_id: null, images: [], public_latitude: lat, public_longitude: lng,
    created_at: `2026-09-${String(15 + n).padStart(2, "0")}T09:00:00Z`, likes, affected, comments,
  };
}

const starterIssues: DemoIssue[] = [
  makeIssue(1, "Sample pothole near Deccan junction", "Illustrative report of damaged road surface near a junction. This is not a verified incident.", "Roads", "Deccan", "submitted", 18.5166, 73.8424, 12, 7, ["Demo neighbor: Adding a photo could help clarify this sample report."]),
  makeIssue(2, "Sample streetlight outage in Camp", "Fictional street lighting case to illustrate the issue-tracking flow.", "Street lighting", "Camp", "in_progress", 18.5134, 73.8790, 21, 13, ["Demo update: Inspection in progress (simulation only)."]),
  makeIssue(3, "Sample missed waste collection", "Example report to explore categories and resident engagement.", "Waste", "Kothrud", "submitted", 18.5074, 73.8077, 9, 5),
  makeIssue(4, "Sample water supply leak", "Fictional report demonstrating a progress update and an approximate map pin.", "Water", "Shivajinagar", "in_progress", 18.5314, 73.8479, 18, 11),
  makeIssue(5, "Sample footpath repair", "Illustrative resolved case; no real-world repair or official action is being claimed.", "Footpaths", "Aundh", "resolved", 18.559, 73.8073, 15, 8),
  makeIssue(6, "Sample drainage cover replacement", "Completed fictional case for reviewing closed status and filters.", "Drainage", "Hadapsar", "closed", 18.5024, 73.9256, 6, 4),
];

const initialChats: Conversation[] = [
  { title: "Sample neighborhood group", messages: [
    { author: "Demo Volunteer", body: "This is a fictional conversation. No messages are sent to real users." },
    { author: "Demo Citizen", body: "Let's review how updates about a civic issue could appear here." },
  ] },
  { title: "Sample direct message", messages: [
    { author: "Demo Neighbor", body: "Could you share an example of the issue location?" },
    { author: "You (demo)", body: "Sure, the sample is marked on our demo map." },
  ] },
  { title: "Sample issue discussion", messages: [
    { author: "Demo Resident", body: "This thread demonstrates a complaint-linked conversation." },
  ] },
];

const statuses = ["submitted", "in_progress", "resolved", "closed"];
const statusName: Record<string, string> = { submitted: "Submitted", in_progress: "In progress", resolved: "Resolved", closed: "Closed" };
const tabs: Tab[] = ["feed", "map", "chats", "profile", "dashboard", "report"];

export function ReviewDemo() {
  const [tab, setTab] = useState<Tab>("feed");
  const [issues, setIssues] = useState<DemoIssue[]>(starterIssues);
  const [filter, setFilter] = useState("all");
  const [selected, setSelected] = useState<DemoIssue | null>(null);
  const [commentInputs, setCommentInputs] = useState<Record<string, string>>({});
  const [chats, setChats] = useState(initialChats);
  const [activeChat, setActiveChat] = useState(0);
  const [draft, setDraft] = useState("");
  const [reportTitle, setReportTitle] = useState("");
  const [reportDescription, setReportDescription] = useState("");
  const [reportFeedback, setReportFeedback] = useState("");
  const [displayName, setDisplayName] = useState("Demo Citizen");

  const filtered = useMemo(() => issues.filter((issue) => filter === "all" || issue.status === filter), [issues, filter]);
  const stats = useMemo(() => statuses.map((status) => ({ status, count: issues.filter((issue) => issue.status === status).length })), [issues]);

  function updateIssue(id: string, change: (issue: DemoIssue) => DemoIssue) {
    setIssues((current) => current.map((issue) => issue.id === id ? change(issue) : issue));
    setSelected((current) => current?.id === id ? change(current) : current);
  }

  function addComment(issue: DemoIssue) {
    const body = commentInputs[issue.id]?.trim();
    if (!body) return;
    updateIssue(issue.id, (existing) => ({ ...existing, comments: [...existing.comments, `${displayName} (demo): ${body}`] }));
    setCommentInputs((current) => ({ ...current, [issue.id]: "" }));
  }

  function sendMessage() {
    if (!draft.trim()) return;
    setChats((current) => current.map((chat, index) => index === activeChat
      ? { ...chat, messages: [...chat.messages, { author: `${displayName} (demo)`, body: draft.trim() }] }
      : chat));
    setDraft("");
  }

  function submitReport() {
    if (!reportTitle.trim() || !reportDescription.trim()) {
      setReportFeedback("Add a title and description to create a sample report.");
      return;
    }
    const n = issues.length + 1;
    const issue = makeIssue(n, `${reportTitle.trim()} (demo)`, reportDescription.trim(), "General", "Pune (illustrative)", "submitted", 18.5204, 73.8567, 0, 0);
    setIssues((current) => [issue, ...current]);
    setReportTitle(""); setReportDescription("");
    setReportFeedback("Sample report created in this browser session only. Nothing was sent to the backend.");
    setTab("feed"); setFilter("all");
  }

  return (
    <AppShell contentClassName="max-w-6xl">
      <div className="space-y-5">
        <section className="rounded-xl border-2 border-amber-400 bg-amber-50 p-4 text-amber-950" role="note">
          <h1 className="text-xl font-bold">CivicSense V3 — review sandbox</h1>
          <p className="mt-1 text-sm">All issues, locations, statuses, profiles, chats and comments below are fictional SAMPLE DATA. This page is Preview-only, uses browser memory, and never submits demo content to the API or database. Refreshing resets it. It does not test live backend features.</p>
        </section>
        <nav aria-label="Review sections" className="flex flex-wrap gap-2">
          {tabs.map((item) => <button key={item} type="button" onClick={() => setTab(item)} aria-current={tab === item ? "page" : undefined} className={`rounded-lg px-4 py-2 text-sm font-medium capitalize ${tab === item ? "bg-slate-900 text-white" : "border border-slate-300 bg-white text-slate-800"}`}>{item}</button>)}
        </nav>

        {tab === "feed" && <section className="space-y-4">
          <h2 className="text-2xl font-semibold">Sample issue feed</h2>
          <div className="flex flex-wrap gap-2">{["all", ...statuses].map((status) => <button type="button" key={status} onClick={() => setFilter(status)} className={`rounded-full px-3 py-1 text-sm ${filter === status ? "bg-blue-600 text-white" : "border border-slate-300"}`}>{status === "all" ? "All" : statusName[status]}</button>)}</div>
          {filtered.map((issue) => <article key={issue.id} className="space-y-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-2"><span className="text-xs uppercase tracking-wide text-slate-600">{issue.category.name} · SAMPLE</span><span className="rounded-full bg-blue-50 px-2 py-1 text-xs">{statusName[issue.status]}</span></div>
            <h3 className="text-lg font-semibold">{issue.title}</h3><p className="text-sm text-slate-700">{issue.description}</p><p className="text-xs text-slate-500">Approximate sample location: {issue.ward}</p>
            <div className="flex flex-wrap gap-3 text-sm"><button type="button" onClick={() => updateIssue(issue.id, (current) => ({ ...current, likes: current.likes + 1 }))}>♡ Like · {issue.likes}</button><button type="button" onClick={() => updateIssue(issue.id, (current) => ({ ...current, affected: current.affected + 1 }))}>Affected · {issue.affected}</button><span>Comments · {issue.comments.length}</span></div>
            <div className="space-y-1">{issue.comments.map((comment, index) => <p className="rounded bg-slate-50 p-2 text-sm" key={`${issue.id}-${index}`}>{comment}</p>)}</div>
            <div className="flex gap-2"><input aria-label={`Comment on ${issue.title}`} className="min-w-0 flex-1 rounded border px-3 py-2 text-sm" placeholder="Sample comment" value={commentInputs[issue.id] ?? ""} onChange={(event) => setCommentInputs((current) => ({ ...current, [issue.id]: event.target.value }))} /><button type="button" className="rounded bg-slate-900 px-3 py-2 text-sm text-white" onClick={() => addComment(issue)}>Comment</button></div>
          </article>)}
        </section>}

        {tab === "map" && <section className="space-y-3"><h2 className="text-2xl font-semibold">Sample map · Pune</h2><p className="text-sm text-slate-600">Approximate fictional pins, not reported incidents. Click a marker to inspect the example.</p><div className="h-[540px] overflow-hidden rounded-xl border"><CivicMap complaints={issues} selectedComplaintId={selected?.id} onSelectComplaint={(issue) => setSelected(issues.find((item) => item.id === issue.id) ?? null)} /></div>{selected && <div className="rounded-xl border bg-white p-4"><p className="text-xs font-semibold text-amber-700">SAMPLE ISSUE</p><h3 className="font-semibold">{selected.title}</h3><p className="text-sm">{selected.description}</p><button className="mt-2 text-sm underline" type="button" onClick={() => setSelected(null)}>Close details</button></div>}</section>}

        {tab === "chats" && <section className="space-y-3"><h2 className="text-2xl font-semibold">Sample chats</h2><div className="grid gap-4 md:grid-cols-[240px_1fr]"><div className="space-y-2">{chats.map((chat, index) => <button type="button" key={chat.title} onClick={() => setActiveChat(index)} className={`block w-full rounded-lg border p-3 text-left text-sm ${activeChat === index ? "border-blue-500 bg-blue-50" : "bg-white"}`}>{chat.title}</button>)}</div><div className="space-y-3 rounded-xl border bg-white p-4"><h3 className="font-semibold">{chats[activeChat].title}</h3>{chats[activeChat].messages.map((message, index) => <div className="rounded-lg bg-slate-50 p-3" key={index}><p className="text-xs font-semibold">{message.author}</p><p className="text-sm">{message.body}</p></div>)}<form className="flex gap-2" onSubmit={(event) => { event.preventDefault(); sendMessage(); }}><input aria-label="Sample message" className="min-w-0 flex-1 rounded border px-3 py-2" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Type a demo message" /><button className="rounded bg-slate-900 px-3 py-2 text-white" type="submit">Send</button></form><p className="text-xs text-slate-500">Messages stay in this browser session. No real messages are sent.</p></div></div></section>}

        {tab === "profile" && <section className="space-y-3 rounded-xl border bg-white p-5"><h2 className="text-2xl font-semibold">Sample citizen profile</h2><label className="block text-sm">Display name<input className="mt-1 block w-full rounded border px-3 py-2" value={displayName} onChange={(event) => setDisplayName(event.target.value)} /></label><p className="text-sm">Handle: @demo-citizen · Sample reputation: 125 XP · Sample badge: Civic Explorer</p><p className="text-xs text-slate-500">No actual profile is created or changed.</p></section>}

        {tab === "dashboard" && <section className="space-y-4"><h2 className="text-2xl font-semibold">Sample dashboard</h2><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{stats.map(({ status, count }) => <div className="rounded-xl border bg-white p-4" key={status}><p className="text-sm text-slate-600">{statusName[status]}</p><p className="text-3xl font-bold">{count}</p></div>)}</div><p className="text-sm text-slate-500">Counts represent only the fictional issues on this page.</p></section>}

        {tab === "report" && <section className="space-y-4 rounded-xl border bg-white p-5"><h2 className="text-2xl font-semibold">Try sample reporting</h2><p className="text-sm text-amber-800">This is a local illustration, not a real civic complaint.</p><label className="block text-sm">Issue title<input className="mt-1 block w-full rounded border px-3 py-2" value={reportTitle} onChange={(event) => setReportTitle(event.target.value)} /></label><label className="block text-sm">Description<textarea className="mt-1 block w-full rounded border px-3 py-2" rows={3} value={reportDescription} onChange={(event) => setReportDescription(event.target.value)} /></label><button type="button" onClick={submitReport} className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white">Add sample to feed</button>{reportFeedback && <p role="status" className="text-sm">{reportFeedback}</p>}</section>}
      </div>
    </AppShell>
  );
}
