"use client";

interface SidebarProps {
  open: boolean;
  onToggle: () => void;
  onNewChat: () => void;
}

export default function Sidebar({ open, onToggle, onNewChat }: SidebarProps) {
  const width = open ? "200px" : "60px";

  return (
    <aside
      style={{ width, minWidth: width }}
      className="flex flex-col bg-[#171717] h-full transition-all duration-200 overflow-hidden"
    >
      {/* New chat button */}
      <div className="flex items-center h-14 px-3">
        <button
          onClick={onNewChat}
          title="New chat"
          className="flex items-center gap-3 w-full rounded-lg px-2 py-2 text-[#8e8ea0] hover:text-[#ececec] hover:bg-[#2f2f2f] transition-colors"
        >
          <span className="text-lg flex-shrink-0">✏</span>
          {open && <span className="text-sm whitespace-nowrap">New chat</span>}
        </button>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-3 space-y-1">
        <button
          title="History"
          className="flex items-center gap-3 w-full rounded-lg px-2 py-2 text-[#8e8ea0] hover:text-[#ececec] hover:bg-[#2f2f2f] transition-colors"
        >
          <span className="text-lg flex-shrink-0">◷</span>
          {open && <span className="text-sm whitespace-nowrap">History</span>}
        </button>
      </nav>

      {/* Toggle + settings at bottom */}
      <div className="px-3 pb-4 space-y-1">
        <button
          title="Settings"
          className="flex items-center gap-3 w-full rounded-lg px-2 py-2 text-[#8e8ea0] hover:text-[#ececec] hover:bg-[#2f2f2f] transition-colors"
        >
          <span className="text-lg flex-shrink-0">⚙</span>
          {open && <span className="text-sm whitespace-nowrap">Settings</span>}
        </button>
        <button
          onClick={onToggle}
          title={open ? "Collapse sidebar" : "Expand sidebar"}
          className="flex items-center gap-3 w-full rounded-lg px-2 py-2 text-[#8e8ea0] hover:text-[#ececec] hover:bg-[#2f2f2f] transition-colors"
        >
          <span className="text-lg flex-shrink-0">{open ? "◂" : "▸"}</span>
          {open && <span className="text-sm whitespace-nowrap">Collapse</span>}
        </button>
      </div>
    </aside>
  );
}
