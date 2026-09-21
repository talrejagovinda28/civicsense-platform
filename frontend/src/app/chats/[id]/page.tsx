import { ChatThreadView } from "@/features/chats/chat-thread-view";

type ChatThreadPageProps = {
  params: Promise<{ id: string }>;
};

export default async function ChatThreadPage({ params }: ChatThreadPageProps) {
  const { id } = await params;
  return <ChatThreadView chatId={id} />;
}
