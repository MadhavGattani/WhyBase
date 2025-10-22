export default function Header() {
  return (
    <header className="flex items-center justify-between p-4 bg-gradient-to-r from-primary/80 to-primary/60">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center text-xl font-bold">L</div>
        <h1 className="text-lg font-semibold">Loominal</h1>
      </div>
      <div>
        <button className="px-4 py-2 rounded-md bg-white/10 hover:bg-white/20">Login</button>
      </div>
    </header>
  );
}
