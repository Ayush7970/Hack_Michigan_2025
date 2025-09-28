import Link from "next/link";
import LoginButton from "./LoginButton";
import { UserButton } from "./UserButton"; // optional, see below

export default function Navbar() {
  return (
    <nav className="w-full">
      <div className="flex justify-between items-center py-8 text-white px-16">
        <Link href="/" className="font-mono font-bold text-3xl hover:text-primary transition-colors duration-300">oParley</Link>

        <div className="flex gap-30 font-mono text-lg">
          <Link href="/" className="hover:text-primary transition-colors duration-300">Home</Link>
          <Link href="/" className="hover:text-primary transition-colors duration-300">About</Link>
          <Link href="/" className="hover:text-primary transition-colors duration-300">Pricing</Link>
        </div>

        <div className="flex items-center gap-3">
          <UserButton />

          <LoginButton className="font-mono bg-primary p-2 px-9 text-black rounded-3xl" />
        </div>
      </div>
    </nav>
  );
}