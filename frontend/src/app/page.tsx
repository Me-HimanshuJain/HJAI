import { redirect } from "next/navigation";

// Root redirects to login — authentication gateway
export default function Home() {
  redirect("/login");
}
