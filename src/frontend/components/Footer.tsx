import Link from "next/link";

export function Footer() {
  return (
    <footer className="mt-12 pt-4 border-t border-gray-800 text-xs tracking-widest uppercase text-gray-500 flex flex-wrap items-center justify-between gap-2">
      <span>
        NeuroPit · Built by{" "}
        <Link
          href="https://github.com/vighriday"
          className="text-gray-300 hover:text-gray-100"
          target="_blank"
          rel="noopener noreferrer"
        >
          Hriday Vig
        </Link>
      </span>
      <span>IBM AI Builders Challenge 2026 powered by IBM SkillsBuild</span>
    </footer>
  );
}
