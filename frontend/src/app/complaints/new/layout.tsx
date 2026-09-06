import { ComplaintWizardProvider } from "@/features/complaints/wizard-context";
import { WizardShell } from "@/features/complaints/wizard-shell";

export default function NewComplaintLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ComplaintWizardProvider>
      <WizardShell>{children}</WizardShell>
    </ComplaintWizardProvider>
  );
}
