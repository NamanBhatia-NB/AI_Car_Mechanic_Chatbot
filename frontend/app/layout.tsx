import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Instant Mechanic — AI Automobile Diagnostic Assistant & Booking',
  description: 'Troubleshoot engine knocks, brake grinding, check engine lights, and vehicle issues with our senior mechanic virtual technician. Upload photos, sound clips, and book certified mobile mechanics instantly.',
  keywords: 'car repair, mechanic chatbot, auto diagnostics, engine noise diagnosis, check engine light, book mechanic, mobile auto repair',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
      </head>
      <body>{children}</body>
    </html>
  );
}
