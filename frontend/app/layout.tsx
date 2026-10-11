import type { Metadata } from "next";
import "./globals.css";
import "./experience.css";
import "./report.css";
import "@fontsource/inter/300.css";
import "@fontsource/inter/400.css";
import "@fontsource/space-grotesk/400.css";

export const metadata: Metadata = {
  title: "Green Home Twin",
  description:
    "An interactive renovation plan for comfort, energy efficiency and your property’s next chapter.",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
