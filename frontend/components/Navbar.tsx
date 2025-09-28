import Link from "next/link";
import LoginButton from "./LoginButton";
import { UserButton } from "./UserButton"; // optional, see below

export default function Navbar() {
  return (
    <nav className="w-full border-b-white border-b-1">
      <div className="flex justify-between items-center py-8 text-white px-16">
        <Link href="/" className="font-mono font-bold text-3xl">oParley</Link>

        <div className="flex gap-30 font-mono text-lg">
          <Link href="/">Home</Link>
          <Link href="/">About</Link>
          <Link href="/">Pricing</Link>
        </div>

        <div className="flex items-center gap-3">
          <UserButton />
          <LoginButton className="font-mono bg-primary p-2 px-9 text-black rounded-3xl" />
        </div>
      </div>
    </nav>
  );
}